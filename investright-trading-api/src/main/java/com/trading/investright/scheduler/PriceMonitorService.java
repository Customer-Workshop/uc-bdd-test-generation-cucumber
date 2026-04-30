package com.trading.investright.scheduler;

import com.trading.investright.client.InvestRightAuthClient;
import com.trading.investright.client.InvestRightMarketClient;
import com.trading.investright.config.SchedulerProperties;
import com.trading.investright.model.TradePosition;
import com.trading.investright.model.request.OrderRequest;
import com.trading.investright.model.response.OrderResponse;
import com.trading.investright.service.OrderService;
import com.trading.investright.service.PositionTracker;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

import java.time.LocalTime;
import java.time.ZoneId;
import java.time.ZonedDateTime;
import java.util.List;

@Slf4j
@Component
@RequiredArgsConstructor
@ConditionalOnProperty(name = "scheduler.enabled", havingValue = "true")
public class PriceMonitorService {

    private final PositionTracker positionTracker;
    private final InvestRightMarketClient marketClient;
    private final InvestRightAuthClient authClient;
    private final OrderService orderService;
    private final SchedulerProperties schedulerProperties;

    private static final LocalTime MARKET_OPEN = LocalTime.of(9, 15);
    private static final LocalTime MARKET_CLOSE = LocalTime.of(15, 30);

    @Scheduled(fixedRateString = "${scheduler.price-check-interval-ms:5000}")
    public void checkPrices() {
        if (!isMarketHours()) {
            return;
        }

        List<TradePosition> activePositions = positionTracker.getActivePositions();
        if (activePositions.isEmpty()) {
            return;
        }

        log.debug("Checking prices for {} active positions", activePositions.size());

        String userId = schedulerProperties.getUserId();
        String accessToken;
        try {
            accessToken = authClient.getAccessToken(userId);
        } catch (Exception ex) {
            log.error("Failed to get access token for price check: {}", ex.getMessage());
            return;
        }

        for (TradePosition position : activePositions) {
            try {
                checkPositionPrice(position, accessToken);
            } catch (Exception ex) {
                log.error("Error checking price for position {}: {}", position.getPositionId(), ex.getMessage());
            }
        }
    }

    void checkPositionPrice(TradePosition position, String accessToken) {
        Double ltp = marketClient.getLastTradedPrice(
                position.getTradingSymbol(), position.getExchange(), accessToken);

        if (ltp == null) {
            log.warn("Could not get LTP for {}", position.getTradingSymbol());
            return;
        }

        position.setLastCheckedAt(java.time.Instant.now());
        log.debug("{} LTP={} Entry={} SL={} T1={} T2={} T3={}",
                position.getInstrumentName(), ltp, position.getEntryPrice(),
                position.getStopLoss(), position.getTarget1(), position.getTarget2(), position.getTarget3());

        if (isStopLossHit(position, ltp)) {
            handleStopLossHit(position, ltp, accessToken);
            return;
        }

        checkAndHandleTargets(position, ltp, accessToken);
    }

    private boolean isStopLossHit(TradePosition position, double ltp) {
        if (position.getStopLoss() <= 0) return false;

        if ("BUY".equalsIgnoreCase(position.getTransactionType())) {
            return ltp <= position.getStopLoss();
        } else {
            return ltp >= position.getStopLoss();
        }
    }

    private void handleStopLossHit(TradePosition position, double ltp, String accessToken) {
        log.warn("STOP LOSS HIT for {} at LTP={} (SL={}). Exiting full position of {} qty.",
                position.getInstrumentName(), ltp, position.getStopLoss(), position.getRemainingQuantity());

        position.setStopLossHit(true);
        placeSellOrder(position, position.getRemainingQuantity(), ltp, "SL_EXIT", accessToken);
        positionTracker.closePosition(position.getPositionId(), TradePosition.PositionStatus.EXITED_STOPLOSS);
    }

