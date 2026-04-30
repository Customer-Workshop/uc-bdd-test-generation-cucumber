package com.trading.investright.service;

import com.trading.investright.model.TradePosition;
import com.trading.investright.model.TradeSignal;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

class PositionTrackerTest {

    private PositionTracker tracker;

    @BeforeEach
    void setUp() {
        tracker = new PositionTracker();
    }

    @Test
    void shouldRegisterAndRetrievePosition() {
        TradeSignal signal = TradeSignal.builder()
                .instrumentName("RELIANCE")
                .tradingSymbol("RELIANCE")
                .exchange("NSE")
                .transactionType("BUY")
                .entryPrice(2500.0)
                .stopLoss(2450.0)
                .target1(2550.0)
                .target2(2600.0)
                .target3(2700.0)
                .build();

        TradePosition position = tracker.registerPosition(signal, "ORD001", 40, "user1");

        assertNotNull(position.getPositionId());
        assertEquals("ORD001", position.getOrderId());
        assertEquals("RELIANCE", position.getInstrumentName());
        assertEquals(40, position.getTotalQuantity());
        assertEquals(40, position.getRemainingQuantity());
        assertEquals(TradePosition.PositionStatus.ACTIVE, position.getStatus());
    }

    @Test
    void shouldReturnOnlyActivePositions() {
        TradeSignal signal1 = createSignal("RELIANCE", 2500.0);
        TradeSignal signal2 = createSignal("TCS", 3800.0);

        TradePosition pos1 = tracker.registerPosition(signal1, "ORD001", 40, "user1");
        tracker.registerPosition(signal2, "ORD002", 26, "user1");

        tracker.closePosition(pos1.getPositionId(), TradePosition.PositionStatus.EXITED_STOPLOSS);

        List<TradePosition> active = tracker.getActivePositions();
        assertEquals(1, active.size());
        assertEquals("TCS", active.get(0).getInstrumentName());
    }

    @Test
    void shouldTrackPartiallyExitedPositions() {
        TradeSignal signal = createSignal("RELIANCE", 2500.0);
        TradePosition position = tracker.registerPosition(signal, "ORD001", 40, "user1");

        position.setStatus(TradePosition.PositionStatus.PARTIALLY_EXITED);
        position.setRemainingQuantity(27);
        position.setTarget1Hit(true);
        tracker.updatePosition(position);

        List<TradePosition> active = tracker.getActivePositions();
        assertEquals(1, active.size());
        assertEquals(27, active.get(0).getRemainingQuantity());
        assertTrue(active.get(0).isTarget1Hit());
    }

    @Test
    void shouldCalculatePartialQuantityForThreeTargets() {
        TradePosition position = TradePosition.builder()
                .totalQuantity(60)
                .target1(100.0)
                .target2(110.0)
                .target3(120.0)
                .build();

        assertEquals(20, position.getPartialQuantity());
    }

    @Test
    void shouldCalculatePartialQuantityForTwoTargets() {
        TradePosition position = TradePosition.builder()
                .totalQuantity(60)
                .target1(100.0)
                .target2(110.0)
                .build();

        assertEquals(30, position.getPartialQuantity());
    }

    @Test
    void shouldReturnActivePositionCount() {
        tracker.registerPosition(createSignal("A", 100.0), "O1", 10, "u1");
        tracker.registerPosition(createSignal("B", 200.0), "O2", 20, "u1");
        tracker.registerPosition(createSignal("C", 300.0), "O3", 30, "u1");

        assertEquals(3, tracker.getActivePositionCount());

        TradePosition pos = tracker.getActivePositions().get(0);
        tracker.closePosition(pos.getPositionId(), TradePosition.PositionStatus.EXITED_TARGET);

        assertEquals(2, tracker.getActivePositionCount());
    }

    @Test
    void shouldClearAllPositions() {
        tracker.registerPosition(createSignal("A", 100.0), "O1", 10, "u1");
        tracker.registerPosition(createSignal("B", 200.0), "O2", 20, "u1");

        tracker.clearAll();

        assertEquals(0, tracker.getActivePositionCount());
        assertTrue(tracker.getAllPositions().isEmpty());
    }

    private TradeSignal createSignal(String name, double price) {
        return TradeSignal.builder()
                .instrumentName(name)
                .tradingSymbol(name)
                .exchange("NSE")
                .transactionType("BUY")
                .entryPrice(price)
                .stopLoss(price * 0.95)
                .target1(price * 1.05)
                .target2(price * 1.10)
                .target3(price * 1.15)
                .build();
    }
}
