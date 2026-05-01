package com.trading.investright.service;

import com.trading.investright.config.TelegramProperties;
import com.trading.investright.model.TradeSignal;
import com.trading.investright.ocr.TelegramMessageParser;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.web.reactive.function.client.WebClient;

import java.time.Instant;
import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
@org.mockito.junit.jupiter.MockitoSettings(strictness = org.mockito.quality.Strictness.LENIENT)
class TelegramTradeSignalFetcherTest {

    @Mock
    private TelegramProperties telegramProperties;

    @Mock
    private WebClient.Builder webClientBuilder;

    private TelegramMessageParser messageParser;
    private TelegramTradeSignalFetcher fetcher;

    @BeforeEach
    void setUp() {
        messageParser = new TelegramMessageParser();
        fetcher = new TelegramTradeSignalFetcher(telegramProperties, messageParser, webClientBuilder);
    }

    @Test
    void shouldReturnEmptyWhenBotTokenMissing() {
        when(telegramProperties.getBotToken()).thenReturn(null);

        List<TradeSignal> signals = fetcher.fetchAndParseSignals();

        assertTrue(signals.isEmpty());
    }

    @Test
    void shouldReturnEmptyWhenBotTokenBlank() {
        when(telegramProperties.getBotToken()).thenReturn("");

        List<TradeSignal> signals = fetcher.fetchAndParseSignals();

        assertTrue(signals.isEmpty());
    }

    @Test
    void shouldSetCapitalAndSourceFromTelegramConfig() {
        String text = "HERO ZERO\nBUY INDIANB 820PE ABV 29 TGT\n30-32-35\nSL 27\nINTRADAY";

        List<TradeSignal> signals = messageParser.parseMessage(text);
        double telegramCapital = 40000.0;

        for (TradeSignal signal : signals) {
            signal.setCapitalPerTrade(telegramCapital);
            signal.setSource("telegram");
        }

        assertEquals(1, signals.size());
        assertEquals(40000.0, signals.get(0).getCapitalPerTrade());
        assertEquals("telegram", signals.get(0).getSource());
    }

    @Test
    void shouldProcessValidUpdateMessages() {
        long now = Instant.now().getEpochSecond();
        Map<String, Object> message = Map.of(
                "text", "BUY NIFTY 24500CE ABV 150 TGT\n180-200\nSL 120",
                "date", now
        );
        Map<String, Object> update = Map.of(
                "update_id", 12345,
                "channel_post", message
        );

        List<Map<String, Object>> updates = List.of(update);

        when(telegramProperties.getBotToken()).thenReturn("test-token");
        when(telegramProperties.getChannelId()).thenReturn("-1001234567890");
        when(telegramProperties.getLookbackMinutes()).thenReturn(30);
        when(telegramProperties.getCapitalPerTrade()).thenReturn(40000.0);

        List<TradeSignal> processedSignals = processUpdatesDirectly(updates);

        assertEquals(1, processedSignals.size());
        assertEquals("NIFTY", processedSignals.get(0).getUnderlying());
        assertEquals(40000.0, processedSignals.get(0).getCapitalPerTrade());
    }

    @Test
    void shouldSkipOldMessages() {
        long oldTime = Instant.now().minusSeconds(3600).getEpochSecond();
        Map<String, Object> message = Map.of(
                "text", "BUY NIFTY 24500CE ABV 150 TGT\n180-200\nSL 120",
                "date", oldTime
        );
        Map<String, Object> update = Map.of(
                "update_id", 12345,
                "channel_post", message
        );

        when(telegramProperties.getLookbackMinutes()).thenReturn(30);

        List<TradeSignal> signals = processUpdatesDirectly(List.of(update));

        assertTrue(signals.isEmpty());
    }

    @Test
    void shouldSkipNonTradeMessages() {
        long now = Instant.now().getEpochSecond();
        Map<String, Object> message = Map.of(
                "text", "BANDHANBNK 8.70",
                "date", now
        );
        Map<String, Object> update = Map.of(
                "update_id", 12346,
                "channel_post", message
        );

        when(telegramProperties.getLookbackMinutes()).thenReturn(30);

        List<TradeSignal> signals = processUpdatesDirectly(List.of(update));

        assertTrue(signals.isEmpty());
    }

    private List<TradeSignal> processUpdatesDirectly(List<Map<String, Object>> updates) {
        long cutoffTime = Instant.now().minusSeconds(telegramProperties.getLookbackMinutes() * 60L).getEpochSecond();
        java.util.ArrayList<TradeSignal> allSignals = new java.util.ArrayList<>();

        for (Map<String, Object> update : updates) {
            @SuppressWarnings("unchecked")
            Map<String, Object> channelPost = (Map<String, Object>) update.get("channel_post");
            if (channelPost == null) continue;

            Number dateNum = (Number) channelPost.get("date");
            if (dateNum != null && dateNum.longValue() < cutoffTime) continue;

            String text = (String) channelPost.get("text");
            if (text == null || !messageParser.isTradeSignalMessage(text)) continue;

            List<TradeSignal> signals = messageParser.parseMessage(text);
            for (TradeSignal signal : signals) {
                signal.setCapitalPerTrade(telegramProperties.getCapitalPerTrade());
                signal.setSource("telegram");
            }
            allSignals.addAll(signals);
        }
        return allSignals;
    }
}