    void checkAndHandleTargets(TradePosition position, double ltp, String accessToken) {
        if (isTargetHit(position.getTarget1(), position, ltp) && !position.isTarget1Hit()) {
            log.info("TARGET 1 HIT for {} at LTP={} (T1={})", position.getInstrumentName(), ltp, position.getTarget1());
            position.setTarget1Hit(true);
            int sellQty = position.getPartialQuantity();
            placeSellOrder(position, sellQty, ltp, "T1_EXIT", accessToken);
            position.setRemainingQuantity(position.getRemainingQuantity() - sellQty);
            updatePositionStatus(position);
        }

        if (isTargetHit(position.getTarget2(), position, ltp) && !position.isTarget2Hit()) {
            log.info("TARGET 2 HIT for {} at LTP={} (T2={})", position.getInstrumentName(), ltp, position.getTarget2());
            position.setTarget2Hit(true);
            int sellQty = Math.min(position.getPartialQuantity(), position.getRemainingQuantity());
            placeSellOrder(position, sellQty, ltp, "T2_EXIT", accessToken);
            position.setRemainingQuantity(position.getRemainingQuantity() - sellQty);
            updatePositionStatus(position);
        }

        if (isTargetHit(position.getTarget3(), position, ltp) && !position.isTarget3Hit()) {
            log.info("TARGET 3 HIT for {} at LTP={} (T3={}). Exiting remaining position.",
                    position.getInstrumentName(), ltp, position.getTarget3());
            position.setTarget3Hit(true);
            placeSellOrder(position, position.getRemainingQuantity(), ltp, "T3_EXIT", accessToken);
            positionTracker.closePosition(position.getPositionId(), TradePosition.PositionStatus.EXITED_TARGET);
        }

        positionTracker.updatePosition(position);
    }

    private boolean isTargetHit(Double target, TradePosition position, double ltp) {
        if (target == null || target <= 0) return false;

        if ("BUY".equalsIgnoreCase(position.getTransactionType())) {
            return ltp >= target;
        } else {
            return ltp <= target;
        }
    }

    private void placeSellOrder(TradePosition position, int quantity, double ltp, String reason, String accessToken) {
        if (quantity <= 0) return;

        String exitType = "BUY".equalsIgnoreCase(position.getTransactionType()) ? "SELL" : "BUY";

        OrderRequest sellOrder = OrderRequest.builder()
                .exchange(position.getExchange())
                .securityId(position.getTradingSymbol())
                .transactionType(exitType)
                .orderType("MARKET")
                .quantity(quantity)
                .price(0.0)
                .triggerPrice(0.0)
                .product("BUY".equalsIgnoreCase(position.getTransactionType()) ? "DELIVERY" : "OVERNIGHT")
                .validity("DAY")
                .amo(false)
                .disclosedQuantity(0)
                .build();

        try {
            OrderResponse response = orderService.placeOrder(sellOrder, position.getUserId());
            log.info("{} order placed for {} qty={} reason={} orderId={}",
                    exitType, position.getInstrumentName(), quantity, reason,
                    response.getData() != null ? response.getData().getOrderId() : "unknown");
        } catch (Exception ex) {
            log.error("Failed to place {} order for {} qty={} reason={}: {}",
                    exitType, position.getInstrumentName(), quantity, reason, ex.getMessage());
        }
    }

    private void updatePositionStatus(TradePosition position) {
        if (position.getRemainingQuantity() <= 0) {
            position.setStatus(TradePosition.PositionStatus.EXITED_TARGET);
        } else if (position.isTarget1Hit() || position.isTarget2Hit()) {
            position.setStatus(TradePosition.PositionStatus.PARTIALLY_EXITED);
        }
    }

    boolean isMarketHours() {
        ZonedDateTime now = ZonedDateTime.now(ZoneId.of(schedulerProperties.getTimezone()));
        LocalTime currentTime = now.toLocalTime();
        return !currentTime.isBefore(MARKET_OPEN) && !currentTime.isAfter(MARKET_CLOSE);
    }
}
