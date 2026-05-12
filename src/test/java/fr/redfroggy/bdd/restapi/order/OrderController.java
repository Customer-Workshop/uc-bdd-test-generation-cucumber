package fr.redfroggy.bdd.restapi.order;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.FieldError;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.*;

import javax.validation.Valid;
import java.util.*;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api")
public class OrderController {

    public static List<OrderDTO> orders = new ArrayList<>();

    @GetMapping("/orders")
    public ResponseEntity<List<OrderDTO>> getAll(
            @RequestParam(value = "userId", required = false) String userId,
            @RequestParam(value = "status", required = false) String status,
            @RequestParam(value = "page", required = false) Integer page,
            @RequestParam(value = "size", required = false) Integer size,
            @RequestParam(value = "sort", required = false) String sort) {

        List<OrderDTO> result = new ArrayList<>(orders);

        if (userId != null && !userId.isBlank()) {
            result = result.stream()
                    .filter(o -> userId.equals(o.getUserId()))
                    .collect(Collectors.toList());
        }

        if (status != null && !status.isBlank()) {
            result = result.stream()
                    .filter(o -> status.equalsIgnoreCase(o.getStatus()))
                    .collect(Collectors.toList());
        }

        if (sort != null && !sort.isBlank()) {
            String[] sortParts = sort.split(",");
            String sortField = sortParts[0];
            boolean ascending = sortParts.length < 2 || "asc".equalsIgnoreCase(sortParts[1]);

            Comparator<OrderDTO> comparator;
            switch (sortField) {
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
            result.sort(comparator);
        }

        if (page != null && size != null) {
            int fromIndex = page * size;
            int toIndex = Math.min(fromIndex + size, result.size());
            if (fromIndex >= result.size()) {
                return ResponseEntity.ok(Collections.emptyList());
            }
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
    public ResponseEntity<?> create(@Valid @RequestBody OrderDTO order) {
        boolean exists = orders.stream().anyMatch(o -> o.getId().equals(order.getId()));
        if (exists) {
            Map<String, String> error = new HashMap<>();
            error.put("error", "Order with id " + order.getId() + " already exists");
            return ResponseEntity.status(HttpStatus.CONFLICT).body(error);
        }

        if (order.getStatus() == null || order.getStatus().isBlank()) {
            order.setStatus("PENDING");
        }

        orders.add(order);
        return ResponseEntity.status(HttpStatus.CREATED).body(order);
    }

    @PutMapping("/orders/{id}")
    public ResponseEntity<?> update(@PathVariable("id") String id, @Valid @RequestBody OrderDTO order) {
        OrderDTO existing = orders.stream()
                .filter(o -> o.getId().equals(id))
                .findFirst()
                .orElse(null);

        if (existing == null) {
            return ResponseEntity.notFound().build();
        }

        existing.setUserId(order.getUserId());
        existing.setProduct(order.getProduct());
        existing.setQuantity(order.getQuantity());
        existing.setPrice(order.getPrice());
        if (order.getStatus() != null) {
            existing.setStatus(order.getStatus());
        }

        return ResponseEntity.ok(existing);
    }

    @DeleteMapping("/orders/{id}")
    public ResponseEntity<Void> delete(@PathVariable("id") String id) {
        boolean removed = orders.removeIf(o -> o.getId().equals(id));
        if (!removed) {
            return ResponseEntity.notFound().build();
        }
        return ResponseEntity.ok().build();
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    @ResponseStatus(HttpStatus.BAD_REQUEST)
    public ResponseEntity<Map<String, Object>> handleValidationExceptions(MethodArgumentNotValidException ex) {
        Map<String, Object> body = new HashMap<>();
        List<Map<String, String>> errors = new ArrayList<>();
        for (FieldError fieldError : ex.getBindingResult().getFieldErrors()) {
            Map<String, String> errorMap = new HashMap<>();
            errorMap.put("field", fieldError.getField());
            errorMap.put("message", fieldError.getDefaultMessage());
            errors.add(errorMap);
        }
        body.put("errors", errors);
        return ResponseEntity.badRequest().body(body);
    }
}
