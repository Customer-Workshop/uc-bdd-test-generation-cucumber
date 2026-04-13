package fr.redfroggy.bdd.restapi.order;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import wiremock.org.apache.commons.lang3.StringUtils;

import java.util.ArrayList;
import java.util.List;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api")
public final class OrderController {

    public static List<OrderDTO> orders = new ArrayList<>();

    @GetMapping("/orders")
    public List<OrderDTO> getAll(
            @RequestParam(value = "status", required = false) String status,
            @RequestParam(value = "customerId", required = false) String customerId) {

        List<OrderDTO> result = orders;

        if (StringUtils.isNotBlank(status)) {
            result = result.stream()
                    .filter(o -> status.equalsIgnoreCase(o.getStatus()))
                    .collect(Collectors.toList());
        }

        if (StringUtils.isNotBlank(customerId)) {
            result = result.stream()
                    .filter(o -> customerId.equals(o.getCustomerId()))
                    .collect(Collectors.toList());
        }

        return result;
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

        return ResponseEntity.ok(order);
    }

    @PostMapping("/orders")
    public ResponseEntity<OrderDTO> create(@RequestBody OrderDTO order) {
        OrderDTO existing = orders.stream()
                .filter(o -> o.getId().equals(order.getId()))
                .findFirst()
                .orElse(null);

        if (existing != null) {
            return ResponseEntity.badRequest().build();
        }

        if (order.getStatus() == null || order.getStatus().isEmpty()) {
            order.setStatus("pending");
        }

        orders.add(order);
        return ResponseEntity.status(201).body(order);
    }

    @PutMapping("/orders/{id}")
    public ResponseEntity<OrderDTO> update(@RequestBody OrderDTO order, @PathVariable String id) {
        OrderDTO existing = orders.stream()
                .filter(o -> o.getId().equals(id))
                .findFirst()
                .orElse(null);

        if (existing == null) {
            return ResponseEntity.notFound().build();
        }

        orders.stream().filter(o -> id.equals(o.getId())).forEach(o -> {
            o.setProduct(order.getProduct());
            o.setQuantity(order.getQuantity());
            o.setPrice(order.getPrice());
            o.setStatus(order.getStatus());
            o.setCustomerId(order.getCustomerId());
            o.setTags(order.getTags());
        });

        return ResponseEntity.ok(order);
    }

    @PatchMapping("/orders/{id}")
    public ResponseEntity<OrderDTO> patch(@RequestBody OrderDTO order, @PathVariable String id) {
        OrderDTO existing = orders.stream()
                .filter(o -> o.getId().equals(id))
                .findFirst()
                .orElse(null);

        if (existing == null) {
            return ResponseEntity.notFound().build();
        }

        if (order.getStatus() != null) {
            existing.setStatus(order.getStatus());
        }
        if (order.getQuantity() > 0) {
            existing.setQuantity(order.getQuantity());
        }

        return ResponseEntity.ok(existing);
    }

    @DeleteMapping("/orders/{id}")
    public ResponseEntity<Void> delete(@PathVariable("id") String id) {
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
