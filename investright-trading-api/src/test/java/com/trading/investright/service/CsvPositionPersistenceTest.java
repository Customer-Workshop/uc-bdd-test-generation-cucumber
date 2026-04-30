package com.trading.investright.service;

import com.trading.investright.config.SchedulerProperties;
import com.trading.investright.model.TradePosition;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.nio.file.Path;
import java.time.Instant;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

class CsvPositionPersistenceTest {

    private CsvPositionPersistence persistence;
    private SchedulerProperties schedulerProperties;

    @TempDir
    Path tempDir;

    @BeforeEach
    void setUp() {
        schedulerProperties = new SchedulerProperties();
        schedulerProperties.setLocalFolderPath(tempDir.toString());
        schedulerProperties.setTimezone("Asia/Kolkata");
        persistence = new CsvPositionPersistence(schedulerProperties);
    }

    @Test
    void shouldSaveAndLoadPositions() {
        TradePosition position = TradePosition.builder()
                .positionId("pos-001")
                .orderId("ORD001")
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
                .filledQuantity(500)
                .status(TradePosition.PositionStatus.ACTIVE)
                .target1Hit(true)
                .target2Hit(false)
                .target3Hit(false)
                .stopLossHit(false)
                .protectiveSlPlaced(true)
                .amoExecuted(true)
                .regularOrderPlaced(false)
                .openPrice(155.0)
                .activeSlOrderId("SL-001")
                .userId("testuser")
                .createdAt(Instant.parse("2026-04-30T03:00:00Z"))
                .lastCheckedAt(Instant.parse("2026-04-30T09:00:00Z"))
                .build();

        persistence.savePositions(List.of(position));

        List<TradePosition> loaded = persistence.loadPositions();

        assertEquals(1, loaded.size());
        TradePosition p = loaded.get(0);
        assertEquals("pos-001", p.getPositionId());
        assertEquals("ORD001", p.getOrderId());
        assertEquals("MAZDOCK 2760CE", p.getInstrumentName());
        assertEquals("MAZDOCK2760CE", p.getTradingSymbol());
        assertEquals("NFO", p.getExchange());
        assertEquals("OPTSTK", p.getInstrumentSegment());
        assertEquals("BUY", p.getTransactionType());
        assertEquals(153.0, p.getEntryPrice());
        assertEquals(135.0, p.getStopLoss());
        assertEquals(160.0, p.getTarget1());
        assertEquals(175.0, p.getTarget2());
        assertEquals(190.0, p.getTarget3());
        assertEquals(653, p.getTotalQuantity());
        assertEquals(653, p.getRemainingQuantity());
        assertEquals(500, p.getFilledQuantity());
        assertEquals(TradePosition.PositionStatus.ACTIVE, p.getStatus());
        assertTrue(p.isTarget1Hit());
        assertFalse(p.isTarget2Hit());
        assertTrue(p.isProtectiveSlPlaced());
        assertTrue(p.isAmoExecuted());
        assertEquals(155.0, p.getOpenPrice());
        assertEquals("SL-001", p.getActiveSlOrderId());
        assertEquals("testuser", p.getUserId());
    }

    @Test
    void shouldHandleMultiplePositions() {
        TradePosition p1 = TradePosition.builder()
                .positionId("pos-001").orderId("O1").instrumentName("A")
                .tradingSymbol("A").exchange("NSE").transactionType("BUY")
                .entryPrice(100.0).stopLoss(95.0).totalQuantity(10)
                .remainingQuantity(10).status(TradePosition.PositionStatus.ACTIVE)
                .userId("u1").build();
        TradePosition p2 = TradePosition.builder()
                .positionId("pos-002").orderId("O2").instrumentName("B")
                .tradingSymbol("B").exchange("BSE").transactionType("SELL")
                .entryPrice(200.0).stopLoss(210.0).totalQuantity(20)
                .remainingQuantity(20).status(TradePosition.PositionStatus.EXITED_STOPLOSS)
                .stopLossHit(true).userId("u1").build();

        persistence.savePositions(List.of(p1, p2));
        List<TradePosition> loaded = persistence.loadPositions();

        assertEquals(2, loaded.size());
        assertEquals("pos-001", loaded.get(0).getPositionId());
        assertEquals("pos-002", loaded.get(1).getPositionId());
        assertTrue(loaded.get(1).isStopLossHit());
    }

    @Test
    void shouldReturnEmptyListWhenNoFile() {
        List<TradePosition> loaded = persistence.loadPositions();
        assertTrue(loaded.isEmpty());
    }

    @Test
    void shouldHandleNullFields() {
        TradePosition position = TradePosition.builder()
                .positionId("pos-null")
                .orderId("O1")
                .instrumentName("TEST")
                .tradingSymbol("TEST")
                .exchange("NSE")
                .transactionType("BUY")
                .entryPrice(100.0)
                .stopLoss(95.0)
                .totalQuantity(10)
                .remainingQuantity(10)
                .status(TradePosition.PositionStatus.ACTIVE)
                .userId("u1")
                .build();

        persistence.savePositions(List.of(position));
        List<TradePosition> loaded = persistence.loadPositions();

        assertEquals(1, loaded.size());
        assertNull(loaded.get(0).getTarget1());
        assertNull(loaded.get(0).getTarget2());
        assertNull(loaded.get(0).getTarget3());
        assertNull(loaded.get(0).getOpenPrice());
        assertNull(loaded.get(0).getActiveSlOrderId());
    }

    @Test
    void shouldCreateDateFolder() {
        Path folder = persistence.getDateFolder();
        assertNotNull(folder);
        assertTrue(folder.toString().contains(tempDir.toString()));
    }
}
