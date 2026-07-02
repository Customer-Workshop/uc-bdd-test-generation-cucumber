package fr.redfroggy.bdd.restapi.order;

import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import wiremock.org.apache.commons.lang3.StringUtils;

import java.util.*;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api")
public final class OrderController {

    private static final Set<String> VALID_STATUSES = new LinkedHashSet<>(
            Arrays.asList("PENDING", "CONFIRMED", "SHIPPED", "DELIVERED", "CANCELLED"));

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
            String[] sortParts = sort.split(",");
            String sortField = sortParts[0];
            boolean ascending = sortParts.length < 2 || "asc".equalsIgnoreCase(sortParts[1]);

            Comparator<OrderDTO> comparator = getOrderComparator(sortField);
            if (comparator != null) {
                if (!ascending) {
                    comparator = comparator.reversed();
                }
                result = result.stream().sorted(comparator).collect(Collectors.toList());
            }
        }

        if (page != null && size != null) {
            if (page < 0 || size <= 0) {
                return ResponseEntity.badRequest()
                        .body(Collections.singletonMap("error", "Invalid pagination parameters"));
            }
            int fromIndex = page * size;
            if (fromIndex >= result.size()) {
                Map<String, Object> pageResponse = new LinkedHashMap<>();
                pageResponse.put("content", Collections.emptyList());
                pageResponse.put("page", page);
                pageResponse.put("size", size);
                pageResponse.put("totalElements", result.size());
                pageResponse.put("totalPages", (int) Math.ceil((double) result.size() / size));
                return ResponseEntity.ok(pageResponse);
            }
            int toIndex = Math.min(fromIndex + size, result.size());
            List<OrderDTO> pageContent = result.subList(fromIndex, toIndex);

            Map<String, Object> pageResponse = new LinkedHashMap<>();
            pageResponse.put("content", pageContent);
            pageResponse.put("page", page);
            pageResponse.put("size", size);
            pageResponse.put("totalElements", result.size());
            pageResponse.put("totalPages", (int) Math.ceil((double) result.size() / size));
            return ResponseEntity.ok(pageResponse);
        }

        return ResponseEntity.ok(result);
    }

    @GetMapping("/orders/{id}")
    public ResponseEntity<OrderDTO> get(@PathVariable("id") String id) {
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

    @PostMapping(value = "/orders")
    public ResponseEntity<?> addOrder(@RequestBody OrderDTO order) {
        List<String> errors = validateOrder(order);
        if (!errors.isEmpty()) {
            return ResponseEntity.badRequest()
                    .body(Collections.singletonMap("errors", errors));
        }

        OrderDTO existing = orders.stream()
                .filter(o -> o.getId().equals(order.getId()))
                .findFirst()
                .orElse(null);
        if (existing != null) {
            return ResponseEntity.status(409)
                    .body(Collections.singletonMap("error", "Order with id " + order.getId() + " already exists"));
        }

        if (StringUtils.isBlank(order.getStatus())) {
            order.setStatus("PENDING");
        }

        orders.add(order);
        return ResponseEntity.status(201).body(order);
    }

    @PutMapping(value = "/orders/{id}")
    public ResponseEntity<?> updateOrder(@RequestBody OrderDTO order, @PathVariable String id) {
        OrderDTO currentOrder = orders.stream()
                .filter(o -> o.getId().equals(id))
                .findFirst()
                .orElse(null);
        if (currentOrder == null) {
            return ResponseEntity.notFound().build();
        }

        if (order.getStatus() != null && !VALID_STATUSES.contains(order.getStatus().toUpperCase())) {
            return ResponseEntity.badRequest()
                    .body(Collections.singletonMap("error", "Invalid status: " + order.getStatus()));
        }

        currentOrder.setProduct(order.getProduct());
        currentOrder.setQuantity(order.getQuantity());
        currentOrder.setPrice(order.getPrice());
        if (order.getStatus() != null) {
            currentOrder.setStatus(order.getStatus().toUpperCase());
        }
        if (order.getItems() != null) {
            currentOrder.setItems(order.getItems());
        }

        return ResponseEntity.ok(currentOrder);
    }

    @PatchMapping(value = "/orders/{id}/status")
    public ResponseEntity<?> updateOrderStatus(@RequestBody Map<String, String> body, @PathVariable String id) {
        OrderDTO currentOrder = orders.stream()
                .filter(o -> o.getId().equals(id))
                .findFirst()
                .orElse(null);
        if (currentOrder == null) {
            return ResponseEntity.notFound().build();
        }

        String newStatus = body.get("status");
        if (StringUtils.isBlank(newStatus) || !VALID_STATUSES.contains(newStatus.toUpperCase())) {
            return ResponseEntity.badRequest()
                    .body(Collections.singletonMap("error", "Invalid status: " + newStatus));
        }

        currentOrder.setStatus(newStatus.toUpperCase());
        return ResponseEntity.ok(currentOrder);
    }

    @DeleteMapping(value = "/orders/{id}")
    public ResponseEntity<Void> deleteOrder(@PathVariable("id") String id) {
        OrderDTO currentOrder = orders.stream()
                .filter(o -> o.getId().equals(id))
                .findFirst()
                .orElse(null);
        if (currentOrder == null) {
            return ResponseEntity.notFound().build();
        }

        orders = orders.stream()
                .filter(o -> !o.getId().equals(id))
                .collect(Collectors.toList());

        return ResponseEntity.ok().build();
    }

    private List<String> validateOrder(OrderDTO order) {
        List<String> errors = new ArrayList<>();

        if (StringUtils.isBlank(order.getId())) {
            errors.add("id is required");
        }
        if (StringUtils.isBlank(order.getUserId())) {
            errors.add("userId is required");
        }
        if (StringUtils.isBlank(order.getProduct())) {
            errors.add("product is required");
        }
        if (order.getQuantity() <= 0) {
            errors.add("quantity must be greater than 0");
        }
        if (order.getPrice() < 0) {
            errors.add("price must not be negative");
        }
        if (order.getStatus() != null && !StringUtils.isBlank(order.getStatus())
                && !VALID_STATUSES.contains(order.getStatus().toUpperCase())) {
            errors.add("Invalid status. Must be one of: " + VALID_STATUSES);
        }

        return errors;
    }

    private Comparator<OrderDTO> getOrderComparator(String field) {
        switch (field) {
            case "price":
                return Comparator.comparingDouble(OrderDTO::getPrice);
            case "quantity":
                return Comparator.comparingInt(OrderDTO::getQuantity);
            case "product":
                return Comparator.comparing(OrderDTO::getProduct, String.CASE_INSENSITIVE_ORDER);
            case "status":
                return Comparator.comparing(OrderDTO::getStatus, String.CASE_INSENSITIVE_ORDER);
            case "id":
                return Comparator.comparing(OrderDTO::getId);
            default:
                return null;
        }
    }
}
