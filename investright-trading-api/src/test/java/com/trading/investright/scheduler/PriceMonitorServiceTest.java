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
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class PriceMonitorServiceTest {

    @Mock
    private PositionTracker positionTracker;

    @Mock
    private InvestRightMarketClient marketClient;

    @Mock
    private InvestRightAuthClient authClient;

    @Mock
    private OrderService orderService;

    @Mock
    private SchedulerProperties schedulerProperties;

    @InjectMocks
    private PriceMonitorService priceMonitorService;

    private TradePosition activePosition;

    @BeforeEach
    void setUp() {
        activePosition = TradePosition.builder()
                .positionId("pos-001")
                .orderId("ORD001")
                .instrumentName("MAZDOCK 2760CE")
                .tradingSymbol("MAZDOCK2760CE")
                .exchange("NFO")
                .transactionType("BUY")
                .entryPrice(153.0)
                .stopLoss(135.0)
                .target1(160.0)
                .target2(175.0)
                .target3(190.0)
                .totalQuantity(653)
                .remainingQuantity(653)
                .status(TradePosition.PositionStatus.ACTIVE)
                .userId("testuser")
                .createdAt(Instant.now())
                .build();
    }

    @Test
    void shouldNotCheckPricesWhenNoActivePositions() {
        when(positionTracker.getActivePositions()).thenReturn(List.of());

        List<TradePosition> positions = positionTracker.getActivePositions();
        assertTrue(positions.isEmpty());
        verifyNoInteractions(marketClient);
        verifyNoInteractions(orderService);
    }

    @Test
    void shouldSellFullPositionOnStopLoss() {
        String accessToken = "test-token";

        when(marketClient.getLastTradedPrice("MAZDOCK2760CE", "NFO", accessToken)).thenReturn(130.0);

        OrderResponse response = OrderResponse.builder()
                .status("success")
                .data(OrderResponse.OrderData.builder().orderId("SELL001").build())
                .build();
        when(orderService.placeOrder(any(OrderRequest.class), eq("testuser"))).thenReturn(response);

        priceMonitorService.checkPositionPrice(activePosition, accessToken);

        verify(orderService).placeOrder(argThat(order ->
                "SELL".equals(order.getTransactionType()) &&
                        order.getQuantity() == 653
        ), eq("testuser"));
        assertTrue(activePosition.isStopLossHit());
    }

    @Test
    void shouldTrailSlToEntryOnTarget1Hit() {
        String accessToken = "test-token";

        priceMonitorService.checkAndHandleTargets(activePosition, 162.0, accessToken);

        assertTrue(activePosition.isTarget1Hit());
        assertEquals(153.0, activePosition.getStopLoss());
        assertEquals(653, activePosition.getRemainingQuantity());
        assertEquals(TradePosition.PositionStatus.PARTIALLY_EXITED, activePosition.getStatus());
        verifyNoInteractions(orderService);
    }

    @Test
    void shouldTrailSlToTarget1OnTarget2Hit() {
        String accessToken = "test-token";

        priceMonitorService.checkAndHandleTargets(activePosition, 178.0, accessToken);

        assertTrue(activePosition.isTarget1Hit());
        assertTrue(activePosition.isTarget2Hit());
        assertEquals(160.0, activePosition.getStopLoss());
        assertEquals(653, activePosition.getRemainingQuantity());
        assertEquals(TradePosition.PositionStatus.PARTIALLY_EXITED, activePosition.getStatus());
        verifyNoInteractions(orderService);
    }

    @Test
    void shouldFullExitOnTarget3Hit() {
        String accessToken = "test-token";

        OrderResponse response = OrderResponse.builder()
                .status("success")
                .data(OrderResponse.OrderData.builder().orderId("SELL003").build())
                .build();
        when(orderService.placeOrder(any(OrderRequest.class), eq("testuser"))).thenReturn(response);

        priceMonitorService.checkAndHandleTargets(activePosition, 192.0, accessToken);

        verify(orderService).placeOrder(argThat(order ->
                "SELL".equals(order.getTransactionType()) &&
                        order.getQuantity() == 653
        ), eq("testuser"));
        assertTrue(activePosition.isTarget3Hit());
        assertTrue(activePosition.isTarget2Hit());
        assertTrue(activePosition.isTarget1Hit());
    }

    @Test
    void shouldExitAtBreakevenAfterTarget1Hit() {
        String accessToken = "test-token";

        // T1 hit → SL moves to entry (153)
        priceMonitorService.checkAndHandleTargets(activePosition, 162.0, accessToken);
        assertEquals(153.0, activePosition.getStopLoss());

        // Price drops back to entry → trailing SL hit → full exit
        when(marketClient.getLastTradedPrice("MAZDOCK2760CE", "NFO", accessToken)).thenReturn(152.0);
        OrderResponse response = OrderResponse.builder()
                .status("success")
                .data(OrderResponse.OrderData.builder().orderId("SELL_SL").build())
                .build();
        when(orderService.placeOrder(any(OrderRequest.class), eq("testuser"))).thenReturn(response);

        priceMonitorService.checkPositionPrice(activePosition, accessToken);

        verify(orderService).placeOrder(argThat(order ->
                "SELL".equals(order.getTransactionType()) &&
                        order.getQuantity() == 653
        ), eq("testuser"));
        assertTrue(activePosition.isStopLossHit());
    }

    @Test
    void shouldExitAtTarget1LevelAfterTarget2Hit() {
        String accessToken = "test-token";

        // T2 hit → SL moves to T1 (160)
        priceMonitorService.checkAndHandleTargets(activePosition, 178.0, accessToken);
        assertEquals(160.0, activePosition.getStopLoss());

        // Price drops to below T1 → trailing SL hit → full exit at T1-level profit
        when(marketClient.getLastTradedPrice("MAZDOCK2760CE", "NFO", accessToken)).thenReturn(158.0);
        OrderResponse response = OrderResponse.builder()
                .status("success")
                .data(OrderResponse.OrderData.builder().orderId("SELL_SL").build())
                .build();
        when(orderService.placeOrder(any(OrderRequest.class), eq("testuser"))).thenReturn(response);

        priceMonitorService.checkPositionPrice(activePosition, accessToken);

        verify(orderService).placeOrder(argThat(order ->
                "SELL".equals(order.getTransactionType()) &&
                        order.getQuantity() == 653
        ), eq("testuser"));
    }

    @Test
    void shouldHandleNullLtpGracefully() {
        String accessToken = "test-token";

        when(marketClient.getLastTradedPrice("MAZDOCK2760CE", "NFO", accessToken)).thenReturn(null);

        priceMonitorService.checkPositionPrice(activePosition, accessToken);

        verifyNoInteractions(orderService);
    }

    @Test
    void shouldNotReTriggerAlreadyHitTargets() {
        String accessToken = "test-token";

        activePosition.setTarget1Hit(true);
        activePosition.setStopLoss(153.0);

        priceMonitorService.checkAndHandleTargets(activePosition, 165.0, accessToken);

        verifyNoInteractions(orderService);
        assertEquals(153.0, activePosition.getStopLoss());
    }

    @Test
    void shouldProgressThroughTrailingSl() {
        String accessToken = "test-token";
        OrderResponse response = OrderResponse.builder()
                .status("success")
                .data(OrderResponse.OrderData.builder().orderId("SELL").build())
                .build();
        when(orderService.placeOrder(any(OrderRequest.class), eq("testuser"))).thenReturn(response);

        // T1 hit → SL moves to entry (153)
        priceMonitorService.checkAndHandleTargets(activePosition, 162.0, accessToken);
        assertTrue(activePosition.isTarget1Hit());
        assertFalse(activePosition.isTarget2Hit());
        assertEquals(153.0, activePosition.getStopLoss());
        assertEquals(653, activePosition.getRemainingQuantity());

        // T2 hit → SL moves to T1 (160)
        priceMonitorService.checkAndHandleTargets(activePosition, 178.0, accessToken);
        assertTrue(activePosition.isTarget2Hit());
        assertFalse(activePosition.isTarget3Hit());
        assertEquals(160.0, activePosition.getStopLoss());
        assertEquals(653, activePosition.getRemainingQuantity());

        // T3 hit → full exit with all 653 qty
        priceMonitorService.checkAndHandleTargets(activePosition, 195.0, accessToken);
        assertTrue(activePosition.isTarget3Hit());

        verify(orderService).placeOrder(argThat(order ->
                "SELL".equals(order.getTransactionType()) &&
                        order.getQuantity() == 653
        ), eq("testuser"));
    }

    @Test
    void shouldRetryAsRegularOrderWhenAmoNotExecuted() {
        activePosition.setAmoExecuted(false);
        activePosition.setRegularOrderPlaced(false);

        OrderResponse cancelResponse = OrderResponse.builder().status("success").build();
        when(orderService.cancelOrder("ORD001", "testuser")).thenReturn(cancelResponse);
        when(marketClient.getLastTradedPrice("MAZDOCK2760CE", "NFO", "test-token"))
                .thenReturn(150.0); // between SL and entry — normal entry

        OrderResponse placeResponse = OrderResponse.builder()
                .status("success")
                .data(OrderResponse.OrderData.builder().orderId("REG001").build())
                .build();
        when(orderService.placeOrder(any(OrderRequest.class), eq("testuser"))).thenReturn(placeResponse);

        priceMonitorService.retryAsRegularOrder(activePosition, "testuser", "test-token");

        verify(orderService).cancelOrder("ORD001", "testuser");
        verify(orderService).placeOrder(argThat(order ->
                "BUY".equals(order.getTransactionType()) &&
                        "SL".equals(order.getOrderType()) &&
                        order.getQuantity() == 653 &&
                        order.getTriggerPrice() == 153.0 &&
                        Boolean.FALSE.equals(order.getAmo())
        ), eq("testuser"));
        assertEquals("REG001", activePosition.getOrderId());
        assertTrue(activePosition.isRegularOrderPlaced());
        assertTrue(activePosition.isAmoExecuted());
    }

    @Test
    void shouldHandleCancelFailureAndStillPlaceRegularOrder() {
        activePosition.setAmoExecuted(false);
        activePosition.setRegularOrderPlaced(false);

        when(orderService.cancelOrder("ORD001", "testuser"))
                .thenThrow(new RuntimeException("Already cancelled"));
        when(marketClient.getLastTradedPrice("MAZDOCK2760CE", "NFO", "test-token"))
                .thenReturn(150.0);

        OrderResponse placeResponse = OrderResponse.builder()
                .status("success")
                .data(OrderResponse.OrderData.builder().orderId("REG002").build())
                .build();
        when(orderService.placeOrder(any(OrderRequest.class), eq("testuser"))).thenReturn(placeResponse);

        priceMonitorService.retryAsRegularOrder(activePosition, "testuser", "test-token");

        verify(orderService).placeOrder(any(OrderRequest.class), eq("testuser"));
        assertEquals("REG002", activePosition.getOrderId());
        assertTrue(activePosition.isRegularOrderPlaced());
    }

    @Test
    void shouldSkipRetryIfAmoAlreadyExecuted() {
        activePosition.setAmoExecuted(true);

        String accessToken = "test-token";
        when(marketClient.getLastTradedPrice("MAZDOCK2760CE", "NFO", accessToken)).thenReturn(155.0);
        when(schedulerProperties.getTimezone()).thenReturn("Asia/Kolkata");

        priceMonitorService.checkPositionPrice(activePosition, accessToken);

        verify(orderService, never()).cancelOrder(anyString(), anyString());
    }

    @Test
    void shouldSkipTradeWhenOpenPriceAtOrBelowStopLoss() {
        activePosition.setAmoExecuted(false);
        activePosition.setRegularOrderPlaced(false);

        when(orderService.cancelOrder("ORD001", "testuser")).thenReturn(
                OrderResponse.builder().status("success").build());
        when(marketClient.getLastTradedPrice("MAZDOCK2760CE", "NFO", "test-token"))
                .thenReturn(130.0); // below SL of 135

        priceMonitorService.retryAsRegularOrder(activePosition, "testuser", "test-token");

        verify(orderService).cancelOrder("ORD001", "testuser");
        verify(orderService, never()).placeOrder(any(OrderRequest.class), anyString());
        verify(positionTracker).closePosition("pos-001", TradePosition.PositionStatus.CLOSED);
    }

    @Test
    void shouldStillEnterWhenOpenPriceAboveTarget1() {
        activePosition.setAmoExecuted(false);
        activePosition.setRegularOrderPlaced(false);

        when(orderService.cancelOrder("ORD001", "testuser")).thenReturn(
                OrderResponse.builder().status("success").build());
        when(marketClient.getLastTradedPrice("MAZDOCK2760CE", "NFO", "test-token"))
                .thenReturn(165.0); // above T1 of 160

        OrderResponse placeResponse = OrderResponse.builder()
                .status("success")
                .data(OrderResponse.OrderData.builder().orderId("REG003").build())
                .build();
        when(orderService.placeOrder(any(OrderRequest.class), eq("testuser"))).thenReturn(placeResponse);

        priceMonitorService.retryAsRegularOrder(activePosition, "testuser", "test-token");

        verify(orderService).placeOrder(any(OrderRequest.class), eq("testuser"));
        assertTrue(activePosition.isRegularOrderPlaced());
        assertEquals(165.0, activePosition.getOpenPrice());
    }

    @Test
    void shouldEnterWhenOpenPriceBetweenSlAndEntry() {
        activePosition.setAmoExecuted(false);
        activePosition.setRegularOrderPlaced(false);

        when(orderService.cancelOrder("ORD001", "testuser")).thenReturn(
                OrderResponse.builder().status("success").build());
        when(marketClient.getLastTradedPrice("MAZDOCK2760CE", "NFO", "test-token"))
                .thenReturn(145.0); // between SL (135) and entry (153)

        OrderResponse placeResponse = OrderResponse.builder()
                .status("success")
                .data(OrderResponse.OrderData.builder().orderId("REG004").build())
                .build();
        when(orderService.placeOrder(any(OrderRequest.class), eq("testuser"))).thenReturn(placeResponse);

        priceMonitorService.retryAsRegularOrder(activePosition, "testuser", "test-token");

        verify(orderService).placeOrder(any(OrderRequest.class), eq("testuser"));
        assertTrue(activePosition.isRegularOrderPlaced());
    }

    @Test
    void shouldSkipTradeForSellWhenOpenPriceAboveStopLoss() {
        activePosition.setTransactionType("SELL");
        activePosition.setStopLoss(170.0);
        activePosition.setAmoExecuted(false);
        activePosition.setRegularOrderPlaced(false);

        assertTrue(priceMonitorService.shouldSkipTrade(activePosition, 175.0));
        assertFalse(priceMonitorService.shouldSkipTrade(activePosition, 160.0));
    }

    @Test
    void shouldProceedWhenOpenPriceNotAvailable() {
        activePosition.setAmoExecuted(false);
        activePosition.setRegularOrderPlaced(false);

        when(orderService.cancelOrder("ORD001", "testuser")).thenReturn(
                OrderResponse.builder().status("success").build());
        when(marketClient.getLastTradedPrice("MAZDOCK2760CE", "NFO", "test-token"))
                .thenReturn(null); // price not available

        OrderResponse placeResponse = OrderResponse.builder()
                .status("success")
                .data(OrderResponse.OrderData.builder().orderId("REG005").build())
                .build();
        when(orderService.placeOrder(any(OrderRequest.class), eq("testuser"))).thenReturn(placeResponse);

        priceMonitorService.retryAsRegularOrder(activePosition, "testuser", "test-token");

        verify(orderService).placeOrder(any(OrderRequest.class), eq("testuser"));
        assertTrue(activePosition.isRegularOrderPlaced());
    }
}
