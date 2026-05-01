package com.trading.investright.service;

import com.trading.investright.model.TradePosition;
import com.trading.investright.model.TradeReport;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.time.Instant;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class TradeReportServiceTest {

    @Mock
    private PositionTracker positionTracker;

    private TradeReportService reportService;

    @BeforeEach
    void setUp() {
        reportService = new TradeReportService(positionTracker);
    }

    private TradePosition telegramPosition(String name, TradePosition.PositionStatus status) {
        return TradePosition.builder()
                .positionId("pos-" + name)
                .orderId("ord-" + name)
                .instrumentName(name)
                .tradingSymbol(name)
                .exchange("NFO")
                .transactionType("BUY")
                .entryPrice(100.0)
                .stopLoss(90.0)
                .target1(120.0)
                .totalQuantity(400)
                .remainingQuantity(status == TradePosition.PositionStatus.ACTIVE ? 400 : 0)
                .status(status)
                .source("telegram")
                .capitalPerTrade(40000.0)
                .realisedPnl(status == TradePosition.PositionStatus.EXITED_TARGET ? 5000.0 : null)
                .createdAt(Instant.now())
                .build();
    }

    private TradePosition imagePosition(String name, TradePosition.PositionStatus status) {
        return TradePosition.builder()
                .positionId("pos-" + name)
                .orderId("ord-" + name)
                .instrumentName(name)
                .tradingSymbol(name)
                .exchange("NSE")
                .transactionType("BUY")
                .entryPrice(2500.0)
                .stopLoss(2400.0)
                .target1(2700.0)
                .totalQuantity(40)
                .remainingQuantity(status == TradePosition.PositionStatus.ACTIVE ? 40 : 0)
                .status(status)
                .source("image")
                .capitalPerTrade(100000.0)
                .realisedPnl(status == TradePosition.PositionStatus.EXITED_STOPLOSS ? -4000.0 : null)
                .createdAt(Instant.now())
                .build();
    }

    @Test
    void shouldGenerateReportGroupedBySource() {
        when(positionTracker.getAllPositions()).thenReturn(List.of(
                telegramPosition("NIFTY24500CE", TradePosition.PositionStatus.ACTIVE),
                telegramPosition("SENSEX76600PE", TradePosition.PositionStatus.EXITED_TARGET),
                imagePosition("RELIANCE", TradePosition.PositionStatus.ACTIVE),
                imagePosition("TCS", TradePosition.PositionStatus.EXITED_STOPLOSS)
        ));

        TradeReport report = reportService.generateReport();

        assertNotNull(report.getOverall());
        assertEquals(4, report.getOverall().getTotalTrades());
        assertEquals(2, report.getOverall().getActiveTrades());
        assertEquals(1, report.getOverall().getExitedByTarget());
        assertEquals(1, report.getOverall().getExitedByStopLoss());
        assertEquals(280000.0, report.getOverall().getTotalCapitalDeployed());
        assertEquals(1000.0, report.getOverall().getTotalRealisedPnl());

        assertEquals(2, report.getBySource().size());

        TradeReport.SourceSummary telegram = report.getBySource().stream()
                .filter(s -> "telegram".equals(s.getSource())).findFirst().orElseThrow();
        assertEquals(2, telegram.getTotalTrades());
        assertEquals(1, telegram.getActiveTrades());
        assertEquals(1, telegram.getExitedByTarget());
        assertEquals(40000.0, telegram.getCapitalPerTrade());
        assertEquals(5000.0, telegram.getTotalRealisedPnl());

        TradeReport.SourceSummary image = report.getBySource().stream()
                .filter(s -> "image".equals(s.getSource())).findFirst().orElseThrow();
        assertEquals(2, image.getTotalTrades());
        assertEquals(1, image.getActiveTrades());
        assertEquals(1, image.getExitedByStopLoss());
        assertEquals(100000.0, image.getCapitalPerTrade());
        assertEquals(-4000.0, image.getTotalRealisedPnl());
    }

    @Test
    void shouldFilterBySource() {
        when(positionTracker.getAllPositions()).thenReturn(List.of(
                telegramPosition("NIFTY24500CE", TradePosition.PositionStatus.ACTIVE),
                telegramPosition("SENSEX76600PE", TradePosition.PositionStatus.EXITED_TARGET),
                imagePosition("RELIANCE", TradePosition.PositionStatus.ACTIVE)
        ));

        TradeReport report = reportService.generateReportBySource("telegram");

        assertEquals(2, report.getOverall().getTotalTrades());
        assertEquals(1, report.getBySource().size());
        assertEquals("telegram", report.getBySource().get(0).getSource());
        assertEquals(2, report.getPositions().size());
    }

    @Test
    void shouldHandleEmptyPositions() {
        when(positionTracker.getAllPositions()).thenReturn(List.of());

        TradeReport report = reportService.generateReport();

        assertEquals(0, report.getOverall().getTotalTrades());
        assertTrue(report.getBySource().isEmpty());
        assertTrue(report.getPositions().isEmpty());
    }

    @Test
    void shouldReturnPositionDetailsInReport() {
        TradePosition pos = telegramPosition("NIFTY24500CE", TradePosition.PositionStatus.ACTIVE);
        when(positionTracker.getAllPositions()).thenReturn(List.of(pos));

        TradeReport report = reportService.generateReport();

        assertEquals(1, report.getPositions().size());
        TradeReport.PositionDetail detail = report.getPositions().get(0);
        assertEquals("NIFTY24500CE", detail.getInstrumentName());
        assertEquals("telegram", detail.getSource());
        assertEquals(40000.0, detail.getCapitalPerTrade());
        assertEquals("ACTIVE", detail.getStatus());
        assertEquals("BUY", detail.getTransactionType());
    }
}
