package fr.redfroggy.bdd.restapi.order;

public enum OrderStatus {

    PENDING,
    SHIPPED,
    CANCELLED;

    public boolean canTransitionTo(OrderStatus target) {
        return this == PENDING && (target == SHIPPED || target == CANCELLED);
    }
}
