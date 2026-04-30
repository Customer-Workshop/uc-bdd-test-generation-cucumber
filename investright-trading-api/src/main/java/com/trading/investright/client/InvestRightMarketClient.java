package com.trading.investright.client;

import com.trading.investright.config.InvestRightProperties;
import com.trading.investright.exception.InvestRightApiException;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.reactive.function.client.WebClientResponseException;

import java.util.Map;

@Slf4j
@Component
@RequiredArgsConstructor
public class InvestRightMarketClient {

    private final WebClient investRightWebClient;
    private final InvestRightProperties properties;

    public Map<String, Object> getQuote(String securityId, String exchange, String accessToken) {
        log.debug("Fetching quote for {} on {}", securityId, exchange);
        try {
            return investRightWebClient.get()
                    .uri(uriBuilder -> uriBuilder
                            .path("/market/quote")
                            .queryParam("api_key", properties.getApiKey())
                            .queryParam("security_id", securityId)
                            .queryParam("exchange", exchange)
                            .build())
                    .header("Authorization", accessToken)
                    .retrieve()
                    .bodyToMono(new ParameterizedTypeReference<Map<String, Object>>() {})
                    .block();
        } catch (WebClientResponseException ex) {
            throw new InvestRightApiException(
                    "Failed to fetch quote for " + securityId + ": " + ex.getResponseBodyAsString(),
                    ex.getStatusCode().value(),
                    ex.getResponseBodyAsString());
        }
    }

    public Double getLastTradedPrice(String securityId, String exchange, String accessToken) {
        try {
            Map<String, Object> quote = getQuote(securityId, exchange, accessToken);
            if (quote == null || !quote.containsKey("data")) {
                log.warn("No quote data for {}", securityId);
                return null;
            }

            Object data = quote.get("data");
            if (data instanceof Map<?, ?> dataMap) {
                Object ltp = dataMap.get("last_traded_price");
                if (ltp == null) ltp = dataMap.get("ltp");
                if (ltp instanceof Number number) {
                    return number.doubleValue();
                }
                if (ltp instanceof String str) {
                    return Double.parseDouble(str);
                }
            }
            return null;
        } catch (Exception ex) {
            log.error("Failed to get LTP for {}: {}", securityId, ex.getMessage());
            return null;
        }
    }
}
