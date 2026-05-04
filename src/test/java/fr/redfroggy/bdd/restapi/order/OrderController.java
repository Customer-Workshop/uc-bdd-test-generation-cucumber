package fr.redfroggy.bdd.restapi.order;

import fr.redfroggy.bdd.restapi.user.UserController;
import fr.redfroggy.bdd.restapi.user.UserDTO;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.ArrayList;
import java.util.List;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api")
public final class OrderController {

    public static List<OrderDTO> orders = new ArrayList<>();

    @PostMapping(value = "/orders")
    public ResponseEntity<OrderDTO> createOrder(@RequestBody OrderDTO order) {
        UserDTO user = UserController.users.stream()
                .filter(u -> u.getId().equals(order.getUserId()))
                .findFirst()
                .orElse(null);

        if (user == null) {
            return ResponseEntity.badRequest().build();
        }

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

    @GetMapping(value = "/orders")
    public List<OrderDTO> getAllOrders(@RequestParam(value = "userId", required = false) String userId) {
        if (userId != null) {
            return orders.stream()
                    .filter(o -> o.getUserId().equals(userId))
                    .collect(Collectors.toList());
        }
        return orders;
    }

    @GetMapping(value = "/orders/{id}")
    public ResponseEntity<OrderDTO> getOrder(@PathVariable("id") String id) {
        OrderDTO order = orders.stream()
                .filter(o -> o.getId().equals(id))
                .findFirst()
                .orElse(null);

        if (order == null) {
            return ResponseEntity.notFound().build();
        }
        return ResponseEntity.ok(order);
    }

    @DeleteMapping(value = "/orders/{id}")
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
}
