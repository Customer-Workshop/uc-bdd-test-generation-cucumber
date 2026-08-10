package fr.redfroggy.bdd.restapi.order;

import fr.redfroggy.bdd.restapi.error.ApiException;
import fr.redfroggy.bdd.restapi.support.PageSupport;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.util.StringUtils;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import javax.validation.Valid;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api")
public final class OrderController {

    public static final List<OrderDTO> orders = new ArrayList<>();

    private static final Map<String, Comparator<OrderDTO>> SORTS = Map.of(
            "id", Comparator.comparing(OrderDTO::getId),
            "customerName", Comparator.comparing(OrderDTO::getCustomerName),
            "status", Comparator.comparing(OrderDTO::getStatus),
            "total", Comparator.comparing(OrderDTO::getTotal));

    @GetMapping("/orders")
    public ResponseEntity<List<OrderDTO>> getAll(@RequestParam(value = "status", required = false) String status,
                                                 @RequestParam(value = "customer", required = false) String customer,
                                                 @RequestParam(value = "sort", required = false) String sort,
                                                 @RequestParam(value = "order", required = false) String order,
                                                 @RequestParam(value = "page", required = false) Integer page,
                                                 @RequestParam(value = "size", required = false) Integer size) {

        List<OrderDTO> matching = orders;

        if (StringUtils.hasText(status)) {
            OrderStatus expectedStatus = parseStatus(status);
            matching = matching.stream()
                    .filter(o -> expectedStatus == o.getStatus())
                    .collect(Collectors.toList());
        }

        if (StringUtils.hasText(customer)) {
            matching = matching.stream()
                    .filter(o -> o.getCustomerName().toLowerCase().contains(customer.toLowerCase()))
                    .collect(Collectors.toList());
        }

        matching = PageSupport.sort(matching, sort, order, SORTS);

        int total = matching.size();

        return ResponseEntity.ok()
                .header("X-Total-Count", String.valueOf(total))
                .body(PageSupport.paginate(matching, page, size));
    }

    @GetMapping("/orders/{id}")
    public ResponseEntity<OrderDTO> get(@PathVariable("id") String id) {
        return ResponseEntity.ok(findOrFail(id));
    }

    @PostMapping("/orders")
    public ResponseEntity<OrderDTO> addOrder(@Valid @RequestBody OrderDTO order) {
        if (find(order.getId()).isPresent()) {
            throw new ApiException(HttpStatus.CONFLICT, "Order already exists with id: " + order.getId());
        }

        if (order.getStatus() == null) {
            order.setStatus(OrderStatus.PENDING);
        }

        orders.add(order);

        return ResponseEntity.status(HttpStatus.CREATED)
                .body(order);
    }

    @PutMapping("/orders/{id}")
    public ResponseEntity<OrderDTO> updateOrder(@PathVariable("id") String id, @Valid @RequestBody OrderDTO order) {
        OrderDTO currentOrder = findOrFail(id);

        if (currentOrder.getStatus() != OrderStatus.PENDING) {
            throw new ApiException(HttpStatus.CONFLICT,
                    "Only a PENDING order can be updated, current status: " + currentOrder.getStatus());
        }

        currentOrder.setCustomerName(order.getCustomerName());
        currentOrder.setCustomerEmail(order.getCustomerEmail());
        currentOrder.setItems(order.getItems());

        return ResponseEntity.ok(currentOrder);
    }

    @PatchMapping("/orders/{id}/status")
    public ResponseEntity<OrderDTO> updateStatus(@PathVariable("id") String id,
                                                 @Valid @RequestBody OrderStatusDTO statusUpdate) {
        OrderDTO currentOrder = findOrFail(id);

        if (!currentOrder.getStatus().canTransitionTo(statusUpdate.getStatus())) {
            throw new ApiException(HttpStatus.CONFLICT, "Cannot move order from " + currentOrder.getStatus()
                    + " to " + statusUpdate.getStatus());
        }

        currentOrder.setStatus(statusUpdate.getStatus());

        return ResponseEntity.ok(currentOrder);
    }

    @DeleteMapping("/orders/{id}")
    public ResponseEntity<Void> deleteOrder(@PathVariable("id") String id) {
        orders.remove(findOrFail(id));
        return ResponseEntity.noContent().build();
    }

    private OrderStatus parseStatus(String status) {
        try {
            return OrderStatus.valueOf(status.toUpperCase());
        } catch (IllegalArgumentException exception) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "Unknown order status: " + status);
        }
    }

    private Optional<OrderDTO> find(String id) {
        return orders.stream()
                .filter(o -> o.getId().equals(id))
                .findFirst();
    }

    private OrderDTO findOrFail(String id) {
        return find(id).orElseThrow(() -> new ApiException(HttpStatus.NOT_FOUND, "No order found with id: " + id));
    }
}
