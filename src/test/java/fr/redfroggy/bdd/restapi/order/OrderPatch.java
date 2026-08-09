package fr.redfroggy.bdd.restapi.order;

public class OrderPatch {

    private OrderStatus status;

    public OrderStatus getStatus() {
        return status;
    }

    public void setStatus(OrderStatus status) {
        this.status = status;
    }
}
