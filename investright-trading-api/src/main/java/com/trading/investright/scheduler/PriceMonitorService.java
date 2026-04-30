package com.trading.investright.scheduler;

import com.trading.investright.client.InvestRightAuthClient;
import com.trading.investright.client.InvestRightMarketClient;
import com.trading.investright.config.SchedulerProperties;
import com.trading.investright.config.TradingProperties;
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
import java.util.Map;

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
    private final TradingProperties tradingProperties;

    private static final LocalTime MARKET_OPEN = LocalTime.of(9, 15);
    private static final LocalTime MARKET_CLOSE = LocalTime.of(15, 30);
    private static final LocalTime EOD_EXIT_TIME = LocalTime.of(15, 25);

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

        String userId = schedulerProperties.getUserId() != null && !schedulerProperties.getUserId().isBlank() ?
                schedulerProperties.getUserId() : schedulerProperties.getUsername();
        String accessToken;
        try {
            accessToken = authClient.getAccessToken(userId);
        } catch (Exception ex) {
            log.error("Failed to get access token for price check: {}", ex.getMessage());
            return;
        }

        for (TradePosition position : activePositions) {
            try {
                if (!position.isAmoExecuted() && !position.isRegularOrderPlaced()) {
                    retryAsRegularOrder(position, userId, accessToken);
                    continue;
                }
                checkPositionPrice(position, accessToken);
            } catch (Exception ex) {
                log.error("Error checking price for position {}: {}", position.getPositionId(), ex.getMessage());
            }
        }
    }

    void retryAsRegularOrder(TradePosition position, String userId, String accessToken) {
        log.info("AMO order not executed for {}. Checking open price before placing regular order.",
                position.getInstrumentName());

        try {
            orderService.cancelOrder(position.getOrderId(), userId);
            log.info("Cancelled AMO order {} for {}", position.getOrderId(), position.getInstrumentName());
        } catch (Exception ex) {
            log.warn("Could not cancel AMO order {} (may already be cancelled): {}",
                    position.getOrderId(), ex.getMessage());
        }

        Double openPrice = fetchOpenPrice(position, accessToken);
        if (openPrice != null && shouldSkipTrade(position, openPrice)) {
            log.warn("SKIPPING trade for {} — opened at ₹{} which is at/below SL (₹{}). No position taken.",
                    position.getInstrumentName(), openPrice, position.getStopLoss());
            positionTracker.closePosition(position.getPositionId(), TradePosition.PositionStatus.CLOSED);
            return;
        }

        if (openPrice != null) {
            position.setOpenPrice(openPrice);
        }

        OrderRequest regularOrder = OrderRequest.builder()
                .exchange(position.getExchange())
                .instrumentSegment(position.getInstrumentSegment() != null ? position.getInstrumentSegment() : "EQUITY")
                .securityId(position.getTradingSymbol())
                .transactionType(position.getTransactionType())
                .orderType("SL")
                .quantity(position.getRemainingQuantity())
                .triggerPrice(position.getEntryPrice())
                .price(calculateRegularOrderPrice(position.getEntryPrice(), position.getTransactionType()))
                .product("BUY".equalsIgnoreCase(position.getTransactionType()) ? "DELIVERY" : "OVERNIGHT")
                .validity("DAY")
                .amo(false)
                .disclosedQuantity(0)
                .build();

        try {
            OrderResponse response = orderService.placeOrder(regularOrder, userId);
            String newOrderId = (response.getData() != null) ? response.getData().getOrderId() : "unknown";
            position.setOrderId(newOrderId);
            position.setRegularOrderPlaced(true);
            position.setAmoExecuted(true);
            positionTracker.updatePosition(position);
            log.info("Regular order placed for {} orderId={} (replaces AMO)",
                    position.getInstrumentName(), newOrderId);
        } catch (Exception ex) {
            log.error("Failed to place regular order for {}: {}", position.getInstrumentName(), ex.getMessage());
        }
    }

    private Double fetchOpenPrice(TradePosition position, String accessToken) {
        if (position.getOpenPrice() != null) {
            return position.getOpenPrice();
        }
        try {
            return marketClient.getLastTradedPrice(
                    position.getTradingSymbol(), position.getExchange(), accessToken);
        } catch (Exception ex) {
            log.warn("Could not fetch open price for {}: {}", position.getInstrumentName(), ex.getMessage());
            return null;
        }
    }

    boolean shouldSkipTrade(TradePosition position, double openPrice) {
        if ("BUY".equalsIgnoreCase(position.getTransactionType())) {
            return openPrice <= position.getStopLoss();
        } else {
            return openPrice >= position.getStopLoss();
        }
    }

    void pollOrderFillStatus(TradePosition position, String userId) {
        try {
            Map<String, Object> orderStatus = orderService.getOrderStatus(position.getOrderId(), userId);
            if (orderStatus == null) return;

            Map<String, Object> data = extractDataMap(orderStatus);
            if (data == null) data = orderStatus;

            String status = data.get("order_status") != null ? data.get("order_status").toString() : "";
            int filled = extractFilledQuantity(data);

            if (("EXECUTED".equalsIgnoreCase(status) || "COMPLETE".equalsIgnoreCase(status)) && filled > 0) {
                position.setFilledQuantity(filled);
                position.setRemainingQuantity(filled);
                log.info("Order {} FILLED for {} — actual qty: {}/{}", position.getOrderId(),
                        position.getInstrumentName(), filled, position.getTotalQuantity());
                positionTracker.updatePosition(position);
            } else if (("PARTIALLY_EXECUTED".equalsIgnoreCase(status) || "PARTIAL".equalsIgnoreCase(status)) && filled > 0) {
                position.setFilledQuantity(filled);
                position.setRemainingQuantity(filled);
                log.info("Order {} PARTIALLY FILLED for {} — actual qty: {}/{}", position.getOrderId(),
                        position.getInstrumentName(), filled, position.getTotalQuantity());
                positionTracker.updatePosition(position);
            }
        } catch (Exception ex) {
            log.warn("Could not poll fill status for order {}: {}", position.getOrderId(), ex.getMessage());
        }
    }

    private int extractFilledQuantity(Map<String, Object> data) {
        Object filledQty = data.get("filled_quantity");
        if (filledQty == null) filledQty = data.get("filledQuantity");
        if (filledQty == null) filledQty = data.get("traded_quantity");
        if (filledQty instanceof Number number) return number.intValue();
        if (filledQty instanceof String str) {
            try { return Integer.parseInt(str); } catch (NumberFormatException e) { return 0; }
        }
        return 0;
    }

    @SuppressWarnings("unchecked")
    private Map<String, Object> extractDataMap(Map<String, Object> response) {
        if (response.containsKey("data") && response.get("data") instanceof Map) {
            return (Map<String, Object>) response.get("data");
        }
        return null;
    }

    private double calculateRegularOrderPrice(double entryPrice, String transactionType) {
        double slippage = entryPrice * 0.005;
        if ("BUY".equalsIgnoreCase(transactionType)) {
            return Math.round((entryPrice + slippage) * 100.0) / 100.0;
        } else {
            return Math.round((entryPrice - slippage) * 100.0) / 100.0;
        }
    }

    void checkPositionPrice(TradePosition position, String accessToken) {
        if (position.getFilledQuantity() == 0 && position.getOrderId() != null) {
            pollOrderFillStatus(position, position.getUserId());
            if (position.getFilledQuantity() == 0) {
                log.debug("Order {} not yet filled for {}", position.getOrderId(), position.getInstrumentName());
                return;
            }
        }

        Double ltp = marketClient.getLastTradedPrice(
                position.getTradingSymbol(), position.getExchange(), accessToken);

        if (ltp == null) {
            log.warn("Could not get LTP for {}", position.getTradingSymbol());
            return;
        }

        position.setLastCheckedAt(java.time.Instant.now());
        log.debug("{} LTP={} Entry={} SL={} T1={} T2={} T3={} FilledQty={}",
                position.getInstrumentName(), ltp, position.getEntryPrice(),
                position.getStopLoss(), position.getTarget1(), position.getTarget2(), position.getTarget3(),
                position.getFilledQuantity());

        if (isStopLossHit(position, ltp)) {
            handleStopLossHit(position, ltp, accessToken);
            return;
        }

        if (isEndOfDay() && isProfitable(position, ltp) && !position.isTarget1Hit()) {
            handleEndOfDayExit(position, ltp, accessToken);
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
        log.warn("STOP LOSS HIT for {} at LTP={} (SL={}). Active SL order {} should execute on broker side.",
                position.getInstrumentName(), ltp, position.getStopLoss(), position.getActiveSlOrderId());

        position.setStopLossHit(true);
        positionTracker.closePosition(position.getPositionId(), TradePosition.PositionStatus.EXITED_STOPLOSS);
    }

    void checkAndHandleTargets(TradePosition position, double ltp, String accessToken) {
        if (isTargetHit(position.getTarget3(), position, ltp) && !position.isTarget3Hit()) {
            log.info("TARGET 3 HIT for {} at LTP={} (T3={}). Cancelling SL order and placing market sell for {} qty.",
                    position.getInstrumentName(), ltp, position.getTarget3(), position.getRemainingQuantity());
            position.setTarget3Hit(true);
            position.setTarget2Hit(true);
            position.setTarget1Hit(true);
            cancelActiveSlOrder(position);
            placeSellOrder(position, position.getRemainingQuantity(), ltp, "T3_FULL_EXIT", accessToken);
            positionTracker.closePosition(position.getPositionId(), TradePosition.PositionStatus.EXITED_TARGET);
            return;
        }

        if (isTargetHit(position.getTarget2(), position, ltp) && !position.isTarget2Hit()) {
            double basePrice = position.getTarget1() != null ? position.getTarget1() : position.getEntryPrice();
            double newSl = calculateTrailingSlPrice(basePrice, position.getTransactionType());
            log.info("TARGET 2 HIT for {} at LTP={} (T2={}). Cancelling old SL and placing new SL at T1+buffer = {} (profit locked).",
                    position.getInstrumentName(), ltp, position.getTarget2(), newSl);
            position.setTarget2Hit(true);
            position.setTarget1Hit(true);
            cancelActiveSlOrder(position);
            position.setStopLoss(newSl);
            placeNewSlOrder(position, newSl, accessToken);
            position.setStatus(TradePosition.PositionStatus.PARTIALLY_EXITED);
        } else if (isTargetHit(position.getTarget1(), position, ltp) && !position.isTarget1Hit()) {
            double newSl = calculateTrailingSlPrice(position.getEntryPrice(), position.getTransactionType());
            log.info("TARGET 1 HIT for {} at LTP={} (T1={}). Cancelling old SL and placing new SL at entry+buffer = {} (profit locked).",
                    position.getInstrumentName(), ltp, position.getTarget1(), newSl);
            position.setTarget1Hit(true);
            cancelActiveSlOrder(position);
            position.setStopLoss(newSl);
            placeNewSlOrder(position, newSl, accessToken);
            position.setStatus(TradePosition.PositionStatus.PARTIALLY_EXITED);
        }

        positionTracker.updatePosition(position);
    }

    private double calculateTrailingSlPrice(double basePrice, String transactionType) {
        double bufferPercent = tradingProperties.getTrailingSlBufferPercent();
        if ("SELL".equalsIgnoreCase(transactionType)) {
            return Math.round(basePrice * (1 - bufferPercent / 100.0) * 100.0) / 100.0;
        }
        return Math.round(basePrice * (1 + bufferPercent / 100.0) * 100.0) / 100.0;
    }

    private void cancelActiveSlOrder(TradePosition position) {
        if (position.getActiveSlOrderId() == null) {
            return;
        }
        try {
            orderService.cancelOrder(position.getActiveSlOrderId(), position.getUserId());
            log.info("Cancelled active SL order {} for {}", position.getActiveSlOrderId(), position.getInstrumentName());
        } catch (Exception ex) {
            log.warn("Could not cancel SL order {} for {} (may already be executed): {}",
                    position.getActiveSlOrderId(), position.getInstrumentName(), ex.getMessage());
        }
        position.setActiveSlOrderId(null);
    }

    private void placeNewSlOrder(TradePosition position, double slPrice, String accessToken) {
        String exitType = "BUY".equalsIgnoreCase(position.getTransactionType()) ? "SELL" : "BUY";
        double slippage = slPrice * 0.005;
        double limitPrice = "SELL".equalsIgnoreCase(exitType)
                ? Math.round((slPrice - slippage) * 100.0) / 100.0
                : Math.round((slPrice + slippage) * 100.0) / 100.0;

        OrderRequest slOrder = OrderRequest.builder()
                .exchange(position.getExchange())
                .instrumentSegment(position.getInstrumentSegment() != null ? position.getInstrumentSegment() : "EQUITY")
                .securityId(position.getTradingSymbol())
                .transactionType(exitType)
                .orderType("SL")
                .quantity(position.getRemainingQuantity())
                .triggerPrice(slPrice)
                .price(limitPrice)
                .product("BUY".equalsIgnoreCase(position.getTransactionType()) ? "DELIVERY" : "OVERNIGHT")
                .validity("DAY")
                .amo(false)
                .disclosedQuantity(0)
                .build();

        try {
            OrderResponse response = orderService.placeOrder(slOrder, position.getUserId());
            String orderId = (response.getData() != null) ? response.getData().getOrderId() : "unknown";
            position.setActiveSlOrderId(orderId);
            log.info("New SL order placed for {} at SL={} orderId={}",
                    position.getInstrumentName(), slPrice, orderId);
        } catch (Exception ex) {
            log.error("Failed to place new SL order for {} at SL={}: {}",
                    position.getInstrumentName(), slPrice, ex.getMessage());
        }
    }

    private boolean isTargetHit(Double target, TradePosition position, double ltp) {
        if (target == null || target <= 0) return false;

        if ("BUY".equalsIgnoreCase(position.getTransactionType())) {
            return ltp >= target;
        } else {
            return ltp <= target;
        }
    }

    private boolean isProfitable(TradePosition position, double ltp) {
        if ("BUY".equalsIgnoreCase(position.getTransactionType())) {
            return ltp > position.getEntryPrice();
        } else {
            return ltp < position.getEntryPrice();
        }
    }

    private boolean isEndOfDay() {
        ZonedDateTime now = ZonedDateTime.now(ZoneId.of(schedulerProperties.getTimezone()));
        return !now.toLocalTime().isBefore(EOD_EXIT_TIME);
    }

    private void handleEndOfDayExit(TradePosition position, double ltp, String accessToken) {
        double profit = "BUY".equalsIgnoreCase(position.getTransactionType())
                ? ltp - position.getEntryPrice()
                : position.getEntryPrice() - ltp;
        log.info("END-OF-DAY EXIT for {} at LTP={} (entry={}, profit=₹{}/unit). Cancelling SL and selling {} qty before market close.",
                position.getInstrumentName(), ltp, position.getEntryPrice(),
                String.format("%.2f", profit), position.getRemainingQuantity());

        cancelActiveSlOrder(position);
        placeSellOrder(position, position.getRemainingQuantity(), ltp, "EOD_PROFIT_EXIT", accessToken);
        positionTracker.closePosition(position.getPositionId(), TradePosition.PositionStatus.EXITED_TARGET);
    }

    private void placeSellOrder(TradePosition position, int quantity, double ltp, String reason, String accessToken) {
        if (quantity <= 0) return;

        String exitType = "BUY".equalsIgnoreCase(position.getTransactionType()) ? "SELL" : "BUY";

        OrderRequest sellOrder = OrderRequest.builder()
                .exchange(position.getExchange())
                .instrumentSegment(position.getInstrumentSegment() != null ? position.getInstrumentSegment() : "EQUITY")
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
            String orderId = (response.getData() != null) ? response.getData().getOrderId() : "unknown";
            log.info("{} order placed for {} qty={} reason={} orderId={}",
                    exitType, position.getInstrumentName(), quantity, reason, orderId);
        } catch (Exception ex) {
            log.error("Failed to place {} order for {} qty={} reason={}: {}",
                    exitType, position.getInstrumentName(), quantity, reason, ex.getMessage());
        }
    }

    boolean isMarketHours() {
        ZonedDateTime now = ZonedDateTime.now(ZoneId.of(schedulerProperties.getTimezone()));
        LocalTime currentTime = now.toLocalTime();
        return !currentTime.isBefore(MARKET_OPEN) && !currentTime.isAfter(MARKET_CLOSE);
    }
}
