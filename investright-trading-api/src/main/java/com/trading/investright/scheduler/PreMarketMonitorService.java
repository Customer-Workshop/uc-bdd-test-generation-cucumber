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
import java.util.Map;

@Slf4j
@Component
@RequiredArgsConstructor
@ConditionalOnProperty(name = "scheduler.enabled", havingValue = "true")
public class PreMarketMonitorService {

    private final PositionTracker positionTracker;
    private final OrderService orderService;
    private final InvestRightAuthClient authClient;
    private final InvestRightMarketClient marketClient;
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
                fetchAndLogOpenPrice(position, accessToken);
            } catch (Exception ex) {
                log.error("Error checking pre-market execution for {}: {}",
                        position.getPositionId(), ex.getMessage());
            }
        }
    }

    void fetchAndLogOpenPrice(TradePosition position, String accessToken) {
        if (position.getOpenPrice() != null) {
            return;
        }

        try {
            Double ltp = marketClient.getLastTradedPrice(
                    position.getTradingSymbol(), position.getExchange(), accessToken);

            if (ltp != null) {
                position.setOpenPrice(ltp);
                positionTracker.updatePosition(position);
                log.info("PRE-MARKET OPEN PRICE for {}: ₹{} (Entry: ₹{}, SL: ₹{}, T1: ₹{})",
                        position.getInstrumentName(), ltp, position.getEntryPrice(),
                        position.getStopLoss(), position.getTarget1());

                if (ltp > position.getEntryPrice()) {
                    log.info("  → {} opened ABOVE entry price by ₹{} — bullish signal",
                            position.getInstrumentName(),
                            Math.round((ltp - position.getEntryPrice()) * 100.0) / 100.0);
                } else if (ltp < position.getStopLoss()) {
                    log.warn("  → {} opened BELOW stop loss at ₹{} — trade may gap down past SL",
                            position.getInstrumentName(), ltp);
                } else {
                    log.info("  → {} opened between SL and entry — within expected range",
                            position.getInstrumentName());
                }
            } else {
                log.debug("Open price not yet available for {}", position.getInstrumentName());
            }
        } catch (Exception ex) {
            log.debug("Could not fetch open price for {}: {}", position.getInstrumentName(), ex.getMessage());
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
            int filled = extractFilledQuantity(orderStatus);
            if (filled > 0) {
                position.setFilledQuantity(filled);
                position.setRemainingQuantity(filled);
                log.info("AMO order {} EXECUTED for {} — filled {}/{} qty.",
                        position.getOrderId(), position.getInstrumentName(), filled, position.getTotalQuantity());
            } else {
                position.setFilledQuantity(position.getTotalQuantity());
                position.setRemainingQuantity(position.getTotalQuantity());
                log.info("AMO order {} EXECUTED for {} — fill qty unavailable, using total qty {}.",
                        position.getOrderId(), position.getInstrumentName(), position.getTotalQuantity());
            }
            placeProtectiveSlOrder(position, accessToken);
            position.setProtectiveSlPlaced(true);
            position.setAmoExecuted(true);
            positionTracker.updatePosition(position);
        } else if ("PARTIALLY_EXECUTED".equalsIgnoreCase(status) || "PARTIAL".equalsIgnoreCase(status)) {
            int filled = extractFilledQuantity(orderStatus);
            if (filled > 0 && !position.isProtectiveSlPlaced()) {
                position.setFilledQuantity(filled);
                position.setRemainingQuantity(filled);
                log.info("AMO order {} PARTIALLY FILLED for {} — filled {}/{} qty. Placing SL for filled qty.",
                        position.getOrderId(), position.getInstrumentName(), filled, position.getTotalQuantity());
                placeProtectiveSlOrder(position, accessToken);
                position.setProtectiveSlPlaced(true);
                position.setAmoExecuted(true);
                positionTracker.updatePosition(position);
            }
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
            position.setActiveSlOrderId(orderId);
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
        Map<String, Object> data = extractDataMap(orderStatus);
        if (data != null) {
            Object status = data.get("order_status");
            return status != null ? status.toString() : "UNKNOWN";
        }
        Object status = orderStatus.get("order_status");
        return status != null ? status.toString() : "UNKNOWN";
    }

    int extractFilledQuantity(Map<String, Object> orderStatus) {
        Map<String, Object> data = extractDataMap(orderStatus);
        if (data == null) data = orderStatus;

        Object filledQty = data.get("filled_quantity");
        if (filledQty == null) filledQty = data.get("filledQuantity");
        if (filledQty == null) filledQty = data.get("traded_quantity");
        if (filledQty instanceof Number number) {
            return number.intValue();
        }
        if (filledQty instanceof String str) {
            try {
                return Integer.parseInt(str);
            } catch (NumberFormatException e) {
                return 0;
            }
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

    boolean isPreMarketWindow() {
        ZonedDateTime now = ZonedDateTime.now(ZoneId.of(schedulerProperties.getTimezone()));
        LocalTime currentTime = now.toLocalTime();
        return !currentTime.isBefore(PRE_MARKET_START) && currentTime.isBefore(PRE_MARKET_END);
    }
}
