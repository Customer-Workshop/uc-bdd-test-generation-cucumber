package com.trading.investright.model.request;

import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.NotBlank;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ModifyOrderRequest {

    private String product;

    private Integer quantity;

    @JsonProperty("order_type")
    @NotBlank(message = "Order type is required")
    private String orderType;

    private Double price;

    @JsonProperty("trigger_price")
    private Double triggerPrice;

    @JsonProperty("disclosed_quantity")
    private Integer disclosedQuantity;

    private String validity;

    private Boolean amo;
}
