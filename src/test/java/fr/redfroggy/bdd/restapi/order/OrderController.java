package fr.redfroggy.bdd.restapi.order;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import javax.validation.Valid;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api")
public class OrderController {

    public static List<OrderDTO> orders = new ArrayList<>();

    @PostMapping("/orders")
    public ResponseEntity<OrderDTO> create(@Valid @RequestBody OrderDTO order) {
        if (find(order.getId()) != null) {
            return ResponseEntity.status(409).build();
        }
        orders.add(order);
        return ResponseEntity.status(201).body(order);
    }

    @GetMapping("/orders")
    public ResponseEntity<List<OrderDTO>> getAll(@RequestParam(required = false) OrderStatus status,
                                                  @RequestParam(required = false) String customerId,
                                                  @RequestParam(required = false) Integer page,
                                                  @RequestParam(required = false) Integer size,
                                                  @RequestParam(required = false) String sort) {
        if ((page != null && page < 0) || (size != null && (size < 1 || size > 100))) {
            return ResponseEntity.badRequest().build();
        }
        List<OrderDTO> result = orders.stream()
                .filter(order -> status == null || order.getStatus() == status)
                .filter(order -> customerId == null || customerId.equals(order.getCustomerId()))
                .collect(Collectors.toList());
        boolean paged = page != null || size != null || sort != null;
        if (!paged) {
            return ResponseEntity.ok(result);
        }
        int currentPage = page == null ? 0 : page;
        int pageSize = size == null ? Math.max(result.size(), 1) : size;
        if (sort != null) {
            String[] parts = sort.split(",", -1);
            if (parts.length > 2 || !isSortField(parts[0])
                    || (parts.length == 2 && !"asc".equalsIgnoreCase(parts[1])
                    && !"desc".equalsIgnoreCase(parts[1]))) {
                return ResponseEntity.badRequest().build();
            }
            Comparator<OrderDTO> comparator = comparator(parts[0]);
            if (parts.length == 2 && "desc".equalsIgnoreCase(parts[1])) {
                comparator = comparator.reversed();
            }
            result.sort(comparator);
        }
        int from = currentPage * pageSize;
        int to = Math.min(from + pageSize, result.size());
        List<OrderDTO> pageResult = from >= result.size() ? new ArrayList<>() : result.subList(from, to);
        return ResponseEntity.ok().header("X-Total-Count", String.valueOf(result.size()))
                .header("X-Page", String.valueOf(currentPage)).header("X-Page-Size", String.valueOf(pageSize))
                .body(pageResult);
    }

    @GetMapping("/orders/{id}")
    public ResponseEntity<OrderDTO> get(@PathVariable String id) {
        OrderDTO order = find(id);
        return order == null ? ResponseEntity.notFound().build() : ResponseEntity.ok(order);
    }

    @PutMapping("/orders/{id}")
    public ResponseEntity<OrderDTO> update(@PathVariable String id, @Valid @RequestBody OrderDTO replacement) {
        OrderDTO current = find(id);
        if (current == null) {
            return ResponseEntity.notFound().build();
        }
        replacement.setId(id);
        if (replacement.getStatus() == null || !allowed(current.getStatus(), replacement.getStatus())) {
            return ResponseEntity.status(409).build();
        }
        orders.set(orders.indexOf(current), replacement);
        return ResponseEntity.ok(replacement);
    }

    @PatchMapping("/orders/{id}")
    public ResponseEntity<OrderDTO> patch(@PathVariable String id, @Valid @RequestBody OrderPatch patch) {
        OrderDTO current = find(id);
        if (current == null) {
            return ResponseEntity.notFound().build();
        }
        if (patch.getStatus() == null || !allowed(current.getStatus(), patch.getStatus())) {
            return ResponseEntity.status(409).build();
        }
        current.setStatus(patch.getStatus());
        return ResponseEntity.ok(current);
    }

    @DeleteMapping("/orders/{id}")
    public ResponseEntity<Void> delete(@PathVariable String id) {
        OrderDTO current = find(id);
        if (current == null) {
            return ResponseEntity.notFound().build();
        }
        orders.remove(current);
        return ResponseEntity.ok().build();
    }

    private OrderDTO find(String id) {
        return orders.stream().filter(order -> id.equals(order.getId())).findFirst().orElse(null);
    }

    private boolean allowed(OrderStatus from, OrderStatus to) {
        if (to == OrderStatus.CANCELLED) {
            return from != OrderStatus.DELIVERED && from != OrderStatus.CANCELLED;
        }
        return to.ordinal() >= from.ordinal() && from != OrderStatus.CANCELLED;
    }

    private boolean isSortField(String field) {
        return "id".equals(field) || "customerId".equals(field) || "amount".equals(field) || "status".equals(field);
    }

    private Comparator<OrderDTO> comparator(String field) {
        if ("customerId".equals(field)) return Comparator.comparing(OrderDTO::getCustomerId);
        if ("amount".equals(field)) return Comparator.comparing(OrderDTO::getAmount);
        if ("status".equals(field)) return Comparator.comparing(OrderDTO::getStatus);
        return Comparator.comparing(OrderDTO::getId);
    }

    public static class OrderPatch {
        private OrderStatus status;
        public OrderStatus getStatus() { return status; }
        public void setStatus(OrderStatus status) { this.status = status; }
    }
}
