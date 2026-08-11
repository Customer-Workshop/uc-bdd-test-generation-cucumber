package fr.redfroggy.bdd.restapi.order;

import fr.redfroggy.bdd.restapi.error.ApiError;
import wiremock.org.apache.commons.lang3.StringUtils;

import java.math.BigDecimal;
import java.util.Optional;

final class OrderValidator {

    static final int MAX_ITEMS = 20;

    private OrderValidator() {
    }

    static Optional<ApiError> validate(OrderDTO order) {
        if (StringUtils.isBlank(order.getId())) {
            return Optional.of(new ApiError("id", "id is required"));
        }
        if (StringUtils.isBlank(order.getCustomerId())) {
            return Optional.of(new ApiError("customerId", "customerId is required"));
        }
        if (StringUtils.isBlank(order.getCurrency())) {
            return Optional.of(new ApiError("currency", "currency is required"));
        }
        if (order.getCurrency().length() != 3) {
            return Optional.of(new ApiError("currency", "currency is not a 3 letters ISO code"));
        }
        if (order.getItems() == null || order.getItems().isEmpty()) {
            return Optional.of(new ApiError("items", "at least one item is required"));
        }
        if (order.getItems().size() > MAX_ITEMS) {
            return Optional.of(new ApiError("items", "an order cannot hold more than " + MAX_ITEMS + " items"));
        }
        for (OrderItemDTO item : order.getItems()) {
            Optional<ApiError> itemError = validateItem(item);
            if (itemError.isPresent()) {
                return itemError;
            }
        }
        return Optional.empty();
    }

    private static Optional<ApiError> validateItem(OrderItemDTO item) {
        if (StringUtils.isBlank(item.getSku())) {
            return Optional.of(new ApiError("items.sku", "sku is required"));
        }
        if (item.getQuantity() == null || item.getQuantity() < 1) {
            return Optional.of(new ApiError("items.quantity", "quantity cannot be lower than 1"));
        }
        if (item.getUnitPrice() == null || item.getUnitPrice().compareTo(BigDecimal.ZERO) < 0) {
            return Optional.of(new ApiError("items.unitPrice", "unitPrice cannot be negative"));
        }
        return Optional.empty();
    }
}
