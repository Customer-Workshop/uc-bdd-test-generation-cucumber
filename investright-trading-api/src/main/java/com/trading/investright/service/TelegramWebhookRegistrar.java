package com.trading.investright.service;

import com.trading.investright.config.TelegramProperties;
import jakarta.annotation.PostConstruct;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClient;

import java.util.Map;

@Slf4j
@Component
@RequiredArgsConstructor
@ConditionalOnProperty(name = "telegram.enabled", havingValue = "true")
public class TelegramWebhookRegistrar {

    private final TelegramProperties telegramProperties;
    private final WebClient.Builder webClientBuilder;

    private static final String TELEGRAM_API_BASE = "https://api.telegram.org/bot";

    @PostConstruct
    public void registerWebhook() {
        String webhookUrl = telegramProperties.getWebhookUrl();
        String token = telegramProperties.getBotToken();

        if (webhookUrl == null || webhookUrl.isBlank()) {
            log.info("No webhook URL configured — Telegram will use polling mode");
            return;
        }

        if (token == null || token.isBlank()) {
            log.error("Cannot register webhook: bot token not configured");
            return;
        }

        try {
            String url = TELEGRAM_API_BASE + token + "/setWebhook";

            WebClient client = webClientBuilder.build();

            var requestBody = new java.util.HashMap<String, Object>();
            requestBody.put("url", webhookUrl);
            requestBody.put("allowed_updates", new String[]{"channel_post", "message"});

            String secret = telegramProperties.getWebhookSecret();
            if (secret != null && !secret.isBlank()) {
                requestBody.put("secret_token", secret);
            }

            @SuppressWarnings("unchecked")
            Map<String, Object> response = client.post()
                    .uri(url)
                    .bodyValue(requestBody)
                    .retrieve()
                    .bodyToMono(Map.class)
                    .block();

            if (response != null && Boolean.TRUE.equals(response.get("ok"))) {
                log.info("Telegram webhook registered: {}", webhookUrl);
            } else {
                log.error("Failed to register Telegram webhook: {}", response);
            }
        } catch (Exception ex) {
            log.error("Error registering Telegram webhook: {}", ex.getMessage());
        }
    }
}
