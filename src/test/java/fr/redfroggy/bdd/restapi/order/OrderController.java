package fr.redfroggy.bdd.restapi.order;

import fr.redfroggy.bdd.restapi.user.ErrorResponse;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import wiremock.org.apache.commons.lang3.StringUtils;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api")
public class OrderController {

    private static final List<String> VALID_STATUSES = Arrays.asList(
            "PENDING", "CONFIRMED", "SHIPPED", "DELIVERED", "CANCELLED"
    );

    public static List<OrderDTO> orders = new ArrayList<>();

    @GetMapping("/orders")
    public ResponseEntity<List<OrderDTO>> getAll(
            @RequestParam(value = "userId", required = false) String userId,
            @RequestParam(value = "status", required = false) String status) {

        List<OrderDTO> result = orders.stream()
                .filter(o -> userId == null || o.getUserId().equals(userId))
                .filter(o -> status == null || o.getStatus().equalsIgnoreCase(status))
                .collect(Collectors.toList());

        return ResponseEntity.ok(result);
    }

    @GetMapping("/orders/{id}")
    public ResponseEntity<?> get(@PathVariable("id") String id) {
        OrderDTO order = orders.stream()
                .filter(o -> o.getId().equals(id))
                .findFirst()
                .orElse(null);

        if (order == null) {
            return ResponseEntity.notFound().build();
        }

        return ResponseEntity.ok()
                .header(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_JSON_VALUE)
                .body(order);
    }

    @PostMapping("/orders")
    public ResponseEntity<?> createOrder(@RequestBody OrderDTO order) {
        if (order.getId() == null || StringUtils.isBlank(order.getId())) {
            return ResponseEntity.badRequest()
                    .body(new ErrorResponse(400, "Bad Request", "id is required"));
        }
        if (order.getUserId() == null || StringUtils.isBlank(order.getUserId())) {
            return ResponseEntity.badRequest()
                    .body(new ErrorResponse(400, "Bad Request", "userId is required"));
        }
        if (order.getItems() == null || order.getItems().isEmpty()) {
            return ResponseEntity.badRequest()
                    .body(new ErrorResponse(400, "Bad Request", "items required and cannot be empty"));
        }

        OrderDTO existing = orders.stream()
                .filter(o -> o.getId().equals(order.getId()))
                .findFirst()
                .orElse(null);
        if (existing != null) {
            return ResponseEntity.status(409)
                    .body(new ErrorResponse(409, "Conflict", "Order with id " + order.getId() + " already exists"));
        }

        if (order.getStatus() == null || StringUtils.isBlank(order.getStatus())) {
            order.setStatus("PENDING");
        }

        double total = order.getItems().stream()
                .mapToDouble(item -> item.getPrice() * item.getQuantity())
                .sum();
        order.setTotalAmount(total);

        orders.add(order);
        return ResponseEntity.status(201).body(order);
    }

    @PutMapping("/orders/{id}")
    public ResponseEntity<?> updateOrder(@RequestBody OrderDTO order, @PathVariable String id) {
        OrderDTO existing = orders.stream()
                .filter(o -> o.getId().equals(id))
                .findFirst()
                .orElse(null);

        if (existing == null) {
            return ResponseEntity.notFound().build();
        }

        if (order.getStatus() != null && !VALID_STATUSES.contains(order.getStatus().toUpperCase())) {
            return ResponseEntity.badRequest()
                    .body(new ErrorResponse(400, "Bad Request",
                            "Invalid status. Must be one of: " + String.join(", ", VALID_STATUSES)));
        }

        existing.setUserId(order.getUserId() != null ? order.getUserId() : existing.getUserId());
        existing.setStatus(order.getStatus() != null ? order.getStatus().toUpperCase() : existing.getStatus());
        if (order.getItems() != null && !order.getItems().isEmpty()) {
            existing.setItems(order.getItems());
            double total = order.getItems().stream()
                    .mapToDouble(item -> item.getPrice() * item.getQuantity())
                    .sum();
            existing.setTotalAmount(total);
        }

        return ResponseEntity.ok(existing);
    }

    @PatchMapping("/orders/{id}/status")
    public ResponseEntity<?> updateOrderStatus(@RequestBody OrderDTO partial, @PathVariable String id) {
        OrderDTO existing = orders.stream()
                .filter(o -> o.getId().equals(id))
                .findFirst()
                .orElse(null);

        if (existing == null) {
            return ResponseEntity.notFound().build();
        }

        if (partial.getStatus() == null || !VALID_STATUSES.contains(partial.getStatus().toUpperCase())) {
            return ResponseEntity.badRequest()
                    .body(new ErrorResponse(400, "Bad Request",
                            "Invalid status. Must be one of: " + String.join(", ", VALID_STATUSES)));
        }

        existing.setStatus(partial.getStatus().toUpperCase());
        return ResponseEntity.ok(existing);
    }

    @DeleteMapping("/orders/{id}")
    public ResponseEntity<?> deleteOrder(@PathVariable("id") String id) {
        OrderDTO existing = orders.stream()
                .filter(o -> o.getId().equals(id))
                .findFirst()
                .orElse(null);

        if (existing == null) {
            return ResponseEntity.notFound().build();
        }

        orders = orders.stream()
                .filter(o -> !o.getId().equals(id))
                .collect(Collectors.toList());

        return ResponseEntity.ok().build();
    }
}
