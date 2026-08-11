package fr.redfroggy.bdd.restapi.order;

import java.util.Arrays;
import java.util.Collections;
import java.util.EnumSet;
import java.util.Set;

public enum OrderStatus {

    PENDING, PAID, SHIPPED, DELIVERED, CANCELLED;

    static OrderStatus from(String value) {
        return Arrays.stream(values())
                .filter(status -> status.name().equalsIgnoreCase(value))
                .findFirst()
                .orElse(null);
    }

    /**
     * @return the statuses this status is allowed to transition to
     */
    Set<OrderStatus> allowedTransitions() {
        switch (this) {
            case PENDING:
                return EnumSet.of(PAID, CANCELLED);
            case PAID:
                return EnumSet.of(SHIPPED, CANCELLED);
            case SHIPPED:
                return EnumSet.of(DELIVERED);
            default:
                return Collections.emptySet();
        }
    }
}
