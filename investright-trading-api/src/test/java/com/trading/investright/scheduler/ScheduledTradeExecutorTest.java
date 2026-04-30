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
import com.trading.investright.service.LocalImageFetcher;
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
    private LocalImageFetcher localImageFetcher;

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
    void shouldSkipWhenNoLocalFolderConfigured() {
        when(schedulerProperties.isAutoLogin()).thenReturn(false);
        when(schedulerProperties.getImageSource()).thenReturn("local");
        when(schedulerProperties.getLocalFolderPath()).thenReturn(null);

        executor.executeScheduledTrades();

        verifyNoInteractions(localImageFetcher);
        verifyNoInteractions(orderService);
    }

    @Test
    void shouldReadFromLocalFolderAndPlaceOrders() {
        when(schedulerProperties.isAutoLogin()).thenReturn(false);
        when(schedulerProperties.getImageSource()).thenReturn("local");
        when(schedulerProperties.getLocalFolderPath()).thenReturn("C:\\trades");
        when(schedulerProperties.isUseDateSubfolder()).thenReturn(false);
        when(schedulerProperties.getUserId()).thenReturn("testuser");

        BufferedImage mockImage = new BufferedImage(100, 100, BufferedImage.TYPE_INT_RGB);
        when(localImageFetcher.fetchImagesFromFolder("C:\\trades")).thenReturn(List.of(mockImage));
        when(imageParserService.extractText(any(BufferedImage.class))).thenReturn("RELIANCE BUY ABOVE 2500 SL 2450");

        TradeSignal signal = TradeSignal.builder()
                .instrumentName("RELIANCE")
                .underlying("RELIANCE")
                .instrumentType(TradeSignal.InstrumentType.EQUITY)
                .transactionType("BUY")
                .entryPrice(2500.0)
                .build();
        when(tradeSignalParser.parseOcrText(anyString())).thenReturn(List.of(signal));

        OrderRequest mockOrder = OrderRequest.builder()
                .exchange("NSE").securityId("RELIANCE").transactionType("BUY").quantity(1).build();
        when(orderService.buildOrderFromSignal(any(), isNull())).thenReturn(mockOrder);

        OrderResponse response = OrderResponse.builder()
                .status("success")
                .data(OrderResponse.OrderData.builder().orderId("ORD001").build())
                .build();
        when(orderService.placeBulkOrders(anyList(), eq("testuser"))).thenReturn(List.of(response));

        executor.executeScheduledTrades();

        verify(localImageFetcher).fetchImagesFromFolder("C:\\trades");
        verify(orderService).placeBulkOrders(anyList(), eq("testuser"));
        verifyNoInteractions(cloudImageFetcher);
    }

    @Test
    void shouldUseCloudSourceWhenConfigured() {
        when(schedulerProperties.isAutoLogin()).thenReturn(true);
        when(schedulerProperties.getUsername()).thenReturn("testuser");
        when(schedulerProperties.getPassword()).thenReturn("testpass");
        when(schedulerProperties.getTwoFaAnswer()).thenReturn("123456");
        when(schedulerProperties.getRetryAttempts()).thenReturn(3);
        when(schedulerProperties.getImageSource()).thenReturn("cloud");
        when(schedulerProperties.getImageSourceUrl()).thenReturn("https://s3.example.com/trades.png");
        when(schedulerProperties.getImageSourceUrls()).thenReturn(List.of());
        when(schedulerProperties.getUserId()).thenReturn("testuser");

        AuthSession session = AuthSession.builder()
                .accessToken("test-token").loginId("login123")
                .expiresAt(Instant.now().plus(8, ChronoUnit.HOURS)).build();
        when(authClient.performFullLogin("testuser", "testpass", "123456")).thenReturn(session);

        BufferedImage mockImage = new BufferedImage(100, 100, BufferedImage.TYPE_INT_RGB);
        when(cloudImageFetcher.fetchImage("https://s3.example.com/trades.png")).thenReturn(mockImage);
        when(imageParserService.extractText(any(BufferedImage.class))).thenReturn("RELIANCE BUY ABOVE 2500 SL 2450");

        TradeSignal signal = TradeSignal.builder()
                .instrumentName("RELIANCE").underlying("RELIANCE")
                .instrumentType(TradeSignal.InstrumentType.EQUITY)
                .transactionType("BUY").entryPrice(2500.0).build();
        when(tradeSignalParser.parseOcrText(anyString())).thenReturn(List.of(signal));

        OrderRequest mockOrder = OrderRequest.builder()
                .exchange("NSE").securityId("RELIANCE").transactionType("BUY").quantity(1).build();
        when(orderService.buildOrderFromSignal(any(), isNull())).thenReturn(mockOrder);

        OrderResponse successResponse = OrderResponse.builder()
                .status("success")
                .data(OrderResponse.OrderData.builder().orderId("ORD123").build()).build();
        when(orderService.placeBulkOrders(anyList(), eq("testuser"))).thenReturn(List.of(successResponse));

        executor.executeScheduledTrades();

        verify(cloudImageFetcher).fetchImage("https://s3.example.com/trades.png");
        verifyNoInteractions(localImageFetcher);
    }

    @Test
    void shouldHandleImageFetchFailureGracefully() {
        when(schedulerProperties.isAutoLogin()).thenReturn(false);
        when(schedulerProperties.getImageSource()).thenReturn("cloud");
        when(schedulerProperties.getImageSourceUrl()).thenReturn("https://s3.example.com/bad.png");
        when(schedulerProperties.getImageSourceUrls()).thenReturn(List.of());

        when(cloudImageFetcher.fetchImage("https://s3.example.com/bad.png"))
                .thenThrow(new RuntimeException("Connection refused"));

        executor.executeScheduledTrades();

        verifyNoInteractions(orderService);
    }

    @Test
    void shouldHandleEmptyLocalFolder() {
        when(schedulerProperties.isAutoLogin()).thenReturn(false);
        when(schedulerProperties.getImageSource()).thenReturn("local");
        when(schedulerProperties.getLocalFolderPath()).thenReturn("C:\\trades");
        when(schedulerProperties.isUseDateSubfolder()).thenReturn(false);

        when(localImageFetcher.fetchImagesFromFolder("C:\\trades")).thenReturn(List.of());

        executor.executeScheduledTrades();

        verifyNoInteractions(orderService);
    }

    @Test
    void shouldUseDateSubfolderWhenEnabled() {
        when(schedulerProperties.isAutoLogin()).thenReturn(false);
        when(schedulerProperties.getImageSource()).thenReturn("local");
        when(schedulerProperties.getLocalFolderPath()).thenReturn("C:\\trades");
        when(schedulerProperties.isUseDateSubfolder()).thenReturn(true);

        when(localImageFetcher.fetchTodaysImages("C:\\trades")).thenReturn(List.of());

        executor.executeScheduledTrades();

        verify(localImageFetcher).fetchTodaysImages("C:\\trades");
        verify(localImageFetcher, never()).fetchImagesFromFolder(anyString());
    }
}
