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
}
