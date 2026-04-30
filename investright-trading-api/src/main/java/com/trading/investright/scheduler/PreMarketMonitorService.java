package com.trading.investright.scheduler;

import com.trading.investright.client.InvestRightAuthClient;
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
import java.util.Map;

@Slf4j
@Component
@RequiredArgsConstructor
@ConditionalOnProperty(name = "scheduler.enabled", havingValue = "true")
public class PreMarketMonitorService {

    private final PositionTracker positionTracker;
    private final OrderService orderService;
    private final InvestRightAuthClient authClient;
    private final SchedulerProperties schedulerProperties;

    private static final LocalTime PRE_MARKET_START = LocalTime.of(9, 0);
    private static final LocalTime PRE_MARKET_END = LocalTime.of(9, 8);

    @Scheduled(fixedRateString = "${scheduler.price-check-interval-ms:5000}")
    public void checkPreMarketExecutions() {
        if (!isPreMarketWindow()) {
            return;
        }

        List<TradePosition> activePositions = positionTracker.getActivePositions();
        if (activePositions.isEmpty()) {
            return;
        }

        log.debug("Pre-market check: {} active positions to verify execution", activePositions.size());

        String userId = schedulerProperties.getUserId() != null && !schedulerProperties.getUserId().isBlank() ?
                schedulerProperties.getUserId() : schedulerProperties.getUsername();
        String accessToken;
        try {
            accessToken = authClient.getAccessToken(userId);
        } catch (Exception ex) {
            log.error("Failed to get access token for pre-market check: {}", ex.getMessage());
            return;
        }

        for (TradePosition position : activePositions) {
            try {
                checkAndPlaceProtectiveSl(position, userId, accessToken);
            } catch (Exception ex) {
                log.error("Error checking pre-market execution for {}: {}",
                        position.getPositionId(), ex.getMessage());
            }
        }
    }

    void checkAndPlaceProtectiveSl(TradePosition position, String userId, String accessToken) {
        if (position.isProtectiveSlPlaced()) {
            return;
        }

        Map<String, Object> orderStatus = orderService.getOrderStatus(position.getOrderId(), userId);
        if (orderStatus == null) {
            log.warn("Could not get order status for {}", position.getOrderId());
            return;
        }

        String status = extractOrderStatus(orderStatus);
        if ("EXECUTED".equalsIgnoreCase(status) || "COMPLETE".equalsIgnoreCase(status)) {
            log.info("AMO order {} EXECUTED for {}. Placing protective SL sell order.",
                    position.getOrderId(), position.getInstrumentName());
            placeProtectiveSlOrder(position, accessToken);
            position.setProtectiveSlPlaced(true);
            positionTracker.updatePosition(position);
        } else {
            log.debug("AMO order {} status: {} for {}", position.getOrderId(), status, position.getInstrumentName());
        }
    }

    private void placeProtectiveSlOrder(TradePosition position, String accessToken) {
        String exitType = "BUY".equalsIgnoreCase(position.getTransactionType()) ? "SELL" : "BUY";

        OrderRequest slOrder = OrderRequest.builder()
                .exchange(position.getExchange())
                .instrumentSegment(position.getInstrumentSegment() != null ? position.getInstrumentSegment() : "EQUITY")
                .securityId(position.getTradingSymbol())
                .transactionType(exitType)
                .orderType("SL")
                .quantity(position.getRemainingQuantity())
                .triggerPrice(position.getStopLoss())
                .price(calculateSlPrice(position.getStopLoss(), exitType))
                .product("BUY".equalsIgnoreCase(position.getTransactionType()) ? "DELIVERY" : "OVERNIGHT")
                .validity("DAY")
                .amo(false)
                .disclosedQuantity(0)
                .build();

        try {
            OrderResponse response = orderService.placeOrder(slOrder, position.getUserId());
            String orderId = (response.getData() != null) ? response.getData().getOrderId() : "unknown";
            log.info("Protective SL order placed for {} at SL={} orderId={}",
                    position.getInstrumentName(), position.getStopLoss(), orderId);
        } catch (Exception ex) {
            log.error("Failed to place protective SL order for {}: {}",
                    position.getInstrumentName(), ex.getMessage());
        }
    }

    private double calculateSlPrice(double triggerPrice, String exitType) {
        double slippage = triggerPrice * 0.005;
        if ("SELL".equalsIgnoreCase(exitType)) {
            return Math.round((triggerPrice - slippage) * 100.0) / 100.0;
        } else {
            return Math.round((triggerPrice + slippage) * 100.0) / 100.0;
        }
    }

    private String extractOrderStatus(Map<String, Object> orderStatus) {
        if (orderStatus.containsKey("data") && orderStatus.get("data") instanceof Map) {
            @SuppressWarnings("unchecked")
            Map<String, Object> data = (Map<String, Object>) orderStatus.get("data");
            Object status = data.get("order_status");
            return status != null ? status.toString() : "UNKNOWN";
        }
        Object status = orderStatus.get("order_status");
        return status != null ? status.toString() : "UNKNOWN";
    }

    boolean isPreMarketWindow() {
        ZonedDateTime now = ZonedDateTime.now(ZoneId.of(schedulerProperties.getTimezone()));
        LocalTime currentTime = now.toLocalTime();
        return !currentTime.isBefore(PRE_MARKET_START) && currentTime.isBefore(PRE_MARKET_END);
    }
}
