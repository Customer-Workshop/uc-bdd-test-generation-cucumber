package com.trading.investright.config;

import lombok.RequiredArgsConstructor;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpHeaders;
import org.springframework.web.reactive.function.client.WebClient;

@Configuration
@RequiredArgsConstructor
public class WebClientConfig {

    private final InvestRightProperties investRightProperties;

    @Bean
    public WebClient investRightWebClient() {
        return WebClient.builder()
                .baseUrl(investRightProperties.getBaseUrl())
                .defaultHeader(HttpHeaders.USER_AGENT, investRightProperties.getUserAgent())
                .defaultHeader(HttpHeaders.CONTENT_TYPE, "application/json")
                .codecs(configurer -> configurer.defaultCodecs().maxInMemorySize(5 * 1024 * 1024))
                .build();
    }
}
