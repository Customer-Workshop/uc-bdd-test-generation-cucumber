package fr.redfroggy.bdd.restapi.order;

import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.ArrayList;
import java.util.List;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api")
public final class OrderController {

    public static List<OrderDTO> orders = new ArrayList<>();

    @GetMapping("/orders")
    public List<OrderDTO> getAll() {
        return orders;
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
                .header("Content-Type", MediaType.APPLICATION_JSON_VALUE)
                .body(order);
    }

    @PostMapping("/orders")
    public ResponseEntity<OrderDTO> addOrder(@RequestBody OrderDTO order) {
        OrderDTO existing = orders.stream()
                .filter(o -> o.getId().equals(order.getId()))
                .findFirst()
                .orElse(null);
        if (existing != null) {
            return ResponseEntity.badRequest().build();
        }
        orders.add(order);
        return ResponseEntity.status(201).body(order);
    }

    @DeleteMapping("/orders/{id}")
    public ResponseEntity<Void> deleteOrder(@PathVariable("id") String id) {
        OrderDTO order = orders.stream()
                .filter(o -> o.getId().equals(id))
                .findFirst()
                .orElse(null);
        if (order == null) {
            return ResponseEntity.notFound().build();
        }
        orders = orders.stream()
                .filter(o -> !o.getId().equals(id))
                .collect(Collectors.toList());
        return ResponseEntity.ok().build();
    }

    @GetMapping("/users/{userId}/orders")
    public List<OrderDTO> getOrdersByUser(@PathVariable("userId") String userId) {
        return orders.stream()
                .filter(o -> userId.equals(o.getUserId()))
                .collect(Collectors.toList());
    }
}
