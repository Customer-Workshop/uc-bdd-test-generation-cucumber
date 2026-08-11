package fr.redfroggy.bdd.restapi.order;

import fr.redfroggy.bdd.restapi.support.ApiError;
import fr.redfroggy.bdd.restapi.support.Page;
import fr.redfroggy.bdd.restapi.support.Sorting;
import org.springframework.http.HttpStatus;
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

import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

/**
 * In memory orders api used by the orders gherkin features.
 */
@RestController
@RequestMapping("/api/orders")
public final class OrderController {

    public static final List<OrderDTO> orders = new ArrayList<>();

    private static final Map<String, Comparator<OrderDTO>> SORTS = new LinkedHashMap<>();

    static {
        SORTS.put("id", Comparator.comparing(OrderDTO::getId));
        SORTS.put("customerId", Comparator.comparing(OrderDTO::getCustomerId));
        SORTS.put("product", Comparator.comparing(OrderDTO::getProduct));
        SORTS.put("quantity", Comparator.comparingInt(OrderDTO::getQuantity));
        SORTS.put("unitPrice", Comparator.comparingDouble(OrderDTO::getUnitPrice));
        SORTS.put("total", Comparator.comparingDouble(OrderDTO::getTotal));
        SORTS.put("status", Comparator.comparing(OrderDTO::getStatus));
    }

    @GetMapping
    public ResponseEntity<Object> getAll(@RequestParam(value = "customerId", required = false) String customerId,
                                         @RequestParam(value = "status", required = false) String status,
                                         @RequestParam(value = "page", required = false) Integer page,
                                         @RequestParam(value = "size", required = false) Integer size,
                                         @RequestParam(value = "sort", required = false) String sort) {

        ApiError pageError = Page.validate(page, size);
        if (pageError != null) {
            return ResponseEntity.badRequest().body(pageError);
        }

        if (StringUtils.isNotBlank(status) && OrderStatus.from(status) == null) {
            return ResponseEntity.badRequest()
                    .body(new ApiError(OrderValidator.unknownStatusMessage(status), "status"));
        }

        List<OrderDTO> matching = orders.stream()
                .filter(order -> StringUtils.isBlank(customerId) || customerId.equals(order.getCustomerId()))
                .filter(order -> StringUtils.isBlank(status) || status.equalsIgnoreCase(order.getStatus()))
                .collect(Collectors.toList());

        ApiError sortError = Sorting.sort(matching, sort, SORTS);
        if (sortError != null) {
            return ResponseEntity.badRequest().body(sortError);
        }

        if (page == null && size == null) {
            return ResponseEntity.ok(matching);
        }

        return Page.of(matching, page, size);
    }

    @GetMapping("/{id}")
    public ResponseEntity<Object> get(@PathVariable("id") String id) {
        OrderDTO order = findById(id);
        if (order == null) {
            return ResponseEntity.notFound().build();
        }
        return ResponseEntity.ok(order);
    }

    @PostMapping
    public ResponseEntity<Object> create(@RequestBody OrderDTO order) {
        ApiError error = OrderValidator.validate(order);
        if (error != null) {
            return ResponseEntity.badRequest().body(error);
        }

        if (findById(order.getId()) != null) {
            return ResponseEntity.status(HttpStatus.CONFLICT)
                    .body(new ApiError("an order with id " + order.getId() + " already exists", "id"));
        }

        order.setStatus(StringUtils.isBlank(order.getStatus()) ? OrderStatus.PENDING.name()
                : OrderStatus.from(order.getStatus()).name());
        orders.add(order);

        return ResponseEntity.status(HttpStatus.CREATED).body(order);
    }

    @PutMapping("/{id}")
    public ResponseEntity<Object> update(@PathVariable("id") String id, @RequestBody OrderDTO order) {
        OrderDTO currentOrder = findById(id);
        if (currentOrder == null) {
            return ResponseEntity.notFound().build();
        }

        ApiError error = OrderValidator.validate(order);
        if (error != null) {
            return ResponseEntity.badRequest().body(error);
        }

        currentOrder.setCustomerId(order.getCustomerId());
        currentOrder.setProduct(order.getProduct());
        currentOrder.setQuantity(order.getQuantity());
        currentOrder.setUnitPrice(order.getUnitPrice());

        return ResponseEntity.ok(currentOrder);
    }

    @PatchMapping("/{id}/status")
    public ResponseEntity<Object> updateStatus(@PathVariable("id") String id,
                                               @RequestBody OrderStatusUpdateDTO statusUpdate) {
        OrderDTO currentOrder = findById(id);
        if (currentOrder == null) {
            return ResponseEntity.notFound().build();
        }

        OrderStatus newStatus = OrderStatus.from(statusUpdate.getStatus());
        if (newStatus == null) {
            return ResponseEntity.badRequest()
                    .body(new ApiError(OrderValidator.unknownStatusMessage(statusUpdate.getStatus()), "status"));
        }

        OrderStatus currentStatus = OrderStatus.from(currentOrder.getStatus());
        if (!currentStatus.allowedTransitions().contains(newStatus)) {
            return ResponseEntity.status(HttpStatus.CONFLICT)
                    .body(new ApiError("cannot move order from " + currentStatus + " to " + newStatus, "status"));
        }

        currentOrder.setStatus(newStatus.name());
        return ResponseEntity.ok(currentOrder);
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Object> delete(@PathVariable("id") String id) {
        OrderDTO currentOrder = findById(id);
        if (currentOrder == null) {
            return ResponseEntity.notFound().build();
        }

        OrderStatus currentStatus = OrderStatus.from(currentOrder.getStatus());
        if (currentStatus == OrderStatus.SHIPPED || currentStatus == OrderStatus.DELIVERED) {
            return ResponseEntity.status(HttpStatus.CONFLICT)
                    .body(new ApiError("a " + currentStatus + " order cannot be deleted", "status"));
        }

        orders.remove(currentOrder);
        return ResponseEntity.ok().build();
    }

    private OrderDTO findById(String id) {
        return orders.stream()
                .filter(order -> order.getId().equals(id))
                .findFirst()
                .orElse(null);
    }
}
