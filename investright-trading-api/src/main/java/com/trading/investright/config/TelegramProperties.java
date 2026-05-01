package com.trading.investright.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

@Data
@Configuration
@ConfigurationProperties(prefix = "telegram")
public class TelegramProperties {

    private boolean enabled = false;
    private String botToken;
    private String channelId;
    private double capitalPerTrade = 40000.0;
    private int lookbackMinutes = 30;
    private String webhookUrl;
    private String webhookSecret;
}
