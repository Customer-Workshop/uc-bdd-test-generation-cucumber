package com.trading.investright.controller;

import com.trading.investright.model.request.ModifyOrderRequest;
import com.trading.investright.model.request.OrderRequest;
import com.trading.investright.model.response.ApiResponse;
import com.trading.investright.model.response.OrderResponse;
import com.trading.investright.service.OrderService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/orders")
@RequiredArgsConstructor
@Tag(name = "Orders", description = "Order management endpoints")
public class OrderController {

    private final OrderService orderService;

    @PostMapping("/place")
    @Operation(summary = "Place order", description = "Place a single order on InvestRight")
    public ResponseEntity<ApiResponse<OrderResponse>> placeOrder(
            @Valid @RequestBody OrderRequest orderRequest,
            @RequestParam String userId) {
        OrderResponse response = orderService.placeOrder(orderRequest, userId);
        return ResponseEntity.ok(ApiResponse.success("Order placed successfully", response));
    }

    @PostMapping("/place-bulk")
    @Operation(summary = "Place bulk orders", description = "Place multiple orders at once")
    public ResponseEntity<ApiResponse<List<OrderResponse>>> placeBulkOrders(
            @Valid @RequestBody List<OrderRequest> orderRequests,
            @RequestParam String userId) {
        List<OrderResponse> responses = orderService.placeBulkOrders(orderRequests, userId);
        return ResponseEntity.ok(ApiResponse.success("Bulk orders processed", responses));
    }

    @GetMapping("/status/{orderId}")
    @Operation(summary = "Get order status", description = "Get the status of a specific order")
    public ResponseEntity<ApiResponse<Map<String, Object>>> getOrderStatus(
            @PathVariable String orderId,
            @RequestParam String userId) {
        Map<String, Object> status = orderService.getOrderStatus(orderId, userId);
        return ResponseEntity.ok(ApiResponse.success(status));
    }

    @GetMapping("/status")
    @Operation(summary = "Get all orders", description = "Get status of all orders")
    public ResponseEntity<ApiResponse<Map<String, Object>>> getAllOrders(
            @RequestParam String userId) {
        Map<String, Object> orders = orderService.getAllOrders(userId);
        return ResponseEntity.ok(ApiResponse.success(orders));
    }

    @PutMapping("/{orderId}")
    @Operation(summary = "Modify order", description = "Modify a pending order")
    public ResponseEntity<ApiResponse<OrderResponse>> modifyOrder(
            @PathVariable String orderId,
            @Valid @RequestBody ModifyOrderRequest modifyRequest,
            @RequestParam String userId) {
        OrderResponse response = orderService.modifyOrder(orderId, modifyRequest, userId);
        return ResponseEntity.ok(ApiResponse.success("Order modified successfully", response));
    }

    @DeleteMapping("/{orderId}")
    @Operation(summary = "Cancel order", description = "Cancel a pending order")
    public ResponseEntity<ApiResponse<OrderResponse>> cancelOrder(
            @PathVariable String orderId,
            @RequestParam String userId) {
        OrderResponse response = orderService.cancelOrder(orderId, userId);
        return ResponseEntity.ok(ApiResponse.success("Order cancelled successfully", response));
    }
}
