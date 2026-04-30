package com.trading.investright.client;

import com.trading.investright.config.InvestRightProperties;
import com.trading.investright.exception.InvestRightApiException;
import com.trading.investright.model.request.ModifyOrderRequest;
import com.trading.investright.model.request.OrderRequest;
import com.trading.investright.model.response.OrderResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.reactive.function.client.WebClientResponseException;

import java.util.List;
import java.util.Map;

@Slf4j
@Component
@RequiredArgsConstructor
public class InvestRightOrderClient {

    private final WebClient investRightWebClient;
    private final InvestRightProperties properties;

    public OrderResponse placeOrder(OrderRequest orderRequest, String accessToken) {
        log.debug("Placing order: {}", orderRequest);
        return ApiRetryHandler.executeWithRetry(() -> {
            try {
                return investRightWebClient.post()
                        .uri(uriBuilder -> uriBuilder
                                .path("/orders/regular")
                                .queryParam("api_key", properties.getApiKey())
                                .build())
                        .header("Authorization", accessToken)
                        .bodyValue(orderRequest)
                        .retrieve()
                        .bodyToMono(OrderResponse.class)
                        .block();
            } catch (WebClientResponseException ex) {
                throw new InvestRightApiException(
                        "Order placement failed: " + ex.getResponseBodyAsString(),
                        ex.getStatusCode().value(),
                        ex.getResponseBodyAsString());
            }
        }, "Place order for " + orderRequest.getSecurityId());
    }

    public OrderResponse modifyOrder(String orderId, ModifyOrderRequest modifyRequest, String accessToken) {
        log.debug("Modifying order {}: {}", orderId, modifyRequest);
        return ApiRetryHandler.executeWithRetry(() -> {
            try {
                return investRightWebClient.put()
                        .uri(uriBuilder -> uriBuilder
                                .path("/orders/regular/{orderId}")
                                .queryParam("api_key", properties.getApiKey())
                                .build(orderId))
                        .header("Authorization", accessToken)
                        .bodyValue(modifyRequest)
                        .retrieve()
                        .bodyToMono(OrderResponse.class)
                        .block();
            } catch (WebClientResponseException ex) {
                throw new InvestRightApiException(
                        "Order modification failed: " + ex.getResponseBodyAsString(),
                        ex.getStatusCode().value(),
                        ex.getResponseBodyAsString());
            }
        }, "Modify order " + orderId);
    }

    public OrderResponse cancelOrder(String orderId, String accessToken) {
        log.debug("Cancelling order: {}", orderId);
        return ApiRetryHandler.executeWithRetry(() -> {
            try {
                return investRightWebClient.delete()
                        .uri(uriBuilder -> uriBuilder
                                .path("/orders/regular/{orderId}")
                                .queryParam("api_key", properties.getApiKey())
                                .build(orderId))
                        .header("Authorization", accessToken)
                        .retrieve()
                        .bodyToMono(OrderResponse.class)
                        .block();
            } catch (WebClientResponseException ex) {
                throw new InvestRightApiException(
                        "Order cancellation failed: " + ex.getResponseBodyAsString(),
                        ex.getStatusCode().value(),
                        ex.getResponseBodyAsString());
            }
        }, "Cancel order " + orderId);
    }

    public Map<String, Object> getOrderStatus(String accessToken) {
        log.debug("Fetching all order statuses");
        return ApiRetryHandler.executeWithRetry(() -> {
            try {
                return investRightWebClient.get()
                        .uri(uriBuilder -> uriBuilder
                                .path("/orders")
                                .queryParam("api_key", properties.getApiKey())
                                .build())
                        .header("Authorization", accessToken)
                        .retrieve()
                        .bodyToMono(new ParameterizedTypeReference<Map<String, Object>>() {})
                        .block();
            } catch (WebClientResponseException ex) {
                throw new InvestRightApiException(
                        "Failed to fetch order status: " + ex.getResponseBodyAsString(),
                        ex.getStatusCode().value(),
                        ex.getResponseBodyAsString());
            }
        }, "Fetch all order statuses");
    }

    public Map<String, Object> getSingleOrderStatus(String orderId, String accessToken) {
        log.debug("Fetching order status for: {}", orderId);
        return ApiRetryHandler.executeWithRetry(() -> {
            try {
                return investRightWebClient.get()
                        .uri(uriBuilder -> uriBuilder
                                .path("/orders/{orderId}")
                                .queryParam("api_key", properties.getApiKey())
                                .build(orderId))
                        .header("Authorization", accessToken)
                        .retrieve()
                        .bodyToMono(new ParameterizedTypeReference<Map<String, Object>>() {})
                        .block();
            } catch (WebClientResponseException ex) {
                throw new InvestRightApiException(
                        "Failed to fetch order status: " + ex.getResponseBodyAsString(),
                        ex.getStatusCode().value(),
                        ex.getResponseBodyAsString());
            }
        }, "Fetch order status for " + orderId);
    }
}
