package fr.redfroggy.bdd.restapi.order;

import fr.redfroggy.bdd.restapi.support.ApiError;
import wiremock.org.apache.commons.lang3.StringUtils;

import java.util.Arrays;

final class OrderValidator {

    static final int MAX_QUANTITY = 100;

    private OrderValidator() {
    }

    /**
     * @return an {@link ApiError} describing the first invalid field, null when the order is valid
     */
    static ApiError validate(OrderDTO order) {
        if (order == null) {
            return new ApiError("an order payload is required", "body");
        }
        if (StringUtils.isBlank(order.getId())) {
            return new ApiError("id is required", "id");
        }
        if (StringUtils.isBlank(order.getCustomerId())) {
            return new ApiError("customerId is required", "customerId");
        }
        if (StringUtils.isBlank(order.getProduct())) {
            return new ApiError("product is required", "product");
        }
        if (order.getQuantity() < 1) {
            return new ApiError("quantity must be greater than 0", "quantity");
        }
        if (order.getQuantity() > MAX_QUANTITY) {
            return new ApiError("quantity must not exceed " + MAX_QUANTITY, "quantity");
        }
        if (order.getUnitPrice() < 0) {
            return new ApiError("unitPrice must be greater than or equal to 0", "unitPrice");
        }
        if (StringUtils.isNotBlank(order.getStatus()) && OrderStatus.from(order.getStatus()) == null) {
            return new ApiError(unknownStatusMessage(order.getStatus()), "status");
        }
        return null;
    }

    static String unknownStatusMessage(String status) {
        return "unknown status: " + status + ", expected one of " + Arrays.toString(OrderStatus.values());
    }
}
