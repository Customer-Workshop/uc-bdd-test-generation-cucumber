package fr.redfroggy.bdd.restapi.order;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import wiremock.org.apache.commons.lang3.StringUtils;

import java.util.*;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api")
public final class OrderController {

    public static List<OrderDTO> orders = new ArrayList<>();

    private static final Set<String> VALID_STATUSES = Set.of("PENDING", "CONFIRMED", "SHIPPED", "DELIVERED", "CANCELLED");

    @GetMapping("/orders")
    public ResponseEntity<?> getAll(
            @RequestParam(value = "userId", required = false) String userId,
            @RequestParam(value = "status", required = false) String status,
            @RequestParam(value = "page", required = false) Integer page,
            @RequestParam(value = "size", required = false) Integer size,
            @RequestParam(value = "sort", required = false) String sort) {

        List<OrderDTO> result = orders;

        if (StringUtils.isNotBlank(userId)) {
            result = result.stream().filter(o -> userId.equals(o.getUserId()))
                    .collect(Collectors.toList());
        }

        if (StringUtils.isNotBlank(status)) {
            result = result.stream().filter(o -> status.equalsIgnoreCase(o.getStatus()))
                    .collect(Collectors.toList());
        }

        if (StringUtils.isNotBlank(sort)) {
            Comparator<OrderDTO> comparator;
            String field = sort;
            boolean descending = false;

            if (sort.startsWith("-")) {
                field = sort.substring(1);
                descending = true;
            }

            switch (field) {
                case "price":
                    comparator = Comparator.comparingDouble(OrderDTO::getPrice);
                    break;
                case "quantity":
                    comparator = Comparator.comparingInt(OrderDTO::getQuantity);
                    break;
                case "product":
                    comparator = Comparator.comparing(OrderDTO::getProduct, Comparator.nullsLast(String::compareToIgnoreCase));
                    break;
                default:
                    comparator = Comparator.comparing(OrderDTO::getId, Comparator.nullsLast(String::compareTo));
                    break;
            }

            if (descending) {
                comparator = comparator.reversed();
            }
            result = result.stream().sorted(comparator).collect(Collectors.toList());
        }

        if (page != null && size != null) {
            int fromIndex = page * size;
            int toIndex = Math.min(fromIndex + size, result.size());

            int totalElements = result.size();
            int totalPages = (int) Math.ceil((double) totalElements / size);

            if (fromIndex >= result.size()) {
                result = Collections.emptyList();
            } else {
                result = result.subList(fromIndex, toIndex);
            }

            Map<String, Object> pagedResponse = new LinkedHashMap<>();
            pagedResponse.put("content", result);
            pagedResponse.put("page", page);
            pagedResponse.put("size", size);
            pagedResponse.put("totalElements", totalElements);
            pagedResponse.put("totalPages", totalPages);
            return ResponseEntity.ok(pagedResponse);
        }

        return ResponseEntity.ok(result);
    }

    @GetMapping("/orders/{id}")
    public ResponseEntity<?> get(@PathVariable("id") String id) {
        OrderDTO order = orders.stream().filter(o -> o.getId().equals(id))
                .findFirst().orElse(null);
        if (order == null) {
            return ResponseEntity.notFound().build();
        }
        return ResponseEntity.ok(order);
    }

