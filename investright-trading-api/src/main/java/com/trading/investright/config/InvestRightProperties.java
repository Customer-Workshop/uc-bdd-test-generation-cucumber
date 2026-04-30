package com.trading.investright.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

@Data
@Configuration
@ConfigurationProperties(prefix = "investright")
public class InvestRightProperties {

    private String baseUrl;
    private String apiKey;
    private String apiSecret;
    private String userAgent;
}
