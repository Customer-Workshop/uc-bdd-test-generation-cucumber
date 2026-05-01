package com.trading.investright.service;

import com.trading.investright.client.InvestRightAuthClient;
import com.trading.investright.config.SchedulerProperties;
import com.trading.investright.config.TelegramProperties;
import com.trading.investright.model.TradeSignal;
import com.trading.investright.model.request.OrderRequest;
import com.trading.investright.model.response.OrderResponse;
import com.trading.investright.ocr.TelegramMessageParser;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Service;

import java.time.LocalTime;
import java.time.ZoneId;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

@Slf4j
@Service
@RequiredArgsConstructor
@ConditionalOnProperty(name = "telegram.enabled", havingValue = "true")
public class TelegramWebhookService {

    private final TelegramProperties telegramProperties;
    private final TelegramMessageParser messageParser;
    private final OrderService orderService;
    private final PositionTracker positionTracker;
    private final InvestRightAuthClient authClient;
    private final SchedulerProperties schedulerProperties;
    private final TradeSignalValidator signalValidator;

    private static final int MAX_DEDUP_ENTRIES = 10_000;

    private final Set<Long> processedMessageIds = Collections.newSetFromMap(
            new LinkedHashMap<>(256, 0.75f, false) {
                @Override
                protected boolean removeEldestEntry(Map.Entry<Long, Boolean> eldest) {
                    return size() > MAX_DEDUP_ENTRIES;
                }
            });

    private static final LocalTime MARKET_OPEN = LocalTime.of(9, 0);
    private static final LocalTime MARKET_CLOSE = LocalTime.of(15, 30);
    private static final ZoneId IST = ZoneId.of("Asia/Kolkata");

    @SuppressWarnings("unchecked")
    public String processWebhookUpdate(Map<String, Object> update) {
        Map<String, Object> message = (Map<String, Object>) update.get("channel_post");
        if (message == null) {
            message = (Map<String, Object>) update.get("message");
        }
        if (message == null) {
            return "no_message";
        }

        Number messageIdNum = (Number) message.get("message_id");
        if (messageIdNum != null) {
            long messageId = messageIdNum.longValue();
            if (!processedMessageIds.add(messageId)) {
                log.debug("Duplicate message_id {}, skipping", messageId);
                return "duplicate";
            }
        }

        String text = (String) message.get("text");
        if (text == null || text.isBlank()) {
            return "no_text";
        }

        if (!messageParser.isTradeSignalMessage(text)) {
            log.debug("Non-trade message: {}", text.substring(0, Math.min(50, text.length())));
            return "not_trade_signal";
        }

        if (!isMarketHours()) {
            log.info("Received trade signal outside market hours, skipping: {}",
                    text.substring(0, Math.min(80, text.length())));
            return "outside_market_hours";
        }

        List<TradeSignal> signals = messageParser.parseMessage(text);
        if (signals.isEmpty()) {
            log.warn("Message matched trade pattern but failed parsing: {}",
                    text.substring(0, Math.min(80, text.length())));
            return "validation_failed";
        }

        for (TradeSignal signal : signals) {
            signal.setCapitalPerTrade(telegramProperties.getCapitalPerTrade());
            signal.setSource("telegram");
        }

        List<TradeSignal> validSignals = signalValidator.filterValid(signals, "telegram-webhook");
        if (validSignals.isEmpty()) {
            log.warn("All {} parsed signals failed validation: {}",
                    signals.size(), text.substring(0, Math.min(80, text.length())));
            return "validation_failed";
        }

        log.info("Received {} valid trade signal(s) from Telegram webhook", validSignals.size());
        placeOrdersForSignals(validSignals);

        return "processed_" + validSignals.size();
    }

    private void placeOrdersForSignals(List<TradeSignal> signals) {
        String userId = schedulerProperties.getUserId() != null && !schedulerProperties.getUserId().isBlank() ?
                schedulerProperties.getUserId() : schedulerProperties.getUsername();

        for (TradeSignal signal : signals) {
            try {
                OrderRequest order = orderService.buildOrderFromSignal(signal, null);
                log.info("Placing Telegram order: {} {} {} @ {} (capital=\u20B9{})",
                        signal.getTransactionType(), signal.getInstrumentName(),
                        order.getQuantity(), signal.getEntryPrice(),
                        signal.getCapitalPerTrade());

                List<OrderResponse> responses = orderService.placeBulkOrders(List.of(order), userId);

                if (!responses.isEmpty()) {
                    OrderResponse response = responses.get(0);
                    String orderId = response.getData() != null ? response.getData().getOrderId() : "unknown";
                    if ("success".equalsIgnoreCase(response.getStatus())) {
                        log.info("Telegram order placed: {} -> orderId={}", signal.getInstrumentName(), orderId);
                        if (orderId != null) {
                            positionTracker.registerPosition(signal, orderId, order.getQuantity(), userId, order.getSecurityId());
                        }
                    } else {
                        log.error("Telegram order failed for {}: {}", signal.getInstrumentName(), orderId);
                    }
                }
            } catch (Exception ex) {
                log.error("Failed to place Telegram order for {}: {}",
                        signal.getInstrumentName(), ex.getMessage());
            }
        }
    }

    boolean isMarketHours() {
        LocalTime now = LocalTime.now(IST);
        return !now.isBefore(MARKET_OPEN) && !now.isAfter(MARKET_CLOSE);
    }

    public int getProcessedMessageCount() {
        return processedMessageIds.size();
    }

    public void clearProcessedMessages() {
        processedMessageIds.clear();
    }
}
