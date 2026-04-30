package com.trading.investright.model.response;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class OrderResponse {

    private String status;
    private OrderData data;

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class OrderData {

        @JsonProperty("order_id")
        private String orderId;
    }
}
