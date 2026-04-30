package com.trading.investright.client;

import com.trading.investright.config.InvestRightProperties;
import com.trading.investright.exception.InvestRightApiException;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.reactive.function.client.WebClientResponseException;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
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

    public Map<String, Double> getBatchLtp(List<Map<String, String>> instruments, String accessToken) {
        Map<String, Double> ltpMap = new HashMap<>();
        if (instruments == null || instruments.isEmpty()) return ltpMap;

        try {
            Map<String, Object> requestBody = Map.of("data", instruments);

            Map<String, Object> response = investRightWebClient.put()
                    .uri(uriBuilder -> uriBuilder
                            .path("/fetch-ltp")
                            .queryParam("api_key", properties.getApiKey())
                            .build())
                    .header("Authorization", accessToken)
                    .bodyValue(requestBody)
                    .retrieve()
                    .bodyToMono(new ParameterizedTypeReference<Map<String, Object>>() {})
                    .block();

            if (response != null && response.containsKey("data") && response.get("data") instanceof List<?> dataList) {
                for (Object item : dataList) {
                    if (item instanceof Map<?, ?> entry) {
                        String token = entry.get("token") != null ? entry.get("token").toString() : "";
                        String exchange = entry.get("exchange") != null ? entry.get("exchange").toString() : "";
                        String key = exchange + ":" + token;

                        Object ltp = entry.get("ltp");
                        if (ltp == null) ltp = entry.get("last_traded_price");
                        if (ltp instanceof Number number) {
                            ltpMap.put(key, number.doubleValue());
                        } else if (ltp instanceof String str) {
                            try { ltpMap.put(key, Double.parseDouble(str)); } catch (NumberFormatException ignored) {}
                        }
                    }
                }
            }

            log.debug("Batch LTP fetched for {} instruments", ltpMap.size());
        } catch (Exception ex) {
            log.error("Failed to fetch batch LTP: {}", ex.getMessage());
        }
        return ltpMap;
    }

    public static List<Map<String, String>> buildBatchRequest(List<? extends LtpRequest> requests) {
        List<Map<String, String>> instruments = new ArrayList<>();
        for (LtpRequest req : requests) {
            instruments.add(Map.of("exchange", req.exchange(), "token", req.token()));
        }
        return instruments;
    }

    public record LtpRequest(String exchange, String token) {}
}
