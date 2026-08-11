package fr.redfroggy.bdd.restapi.order;

import fr.redfroggy.bdd.restapi.error.ApiError;
import org.springframework.http.ResponseEntity;
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
import wiremock.org.apache.commons.lang3.StringUtils;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api")
public final class OrderController {

    public static final List<OrderDTO> orders = new ArrayList<>();

    private static final Map<String, Comparator<OrderDTO>> SORTS = new HashMap<>();

    static {
        SORTS.put("id", Comparator.comparing(OrderDTO::getId));
        SORTS.put("customerId", Comparator.comparing(OrderDTO::getCustomerId));
        SORTS.put("status", Comparator.comparing(OrderDTO::getStatus));
        SORTS.put("total", Comparator.comparing(OrderDTO::getTotal));
    }

    @GetMapping("/orders")
    public ResponseEntity<Object> getAll(@RequestParam(required = false) String customerId,
                                         @RequestParam(required = false) String status,
                                         @RequestParam(required = false) String sort,
                                         @RequestParam(required = false) Integer page,
                                         @RequestParam(required = false) Integer size) {
        List<OrderDTO> matching = new ArrayList<>(orders);

        if (StringUtils.isNotBlank(customerId)) {
            matching = matching.stream()
                    .filter(order -> customerId.equals(order.getCustomerId()))
                    .collect(Collectors.toList());
        }

        if (StringUtils.isNotBlank(status)) {
            Optional<OrderStatus> filteredStatus = OrderStatus.from(status);
            if (!filteredStatus.isPresent()) {
                return ResponseEntity.badRequest()
                        .body(new ApiError("status", "unknown status, expected one of " + OrderStatus.names()));
            }
            matching = matching.stream()
                    .filter(order -> filteredStatus.get() == order.getStatus())
                    .collect(Collectors.toList());
        }

        if (StringUtils.isNotBlank(sort)) {
            String[] sortParts = sort.split(",");
            Comparator<OrderDTO> comparator = SORTS.get(sortParts[0]);
            if (comparator == null) {
                return ResponseEntity.badRequest()
                        .body(new ApiError("sort", "unknown sort property " + sortParts[0]));
            }
            String direction = sortParts.length > 1 ? sortParts[1] : "asc";
            if (!"asc".equalsIgnoreCase(direction) && !"desc".equalsIgnoreCase(direction)) {
                return ResponseEntity.badRequest()
                        .body(new ApiError("sort", "unknown sort direction " + direction));
            }
            matching = matching.stream()
                    .sorted("desc".equalsIgnoreCase(direction) ? comparator.reversed() : comparator)
                    .collect(Collectors.toList());
        }

        if (page != null || size != null) {
            int pageNumber = page != null ? page : 0;
            int pageSize = size != null ? size : 20;
            if (pageNumber < 0) {
                return ResponseEntity.badRequest()
                        .body(new ApiError("page", "page cannot be negative"));
            }
            if (pageSize < 1) {
                return ResponseEntity.badRequest()
                        .body(new ApiError("size", "size cannot be lower than 1"));
            }
            matching = matching.stream()
                    .skip((long) pageNumber * pageSize)
                    .limit(pageSize)
                    .collect(Collectors.toList());
        }

        return ResponseEntity.ok(matching);
    }

    @GetMapping("/orders/{id}")
    public ResponseEntity<Object> get(@PathVariable("id") String id) {
        return findById(id)
                .<ResponseEntity<Object>>map(ResponseEntity::ok)
                .orElseGet(() -> ResponseEntity.notFound().build());
    }

    @PostMapping("/orders")
    public ResponseEntity<Object> addOrder(@RequestBody OrderDTO order) {
        Optional<ApiError> error = OrderValidator.validate(order);
        if (error.isPresent()) {
            return ResponseEntity.badRequest()
                    .body(error.get());
        }

        if (findById(order.getId()).isPresent()) {
            return ResponseEntity.status(409)
                    .body(new ApiError("id", "an order already exists with id " + order.getId()));
        }

        order.setStatus(order.getStatus() != null ? order.getStatus() : OrderStatus.CREATED);
        order.setTotal(computeTotal(order));
        orders.add(order);

        return ResponseEntity.status(201)
                .body(order);
    }

    @PutMapping("/orders/{id}")
    public ResponseEntity<Object> updateOrder(@PathVariable("id") String id, @RequestBody OrderDTO order) {
        Optional<OrderDTO> existing = findById(id);
        if (!existing.isPresent()) {
            return ResponseEntity.notFound().build();
        }

        Optional<ApiError> error = OrderValidator.validate(order);
        if (error.isPresent()) {
            return ResponseEntity.badRequest()
                    .body(error.get());
        }

        OrderDTO currentOrder = existing.get();
        if (currentOrder.getStatus() != OrderStatus.CREATED) {
            return ResponseEntity.status(409)
                    .body(new ApiError("status", "only a CREATED order can be updated"));
        }

        currentOrder.setCustomerId(order.getCustomerId());
        currentOrder.setCurrency(order.getCurrency());
        currentOrder.setItems(order.getItems());
        currentOrder.setTotal(computeTotal(currentOrder));

        return ResponseEntity.ok(currentOrder);
    }

    @PatchMapping("/orders/{id}/status")
    public ResponseEntity<Object> updateStatus(@PathVariable("id") String id,
                                               @RequestBody OrderStatusUpdateDTO statusUpdate) {
        Optional<OrderDTO> existing = findById(id);
        if (!existing.isPresent()) {
            return ResponseEntity.notFound().build();
        }

        Optional<OrderStatus> newStatus = OrderStatus.from(statusUpdate.getStatus());
        if (!newStatus.isPresent()) {
            return ResponseEntity.badRequest()
                    .body(new ApiError("status", "unknown status, expected one of " + OrderStatus.names()));
        }

        OrderDTO currentOrder = existing.get();
        if (!currentOrder.getStatus().allowedTransitions().contains(newStatus.get())) {
            return ResponseEntity.status(409)
                    .body(new ApiError("status", currentOrder.getStatus() + " cannot be changed to "
                            + newStatus.get()));
        }

        currentOrder.setStatus(newStatus.get());

        return ResponseEntity.ok(currentOrder);
    }

    @DeleteMapping("/orders/{id}")
    public ResponseEntity<Object> deleteOrder(@PathVariable("id") String id) {
        Optional<OrderDTO> existing = findById(id);
        if (!existing.isPresent()) {
            return ResponseEntity.notFound().build();
        }

        orders.remove(existing.get());

        return ResponseEntity.ok().build();
    }

    private Optional<OrderDTO> findById(String id) {
        return orders.stream()
                .filter(order -> order.getId().equals(id))
                .findFirst();
    }

    private BigDecimal computeTotal(OrderDTO order) {
        return order.getItems().stream()
                .map(item -> item.getUnitPrice().multiply(BigDecimal.valueOf(item.getQuantity())))
                .reduce(BigDecimal.ZERO, BigDecimal::add);
    }
}
