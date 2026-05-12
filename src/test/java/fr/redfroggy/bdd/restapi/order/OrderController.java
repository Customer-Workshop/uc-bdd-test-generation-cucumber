package fr.redfroggy.bdd.restapi.order;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import wiremock.org.apache.commons.lang3.StringUtils;

import java.util.*;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api")
public final class OrderController {

    private static final Set<String> VALID_STATUSES = new HashSet<>(
            Arrays.asList("pending", "confirmed", "shipped", "delivered", "cancelled"));

    public static List<OrderDTO> orders = new ArrayList<>();

    @GetMapping("/orders")
    public ResponseEntity<?> getAll(
            @RequestParam(value = "userId", required = false) String userId,
            @RequestParam(value = "status", required = false) String status,
            @RequestParam(value = "page", required = false) Integer page,
            @RequestParam(value = "size", required = false) Integer size,
            @RequestParam(value = "sort", required = false) String sort) {

        List<OrderDTO> result = orders;

        if (StringUtils.isNotBlank(userId)) {
            result = result.stream()
                    .filter(o -> userId.equals(o.getUserId()))
                    .collect(Collectors.toList());
        }

        if (StringUtils.isNotBlank(status)) {
            result = result.stream()
                    .filter(o -> status.equalsIgnoreCase(o.getStatus()))
                    .collect(Collectors.toList());
        }

        if (StringUtils.isNotBlank(sort)) {
            String[] parts = sort.split(",");
            String field = parts[0];
            boolean ascending = parts.length < 2 || "asc".equalsIgnoreCase(parts[1]);

            Comparator<OrderDTO> comparator;
            switch (field) {
                case "product":
                    comparator = Comparator.comparing(OrderDTO::getProduct, String.CASE_INSENSITIVE_ORDER);
                    break;
                case "price":
                    comparator = Comparator.comparingDouble(OrderDTO::getPrice);
                    break;
                case "quantity":
                    comparator = Comparator.comparingInt(OrderDTO::getQuantity);
                    break;
                default:
                    comparator = Comparator.comparing(OrderDTO::getId);
            }
            if (!ascending) {
                comparator = comparator.reversed();
            }
            result = result.stream().sorted(comparator).collect(Collectors.toList());
        }

        if (page != null && size != null) {
            int fromIndex = page * size;
            if (fromIndex >= result.size()) {
                return ResponseEntity.ok(Collections.emptyList());
            }
            int toIndex = Math.min(fromIndex + size, result.size());
            result = result.subList(fromIndex, toIndex);
        }

        return ResponseEntity.ok(result);
    }

    @GetMapping("/orders/{id}")
    public ResponseEntity<OrderDTO> get(@PathVariable("id") String id) {
        return orders.stream()
                .filter(o -> o.getId().equals(id))
                .findFirst()
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }

    @PostMapping("/orders")
    public ResponseEntity<?> addOrder(@RequestBody OrderDTO order) {
        if (StringUtils.isBlank(order.getId())) {
            return ResponseEntity.badRequest()
                    .body(Collections.singletonMap("error", "id is required"));
        }
        if (StringUtils.isBlank(order.getProduct())) {
            return ResponseEntity.badRequest()
                    .body(Collections.singletonMap("error", "product is required"));
        }
        if (order.getQuantity() <= 0) {
            return ResponseEntity.badRequest()
                    .body(Collections.singletonMap("error", "quantity is required to be positive"));
        }
        if (order.getPrice() < 0) {
            return ResponseEntity.badRequest()
                    .body(Collections.singletonMap("error", "price cannot be negative"));
        }
        if (StringUtils.isNotBlank(order.getStatus()) && !VALID_STATUSES.contains(order.getStatus().toLowerCase())) {
            return ResponseEntity.badRequest()
                    .body(Collections.singletonMap("error", "invalid status, must be one of: " + VALID_STATUSES));
        }

        boolean duplicate = orders.stream().anyMatch(o -> o.getId().equals(order.getId()));
        if (duplicate) {
            return ResponseEntity.status(409)
                    .body(Collections.singletonMap("error", "order with id " + order.getId() + " already exists"));
        }

        if (StringUtils.isBlank(order.getStatus())) {
            order.setStatus("pending");
        }

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

        if (StringUtils.isNotBlank(order.getStatus()) && !VALID_STATUSES.contains(order.getStatus().toLowerCase())) {
            return ResponseEntity.badRequest()
                    .body(Collections.singletonMap("error", "invalid status"));
        }

        existing.setProduct(order.getProduct());
        existing.setQuantity(order.getQuantity());
        existing.setPrice(order.getPrice());
        existing.setUserId(order.getUserId());
        if (StringUtils.isNotBlank(order.getStatus())) {
            existing.setStatus(order.getStatus());
        }

        return ResponseEntity.ok(existing);
    }

    @DeleteMapping("/orders/{id}")
    public ResponseEntity<Void> deleteOrder(@PathVariable("id") String id) {
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
