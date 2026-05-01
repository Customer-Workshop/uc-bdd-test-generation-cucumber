package com.trading.investright.service;

import com.trading.investright.config.TelegramProperties;
import com.trading.investright.model.TradeSignal;
import com.trading.investright.ocr.TelegramMessageParser;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;

import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

@Slf4j
@Service
@RequiredArgsConstructor
@ConditionalOnProperty(name = "telegram.enabled", havingValue = "true")
public class TelegramTradeSignalFetcher {

    private final TelegramProperties telegramProperties;
    private final TelegramMessageParser messageParser;
    private final WebClient.Builder webClientBuilder;

    private static final String TELEGRAM_API_BASE = "https://api.telegram.org/bot";
    private long lastUpdateId = 0;

    public List<TradeSignal> fetchAndParseSignals() {
        String token = telegramProperties.getBotToken();
        String channelId = telegramProperties.getChannelId();

        if (token == null || token.isBlank()) {
            log.error("Telegram bot token is not configured");
            return List.of();
        }

        log.info("Fetching trade signals from Telegram channel: {}", channelId);

        List<TradeSignal> allSignals = new ArrayList<>();

        try {
            List<Map<String, Object>> messages = fetchRecentMessages(token);

            long cutoffTime = Instant.now().minusSeconds(telegramProperties.getLookbackMinutes() * 60L).getEpochSecond();

            for (Map<String, Object> update : messages) {
                try {
                    Map<String, Object> message = extractMessage(update);
                    if (message == null) continue;

                    Number dateNum = (Number) message.get("date");
                    if (dateNum != null && dateNum.longValue() < cutoffTime) {
                        continue;
                    }

                    String text = (String) message.get("text");
                    if (text == null || text.isBlank()) continue;

                    if (!messageParser.isTradeSignalMessage(text)) {
                        log.debug("Skipping non-trade message: {}", text.substring(0, Math.min(50, text.length())));
                        continue;
                    }

                    List<TradeSignal> signals = messageParser.parseMessage(text);
                    for (TradeSignal signal : signals) {
                        signal.setCapitalPerTrade(telegramProperties.getCapitalPerTrade());
                        signal.setSource("telegram");
                    }
                    allSignals.addAll(signals);
                } catch (Exception ex) {
                    log.warn("Failed to process Telegram message: {}", ex.getMessage());
                }
            }
        } catch (Exception ex) {
            log.error("Failed to fetch Telegram messages: {}", ex.getMessage());
        }

        log.info("Parsed {} trade signals from Telegram", allSignals.size());
        return allSignals;
    }

    @SuppressWarnings("unchecked")
    List<Map<String, Object>> fetchRecentMessages(String token) {
        String url = TELEGRAM_API_BASE + token + "/getUpdates";

        WebClient client = webClientBuilder.build();
        Map<String, Object> response = client.get()
                .uri(url, uriBuilder -> {
                    uriBuilder.queryParam("allowed_updates", "channel_post");
                    if (lastUpdateId > 0) {
                        uriBuilder.queryParam("offset", lastUpdateId + 1);
                    }
                    return uriBuilder.build();
                })
                .retrieve()
                .bodyToMono(Map.class)
                .block();

        if (response == null || !Boolean.TRUE.equals(response.get("ok"))) {
            log.error("Telegram API returned error: {}", response);
            return List.of();
        }

        List<Map<String, Object>> results = (List<Map<String, Object>>) response.get("result");
        if (results == null) return List.of();

        if (!results.isEmpty()) {
            Map<String, Object> lastUpdate = results.get(results.size() - 1);
            Number updateId = (Number) lastUpdate.get("update_id");
            if (updateId != null) {
                lastUpdateId = updateId.longValue();
            }
        }

        log.info("Fetched {} updates from Telegram", results.size());
        return results;
    }

    @SuppressWarnings("unchecked")
    private Map<String, Object> extractMessage(Map<String, Object> update) {
        Map<String, Object> channelPost = (Map<String, Object>) update.get("channel_post");
        if (channelPost != null) return channelPost;

        Map<String, Object> message = (Map<String, Object>) update.get("message");
        return message;
    }
}
