package com.trading.investright.scheduler;

import com.trading.investright.client.InvestRightAuthClient;
import com.trading.investright.client.InvestRightMarketClient;
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
    private InvestRightMarketClient marketClient;

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

    @Test
    void shouldFetchAndLogOpenPrice() {
        String accessToken = "test-token";

        when(marketClient.getLastTradedPrice("MAZDOCK2760CE", "NFO", accessToken))
                .thenReturn(160.0);

        preMarketMonitorService.fetchAndLogOpenPrice(activePosition, accessToken);

        assertEquals(160.0, activePosition.getOpenPrice());
        verify(positionTracker).updatePosition(activePosition);
    }

    @Test
    void shouldSkipOpenPriceFetchIfAlreadySet() {
        String accessToken = "test-token";
        activePosition.setOpenPrice(155.0);

        preMarketMonitorService.fetchAndLogOpenPrice(activePosition, accessToken);

        verify(marketClient, never()).getLastTradedPrice(anyString(), anyString(), anyString());
    }

    @Test
    void shouldHandleNullLtpGracefully() {
        String accessToken = "test-token";

        when(marketClient.getLastTradedPrice("MAZDOCK2760CE", "NFO", accessToken))
                .thenReturn(null);

        preMarketMonitorService.fetchAndLogOpenPrice(activePosition, accessToken);

        assertNull(activePosition.getOpenPrice());
        verify(positionTracker, never()).updatePosition(activePosition);
    }

    @Test
    void shouldLogBelowStopLossWarning() {
        String accessToken = "test-token";

        when(marketClient.getLastTradedPrice("MAZDOCK2760CE", "NFO", accessToken))
                .thenReturn(130.0);

        preMarketMonitorService.fetchAndLogOpenPrice(activePosition, accessToken);

        assertEquals(130.0, activePosition.getOpenPrice());
        verify(positionTracker).updatePosition(activePosition);
    }

    @Test
    void shouldUpdateFilledQuantityFromOrderStatus() {
        String accessToken = "test-token";

        Map<String, Object> orderStatus = Map.of(
                "data", Map.of("order_status", "EXECUTED", "filled_quantity", 500)
        );
        when(orderService.getOrderStatus("AMO001", "testuser")).thenReturn(orderStatus);

        OrderResponse response = OrderResponse.builder()
                .status("success")
                .data(OrderResponse.OrderData.builder().orderId("SL-PARTIAL").build())
                .build();
        when(orderService.placeOrder(any(OrderRequest.class), eq("testuser"))).thenReturn(response);

        preMarketMonitorService.checkAndPlaceProtectiveSl(activePosition, "testuser", accessToken);

        assertEquals(500, activePosition.getFilledQuantity());
        assertEquals(500, activePosition.getRemainingQuantity());
        verify(orderService).placeOrder(argThat(order ->
                order.getQuantity() == 500
        ), eq("testuser"));
    }

    @Test
    void shouldHandlePartiallyExecutedAmoOrder() {
        String accessToken = "test-token";

        Map<String, Object> orderStatus = Map.of(
                "data", Map.of("order_status", "PARTIALLY_EXECUTED", "filled_quantity", 300)
        );
        when(orderService.getOrderStatus("AMO001", "testuser")).thenReturn(orderStatus);

        OrderResponse response = OrderResponse.builder()
                .status("success")
                .data(OrderResponse.OrderData.builder().orderId("SL-PARTIAL-300").build())
                .build();
        when(orderService.placeOrder(any(OrderRequest.class), eq("testuser"))).thenReturn(response);

        preMarketMonitorService.checkAndPlaceProtectiveSl(activePosition, "testuser", accessToken);

        assertEquals(300, activePosition.getFilledQuantity());
        assertEquals(300, activePosition.getRemainingQuantity());
        assertTrue(activePosition.isProtectiveSlPlaced());
        verify(orderService).placeOrder(argThat(order ->
                order.getQuantity() == 300
        ), eq("testuser"));
    }

    @Test
    void shouldExtractFilledQuantityFromVariousFieldNames() {
        Map<String, Object> withFilledQty = Map.of("filled_quantity", 100);
        assertEquals(100, preMarketMonitorService.extractFilledQuantity(withFilledQty));

        Map<String, Object> withTradedQty = Map.of("traded_quantity", 200);
        assertEquals(200, preMarketMonitorService.extractFilledQuantity(withTradedQty));

        Map<String, Object> withStringQty = Map.of("filled_quantity", "350");
        assertEquals(350, preMarketMonitorService.extractFilledQuantity(withStringQty));

        Map<String, Object> withNoQty = Map.of("order_status", "PENDING");
        assertEquals(0, preMarketMonitorService.extractFilledQuantity(withNoQty));
    }
}
