package fr.redfroggy.bdd.restapi.order;

import java.util.Arrays;
import java.util.Collections;
import java.util.EnumSet;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.stream.Collectors;

public enum OrderStatus {

    CREATED,
    PAID,
    SHIPPED,
    DELIVERED,
    CANCELLED;

    static Optional<OrderStatus> from(String value) {
        return Arrays.stream(values())
                .filter(status -> status.name().equalsIgnoreCase(value))
                .findFirst();
    }

    Set<OrderStatus> allowedTransitions() {
        switch (this) {
            case CREATED:
                return EnumSet.of(PAID, CANCELLED);
            case PAID:
                return EnumSet.of(SHIPPED, CANCELLED);
            case SHIPPED:
                return EnumSet.of(DELIVERED);
            default:
                return Collections.emptySet();
        }
    }

    static List<String> names() {
        return Arrays.stream(values()).map(Enum::name).collect(Collectors.toList());
    }
}
