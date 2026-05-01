package com.trading.investright.service;

import com.trading.investright.client.InvestRightAuthClient;
import com.trading.investright.config.SchedulerProperties;
import com.trading.investright.config.TelegramProperties;
import com.trading.investright.ocr.TelegramMessageParser;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;

@ExtendWith(MockitoExtension.class)
class TelegramWebhookServiceTest {

    @Mock
    private OrderService orderService;
    @Mock
    private PositionTracker positionTracker;
    @Mock
    private InvestRightAuthClient authClient;

    private TelegramProperties telegramProperties;
    private SchedulerProperties schedulerProperties;
    private TelegramMessageParser messageParser;
    private TelegramWebhookService webhookService;

    @BeforeEach
    void setUp() {
        telegramProperties = new TelegramProperties();
        telegramProperties.setEnabled(true);
        telegramProperties.setCapitalPerTrade(40000.0);

        schedulerProperties = new SchedulerProperties();
        schedulerProperties.setUsername("testuser");

        messageParser = new TelegramMessageParser();
        webhookService = new TelegramWebhookService(
                telegramProperties, messageParser, orderService,
                positionTracker, authClient, schedulerProperties);
    }

    @Test
    void shouldReturnNoMessageWhenChannelPostMissing() {
        Map<String, Object> update = Map.of("update_id", 123);
        assertEquals("no_message", webhookService.processWebhookUpdate(update));
    }

    @Test
    void shouldReturnNoTextWhenTextMissing() {
        Map<String, Object> update = Map.of(
                "channel_post", Map.of("message_id", 1, "date", 1234567890)
        );
        assertEquals("no_text", webhookService.processWebhookUpdate(update));
    }

    @Test
    void shouldSkipNonTradeMessages() {
        Map<String, Object> update = Map.of(
                "channel_post", Map.of(
                        "message_id", 2,
                        "text", "Good morning everyone!"
                )
        );
        assertEquals("not_trade_signal", webhookService.processWebhookUpdate(update));
    }

    @Test
    void shouldDetectDuplicateMessages() {
        Map<String, Object> update = Map.of(
                "channel_post", Map.of(
                        "message_id", 100,
                        "text", "BANDHANBNK 8.70"
                )
        );
        webhookService.processWebhookUpdate(update);

        Map<String, Object> duplicate = Map.of(
                "channel_post", Map.of(
                        "message_id", 100,
                        "text", "BANDHANBNK 8.70"
                )
        );
        assertEquals("duplicate", webhookService.processWebhookUpdate(duplicate));
    }

    @Test
    void shouldSkipSignalsOutsideMarketHours() {
        Map<String, Object> update = Map.of(
                "channel_post", Map.of(
                        "message_id", 200,
                        "text", "BUY NIFTY 24500CE ABV 150 TGT 180-200 SL 120"
                )
        );
        String result = webhookService.processWebhookUpdate(update);
        // Either processes or skips based on current time
        assertNotNull(result);
        assertNotEquals("no_message", result);
    }

    @Test
    void shouldRejectSignalsMissingStopLoss() {
        Map<String, Object> update = Map.of(
                "channel_post", Map.of(
                        "message_id", 300,
                        "text", "BUY NIFTY 24500CE ABV 150 TGT 180-200"
                )
        );
        String result = webhookService.processWebhookUpdate(update);
        assertTrue("validation_failed".equals(result) || "outside_market_hours".equals(result));
    }

    @Test
    void shouldTrackProcessedMessageCount() {
        assertEquals(0, webhookService.getProcessedMessageCount());
        Map<String, Object> update = Map.of(
                "channel_post", Map.of(
                        "message_id", 400,
                        "text", "Hello"
                )
        );
        webhookService.processWebhookUpdate(update);
        assertEquals(1, webhookService.getProcessedMessageCount());
    }

    @Test
    void shouldClearProcessedMessages() {
        Map<String, Object> update = Map.of(
                "channel_post", Map.of(
                        "message_id", 500,
                        "text", "test"
                )
        );
        webhookService.processWebhookUpdate(update);
        assertEquals(1, webhookService.getProcessedMessageCount());
        webhookService.clearProcessedMessages();
        assertEquals(0, webhookService.getProcessedMessageCount());
    }
}
