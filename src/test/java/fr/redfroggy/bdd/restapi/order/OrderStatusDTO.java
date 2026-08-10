package fr.redfroggy.bdd.restapi.order;

import javax.validation.constraints.NotNull;

public class OrderStatusDTO {

    @NotNull
    private OrderStatus status;

    public OrderStatus getStatus() {
        return status;
    }

    public void setStatus(OrderStatus status) {
        this.status = status;
    }
}
