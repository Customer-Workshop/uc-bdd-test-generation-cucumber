package com.trading.investright.scheduler;

import com.trading.investright.config.SchedulerProperties;
import com.trading.investright.model.TradePosition;
import com.trading.investright.service.CsvPositionPersistence;
import com.trading.investright.service.PositionTracker;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.junit.jupiter.api.io.TempDir;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class DailyReportServiceTest {

    @Mock
    private PositionTracker positionTracker;

    @Mock
    private CsvPositionPersistence csvPersistence;

    @Mock
    private SchedulerProperties schedulerProperties;

    private DailyReportService reportService;

    @TempDir
    Path tempDir;

    @BeforeEach
    void setUp() {
        reportService = new DailyReportService(positionTracker, csvPersistence, schedulerProperties);
    }

    @Test
    void shouldGenerateReportWithTradeData() throws IOException {
        TradePosition winTrade = TradePosition.builder()
                .positionId("pos-001").instrumentName("MAZDOCK 2760CE")
                .transactionType("BUY").entryPrice(153.0).stopLoss(135.0)
                .target1(160.0).target2(175.0).target3(190.0)
                .totalQuantity(653).remainingQuantity(0).filledQuantity(653)
                .status(TradePosition.PositionStatus.EXITED_TARGET)
                .target1Hit(true).target2Hit(true).target3Hit(true)
                .userId("u1").createdAt(Instant.now())
                .build();

        TradePosition lossTrade = TradePosition.builder()
                .positionId("pos-002").instrumentName("RECLTD 370PE")
                .transactionType("BUY").entryPrice(18.75).stopLoss(17.25)
                .target1(19.75).target2(21.0).target3(23.0)
                .totalQuantity(5333).remainingQuantity(0).filledQuantity(5333)
                .status(TradePosition.PositionStatus.EXITED_STOPLOSS)
                .stopLossHit(true)
                .userId("u1").createdAt(Instant.now())
                .build();

        Path reportFile = tempDir.resolve("report.txt");
        when(schedulerProperties.getTimezone()).thenReturn("Asia/Kolkata");

        reportService.writeReport(List.of(winTrade, lossTrade), reportFile);

        assertTrue(Files.exists(reportFile));
        String content = Files.readString(reportFile);
        assertTrue(content.contains("DAILY TRADE REPORT"));
        assertTrue(content.contains("MAZDOCK 2760CE"));
        assertTrue(content.contains("RECLTD 370PE"));
        assertTrue(content.contains("TOTAL TRADES:     2"));
        assertTrue(content.contains("WINS:             1"));
        assertTrue(content.contains("LOSSES:           1"));
        assertTrue(content.contains("WIN RATE:         50.0%"));
        assertTrue(content.contains("T1:HIT"));
        assertTrue(content.contains("[SL HIT]"));
    }

    @Test
    void shouldSkipReportWhenNoTrades() {
        when(positionTracker.getAllPositions()).thenReturn(List.of());

        reportService.generateDailyReport();

        verify(csvPersistence, never()).getDateFolder();
    }

    @Test
    void shouldCalculateCorrectPnlForWinningTrade() throws IOException {
        TradePosition trade = TradePosition.builder()
                .positionId("p1").instrumentName("TEST")
                .transactionType("BUY").entryPrice(100.0).stopLoss(90.0)
                .target1(110.0).target2(120.0).target3(130.0)
                .totalQuantity(100).remainingQuantity(0).filledQuantity(100)
                .status(TradePosition.PositionStatus.EXITED_TARGET)
                .target1Hit(true).target2Hit(true).target3Hit(true)
                .userId("u1").build();

        Path reportFile = tempDir.resolve("pnl-report.txt");
        when(schedulerProperties.getTimezone()).thenReturn("Asia/Kolkata");

        reportService.writeReport(List.of(trade), reportFile);

        String content = Files.readString(reportFile);
        assertTrue(content.contains("TOTAL P&L"));
        assertTrue(content.contains("ROI"));
    }
}
