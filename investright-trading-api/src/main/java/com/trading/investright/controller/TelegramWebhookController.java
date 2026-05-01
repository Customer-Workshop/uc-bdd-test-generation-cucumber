package com.trading.investright.controller;

import com.trading.investright.config.TelegramProperties;
import com.trading.investright.service.TelegramWebhookService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@Slf4j
@RestController
@RequestMapping("/api/telegram")
@RequiredArgsConstructor
@ConditionalOnProperty(name = "telegram.enabled", havingValue = "true")
public class TelegramWebhookController {

    private final TelegramWebhookService webhookService;
    private final TelegramProperties telegramProperties;

    @PostMapping("/webhook")
    public ResponseEntity<Map<String, String>> handleWebhook(
            @RequestBody Map<String, Object> update,
            @RequestHeader(value = "X-Telegram-Bot-Api-Secret-Token", required = false) String secretToken) {

        if (telegramProperties.getWebhookSecret() != null
                && !telegramProperties.getWebhookSecret().isBlank()
                && !telegramProperties.getWebhookSecret().equals(secretToken)) {
            log.warn("Telegram webhook rejected: invalid secret token");
            return ResponseEntity.status(403).body(Map.of("status", "forbidden"));
        }

        String result = webhookService.processWebhookUpdate(update);
        return ResponseEntity.ok(Map.of("status", "ok", "result", result));
    }
}
