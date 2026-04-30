package com.trading.investright.model.request;

import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class OrderRequest {

    @NotBlank(message = "Exchange is required")
    private String exchange;

    @JsonProperty("security_id")
    @NotBlank(message = "Security ID is required")
    private String securityId;

    @JsonProperty("underlying_symbol")
    private String underlyingSymbol;

    @JsonProperty("instrument_segment")
    @NotBlank(message = "Instrument segment is required")
    private String instrumentSegment;

    @JsonProperty("transaction_type")
    @NotBlank(message = "Transaction type is required")
    private String transactionType;

    @NotBlank(message = "Product is required")
    private String product;

    @JsonProperty("order_type")
    @NotBlank(message = "Order type is required")
    private String orderType;

    @NotNull(message = "Price is required")
    private Double price;

    @JsonProperty("trigger_price")
    private Double triggerPrice;

    @NotNull(message = "Quantity is required")
    @Min(value = 1, message = "Quantity must be at least 1")
    private Integer quantity;

    @JsonProperty("disclosed_quantity")
    private Integer disclosedQuantity;

    @JsonProperty("option_type")
    private String optionType;

    @JsonProperty("strike_price")
    private Double strikePrice;

    @JsonProperty("expiry_date")
    private String expiryDate;

    @NotBlank(message = "Validity is required")
    private String validity;

    private Boolean amo;

    @JsonProperty("external_reference_number")
    private Long externalReferenceNumber;

    private String tradingSymbol;
}
