package com.trading.investright.scheduler;

import com.trading.investright.client.InvestRightAuthClient;
import com.trading.investright.config.SchedulerProperties;
import com.trading.investright.model.AuthSession;
import com.trading.investright.model.TradeSignal;
import com.trading.investright.model.request.OrderRequest;
import com.trading.investright.model.response.OrderResponse;
import com.trading.investright.ocr.ImageParserService;
import com.trading.investright.ocr.TradeSignalParser;
import com.trading.investright.service.CloudImageFetcher;
import com.trading.investright.service.OrderService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.awt.image.BufferedImage;
import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.List;

import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class ScheduledTradeExecutorTest {

    @Mock
    private SchedulerProperties schedulerProperties;

    @Mock
    private CloudImageFetcher cloudImageFetcher;

    @Mock
    private ImageParserService imageParserService;

    @Mock
    private TradeSignalParser tradeSignalParser;

    @Mock
    private OrderService orderService;

    @Mock
    private InvestRightAuthClient authClient;

    @InjectMocks
    private ScheduledTradeExecutor executor;

    @BeforeEach
    void setUp() {
        when(schedulerProperties.getTimezone()).thenReturn("Asia/Kolkata");
    }

    @Test
    void shouldSkipWhenNoImageUrlsConfigured() {
        when(schedulerProperties.isAutoLogin()).thenReturn(false);
        when(schedulerProperties.getImageSourceUrl()).thenReturn(null);
        when(schedulerProperties.getImageSourceUrls()).thenReturn(List.of());

        executor.executeScheduledTrades();

        verifyNoInteractions(cloudImageFetcher);
        verifyNoInteractions(orderService);
    }

    @Test
    void shouldPerformAutoLoginAndPlaceOrders() {
        when(schedulerProperties.isAutoLogin()).thenReturn(true);
        when(schedulerProperties.getUsername()).thenReturn("testuser");
        when(schedulerProperties.getPassword()).thenReturn("testpass");
        when(schedulerProperties.getTwoFaAnswer()).thenReturn("123456");
        when(schedulerProperties.getRetryAttempts()).thenReturn(3);
        when(schedulerProperties.getImageSourceUrl()).thenReturn("https://s3.example.com/trades.png");
        when(schedulerProperties.getImageSourceUrls()).thenReturn(List.of());
        when(schedulerProperties.getUserId()).thenReturn("testuser");

        AuthSession session = AuthSession.builder()
                .accessToken("test-token")
                .loginId("login123")
                .expiresAt(Instant.now().plus(8, ChronoUnit.HOURS))
                .build();
        when(authClient.performFullLogin("testuser", "testpass", "123456")).thenReturn(session);

        BufferedImage mockImage = new BufferedImage(100, 100, BufferedImage.TYPE_INT_RGB);
        when(cloudImageFetcher.fetchImage("https://s3.example.com/trades.png")).thenReturn(mockImage);
        when(imageParserService.extractText(any(BufferedImage.class))).thenReturn("RELIANCE BUY ABOVE 2500 SL 2450");

        TradeSignal signal = TradeSignal.builder()
                .instrumentName("RELIANCE")
                .underlying("RELIANCE")
                .instrumentType(TradeSignal.InstrumentType.EQUITY)
                .transactionType("BUY")
                .entryPrice(2500.0)
                .stopLoss(2450.0)
                .build();
        when(tradeSignalParser.parseOcrText(anyString())).thenReturn(List.of(signal));

        OrderRequest mockOrder = OrderRequest.builder()
                .exchange("NSE")
                .securityId("RELIANCE")
                .transactionType("BUY")
                .quantity(1)
                .build();
        when(orderService.buildOrderFromSignal(any(TradeSignal.class), isNull())).thenReturn(mockOrder);

        OrderResponse successResponse = OrderResponse.builder()
                .status("success")
                .data(OrderResponse.OrderData.builder().orderId("ORD123").build())
                .build();
        when(orderService.placeBulkOrders(anyList(), eq("testuser"))).thenReturn(List.of(successResponse));

        executor.executeScheduledTrades();

        verify(authClient).performFullLogin("testuser", "testpass", "123456");
        verify(cloudImageFetcher).fetchImage("https://s3.example.com/trades.png");
        verify(orderService).placeBulkOrders(anyList(), eq("testuser"));
    }

    @Test
    void shouldHandleImageFetchFailureGracefully() {
        when(schedulerProperties.isAutoLogin()).thenReturn(false);
        when(schedulerProperties.getImageSourceUrl()).thenReturn("https://s3.example.com/bad.png");
        when(schedulerProperties.getImageSourceUrls()).thenReturn(List.of());

        when(cloudImageFetcher.fetchImage("https://s3.example.com/bad.png"))
                .thenThrow(new RuntimeException("Connection refused"));

        executor.executeScheduledTrades();

        verifyNoInteractions(orderService);
    }

    @Test
    void shouldProcessMultipleImageUrls() {
        when(schedulerProperties.isAutoLogin()).thenReturn(false);
        when(schedulerProperties.getImageSourceUrl()).thenReturn("https://s3.example.com/img1.png");
        when(schedulerProperties.getImageSourceUrls()).thenReturn(List.of("https://s3.example.com/img2.png"));
        when(schedulerProperties.getUserId()).thenReturn("testuser");

        BufferedImage mockImage = new BufferedImage(100, 100, BufferedImage.TYPE_INT_RGB);
        when(cloudImageFetcher.fetchImage(anyString())).thenReturn(mockImage);
        when(imageParserService.extractText(any(BufferedImage.class))).thenReturn("INFY BUY ABOVE 1500 SL 1470");

        TradeSignal signal = TradeSignal.builder()
                .instrumentName("INFY")
                .underlying("INFY")
                .instrumentType(TradeSignal.InstrumentType.EQUITY)
                .transactionType("BUY")
                .entryPrice(1500.0)
                .build();
        when(tradeSignalParser.parseOcrText(anyString())).thenReturn(List.of(signal));

        OrderRequest mockOrder = OrderRequest.builder()
                .exchange("NSE")
                .securityId("INFY")
                .transactionType("BUY")
                .quantity(1)
                .build();
        when(orderService.buildOrderFromSignal(any(TradeSignal.class), isNull())).thenReturn(mockOrder);

        OrderResponse successResponse = OrderResponse.builder()
                .status("success")
                .data(OrderResponse.OrderData.builder().orderId("ORD456").build())
                .build();
        when(orderService.placeBulkOrders(anyList(), eq("testuser"))).thenReturn(List.of(successResponse));

        executor.executeScheduledTrades();

        verify(cloudImageFetcher, times(2)).fetchImage(anyString());
        verify(orderService).placeBulkOrders(anyList(), eq("testuser"));
    }
}