    @PostMapping("/orders")
    public ResponseEntity<?> addOrder(@RequestBody OrderDTO order) {

        Map<String, String> errors = new LinkedHashMap<>();

        if (StringUtils.isBlank(order.getId())) {
            errors.put("id", "id is required");
        }
        if (StringUtils.isBlank(order.getProduct())) {
            errors.put("product", "product is required");
        }
        if (order.getQuantity() <= 0) {
            errors.put("quantity", "quantity requires a positive value");
        }
        if (order.getPrice() <= 0) {
            errors.put("price", "price requires a positive value");
        }

        if (!errors.isEmpty()) {
            Map<String, Object> errorResponse = new LinkedHashMap<>();
            errorResponse.put("status", 400);
            errorResponse.put("error", "Bad Request");
            errorResponse.put("errors", errors);
            return ResponseEntity.badRequest().body(errorResponse);
        }

        if (StringUtils.isBlank(order.getStatus())) {
            order.setStatus("PENDING");
        } else if (!VALID_STATUSES.contains(order.getStatus().toUpperCase())) {
            Map<String, Object> errorResponse = new LinkedHashMap<>();
            errorResponse.put("status", 400);
            errorResponse.put("error", "Bad Request");
            errorResponse.put("errors", Map.of("status", "Invalid status. Valid values: " + VALID_STATUSES));
            return ResponseEntity.badRequest().body(errorResponse);
        } else {
            order.setStatus(order.getStatus().toUpperCase());
        }

        OrderDTO existing = orders.stream().filter(o -> o.getId().equals(order.getId()))
                .findFirst().orElse(null);
        if (existing != null) {
            Map<String, Object> conflictResponse = new LinkedHashMap<>();
            conflictResponse.put("status", 409);
            conflictResponse.put("error", "Conflict");
            conflictResponse.put("message", "Order with id " + order.getId() + " already exists");
            return ResponseEntity.status(409).body(conflictResponse);
        }

        orders.add(order);
        return ResponseEntity.status(201).body(order);
    }

    @PutMapping("/orders/{id}")
    public ResponseEntity<?> updateOrder(@RequestBody OrderDTO order, @PathVariable String id) {

        OrderDTO currentOrder = orders.stream().filter(o -> o.getId().equals(id))
                .findFirst().orElse(null);
        if (currentOrder == null) {
            return ResponseEntity.notFound().build();
        }

        if (StringUtils.isNotBlank(order.getStatus()) && !VALID_STATUSES.contains(order.getStatus().toUpperCase())) {
            Map<String, Object> errorResponse = new LinkedHashMap<>();
            errorResponse.put("status", 400);
            errorResponse.put("error", "Bad Request");
            errorResponse.put("errors", Map.of("status", "Invalid status. Valid values: " + VALID_STATUSES));
            return ResponseEntity.badRequest().body(errorResponse);
        }

        orders.stream().filter(o -> id.equals(o.getId())).forEach(o -> {
            if (StringUtils.isNotBlank(order.getProduct())) {
                o.setProduct(order.getProduct());
            }
            if (order.getQuantity() > 0) {
                o.setQuantity(order.getQuantity());
            }
            if (order.getPrice() > 0) {
                o.setPrice(order.getPrice());
            }
            if (StringUtils.isNotBlank(order.getStatus())) {
                o.setStatus(order.getStatus().toUpperCase());
            }
            if (order.getTags() != null) {
                o.setTags(order.getTags());
            }
        });

        OrderDTO updated = orders.stream().filter(o -> id.equals(o.getId())).findFirst().orElse(null);
        return ResponseEntity.ok(updated);
    }

    @PatchMapping("/orders/{id}/status")
    public ResponseEntity<?> updateStatus(@RequestBody Map<String, String> body, @PathVariable String id) {

        OrderDTO currentOrder = orders.stream().filter(o -> o.getId().equals(id))
                .findFirst().orElse(null);
        if (currentOrder == null) {
            return ResponseEntity.notFound().build();
        }

        String newStatus = body.get("status");
        if (StringUtils.isBlank(newStatus) || !VALID_STATUSES.contains(newStatus.toUpperCase())) {
            Map<String, Object> errorResponse = new LinkedHashMap<>();
            errorResponse.put("status", 400);
            errorResponse.put("error", "Bad Request");
            errorResponse.put("errors", Map.of("status", "Invalid status. Valid values: " + VALID_STATUSES));
            return ResponseEntity.badRequest().body(errorResponse);
        }

        currentOrder.setStatus(newStatus.toUpperCase());
        return ResponseEntity.ok(currentOrder);
    }

    @DeleteMapping("/orders/{id}")
    public ResponseEntity<?> deleteOrder(@PathVariable("id") String id) {

        OrderDTO order = orders.stream().filter(o -> o.getId().equals(id))
                .findFirst().orElse(null);
        if (order == null) {
            return ResponseEntity.notFound().build();
        }

        orders = orders.stream().filter(o -> !o.getId().equals(id))
                .collect(Collectors.toList());

        return ResponseEntity.ok().build();
    }
}
