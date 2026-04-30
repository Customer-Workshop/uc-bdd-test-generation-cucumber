package com.trading.investright.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.trading.investright.model.request.OrderRequest;
import com.trading.investright.model.response.OrderResponse;
import com.trading.investright.service.OrderService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.security.test.context.support.WithMockUser;
import org.springframework.test.web.servlet.MockMvc;

import java.util.Map;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.when;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.csrf;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(OrderController.class)
class OrderControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private OrderService orderService;

    @Autowired
    private ObjectMapper objectMapper;

    @Test
    @WithMockUser
    void shouldPlaceOrder() throws Exception {
        OrderResponse response = OrderResponse.builder()
                .status("success")
                .data(OrderResponse.OrderData.builder().orderId("12345").build())
                .build();
        when(orderService.placeOrder(any(OrderRequest.class), anyString()))
                .thenReturn(response);

        OrderRequest request = OrderRequest.builder()
                .exchange("NSE")
                .securityId("RELIANCE")
                .instrumentSegment("EQUITY")
                .transactionType("BUY")
                .product("DELIVERY")
                .orderType("MARKET")
                .price(0.0)
                .quantity(1)
                .validity("DAY")
                .build();

        mockMvc.perform(post("/api/orders/place")
                        .with(csrf())
                        .param("userId", "testuser")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("success"))
                .andExpect(jsonPath("$.data.status").value("success"));
    }

    @Test
    @WithMockUser
    void shouldGetOrderStatus() throws Exception {
        when(orderService.getOrderStatus(anyString(), anyString()))
                .thenReturn(Map.of("status", "success", "order_id", "12345"));

        mockMvc.perform(get("/api/orders/status/12345")
                        .param("userId", "testuser"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("success"));
    }

    @Test
    @WithMockUser
    void shouldCancelOrder() throws Exception {
        OrderResponse response = OrderResponse.builder()
                .status("success")
                .data(OrderResponse.OrderData.builder().orderId("12345").build())
                .build();
        when(orderService.cancelOrder(anyString(), anyString()))
                .thenReturn(response);

        mockMvc.perform(delete("/api/orders/12345")
                        .with(csrf())
                        .param("userId", "testuser"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("success"));
    }
}
