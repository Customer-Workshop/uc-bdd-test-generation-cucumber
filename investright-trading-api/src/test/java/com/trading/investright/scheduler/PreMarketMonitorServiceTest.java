package com.trading.investright.scheduler;

import com.trading.investright.client.InvestRightAuthClient;
import com.trading.investright.config.SchedulerProperties;
import com.trading.investright.model.TradePosition;
import com.trading.investright.model.request.OrderRequest;
import com.trading.investright.model.response.OrderResponse;
import com.trading.investright.service.OrderService;
import com.trading.investright.service.PositionTracker;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.time.Instant;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class PreMarketMonitorServiceTest {

    @Mock
    private PositionTracker positionTracker;

    @Mock
    private OrderService orderService;

    @Mock
    private InvestRightAuthClient authClient;

    @Mock
    private SchedulerProperties schedulerProperties;

    @InjectMocks
    private PreMarketMonitorService preMarketMonitorService;

    private TradePosition activePosition;

    @BeforeEach
    void setUp() {
        activePosition = TradePosition.builder()
                .positionId("pos-001")
                .orderId("AMO001")
                .instrumentName("MAZDOCK 2760CE")
                .tradingSymbol("MAZDOCK2760CE")
                .exchange("NFO")
                .instrumentSegment("OPTSTK")
                .transactionType("BUY")
                .entryPrice(153.0)
                .stopLoss(135.0)
                .target1(160.0)
                .target2(175.0)
                .target3(190.0)
                .totalQuantity(653)
                .remainingQuantity(653)
                .status(TradePosition.PositionStatus.ACTIVE)
                .protectiveSlPlaced(false)
                .userId("testuser")
                .createdAt(Instant.now())
                .build();
    }

    @Test
    void shouldPlaceProtectiveSlWhenAmoOrderExecuted() {
        String accessToken = "test-token";

        Map<String, Object> orderStatus = Map.of(
                "data", Map.of("order_status", "EXECUTED")
        );
        when(orderService.getOrderStatus("AMO001", "testuser")).thenReturn(orderStatus);

        OrderResponse response = OrderResponse.builder()
                .status("success")
                .data(OrderResponse.OrderData.builder().orderId("SL001").build())
                .build();
        when(orderService.placeOrder(any(OrderRequest.class), eq("testuser"))).thenReturn(response);

        preMarketMonitorService.checkAndPlaceProtectiveSl(activePosition, "testuser", accessToken);

        verify(orderService).placeOrder(argThat(order ->
                "SELL".equals(order.getTransactionType()) &&
                        "SL".equals(order.getOrderType()) &&
                        order.getQuantity() == 653 &&
                        order.getTriggerPrice() == 135.0
        ), eq("testuser"));
        assertTrue(activePosition.isProtectiveSlPlaced());
    }

    @Test
    void shouldNotPlaceSlWhenOrderNotExecuted() {
        String accessToken = "test-token";

        Map<String, Object> orderStatus = Map.of(
                "data", Map.of("order_status", "PENDING")
        );
        when(orderService.getOrderStatus("AMO001", "testuser")).thenReturn(orderStatus);

        preMarketMonitorService.checkAndPlaceProtectiveSl(activePosition, "testuser", accessToken);

        verify(orderService, never()).placeOrder(any(OrderRequest.class), anyString());
        assertFalse(activePosition.isProtectiveSlPlaced());
    }

    @Test
    void shouldSkipIfProtectiveSlAlreadyPlaced() {
        String accessToken = "test-token";
        activePosition.setProtectiveSlPlaced(true);

        preMarketMonitorService.checkAndPlaceProtectiveSl(activePosition, "testuser", accessToken);

        verify(orderService, never()).getOrderStatus(anyString(), anyString());
        verify(orderService, never()).placeOrder(any(OrderRequest.class), anyString());
    }

    @Test
    void shouldHandleCompleteStatus() {
        String accessToken = "test-token";

        Map<String, Object> orderStatus = Map.of(
                "data", Map.of("order_status", "COMPLETE")
        );
        when(orderService.getOrderStatus("AMO001", "testuser")).thenReturn(orderStatus);

        OrderResponse response = OrderResponse.builder()
                .status("success")
                .data(OrderResponse.OrderData.builder().orderId("SL002").build())
                .build();
        when(orderService.placeOrder(any(OrderRequest.class), eq("testuser"))).thenReturn(response);

        preMarketMonitorService.checkAndPlaceProtectiveSl(activePosition, "testuser", accessToken);

        verify(orderService).placeOrder(any(OrderRequest.class), eq("testuser"));
        assertTrue(activePosition.isProtectiveSlPlaced());
    }

    @Test
    void shouldHandleNullOrderStatus() {
        String accessToken = "test-token";

        when(orderService.getOrderStatus("AMO001", "testuser")).thenReturn(null);

        preMarketMonitorService.checkAndPlaceProtectiveSl(activePosition, "testuser", accessToken);

        verify(orderService, never()).placeOrder(any(OrderRequest.class), anyString());
        assertFalse(activePosition.isProtectiveSlPlaced());
    }

    @Test
    void shouldPlaceSlWithCorrectInstrumentSegment() {
        String accessToken = "test-token";

        Map<String, Object> orderStatus = Map.of(
                "data", Map.of("order_status", "EXECUTED")
        );
        when(orderService.getOrderStatus("AMO001", "testuser")).thenReturn(orderStatus);

        OrderResponse response = OrderResponse.builder()
                .status("success")
                .data(OrderResponse.OrderData.builder().orderId("SL003").build())
                .build();
        when(orderService.placeOrder(any(OrderRequest.class), eq("testuser"))).thenReturn(response);

        preMarketMonitorService.checkAndPlaceProtectiveSl(activePosition, "testuser", accessToken);

        verify(orderService).placeOrder(argThat(order ->
                "OPTSTK".equals(order.getInstrumentSegment()) &&
                        "NFO".equals(order.getExchange())
        ), eq("testuser"));
    }
}
