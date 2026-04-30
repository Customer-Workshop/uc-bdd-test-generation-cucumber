package com.trading.investright.service;

import com.trading.investright.model.TradePosition;
import com.trading.investright.model.TradeSignal;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;

@Slf4j
@Service
public class PositionTracker {

    private final Map<String, TradePosition> activePositions = new ConcurrentHashMap<>();

    public TradePosition registerPosition(TradeSignal signal, String orderId, int quantity, String userId) {
        TradePosition position = TradePosition.builder()
                .positionId(UUID.randomUUID().toString())
                .orderId(orderId)
                .instrumentName(signal.getInstrumentName())
                .tradingSymbol(signal.getTradingSymbol() != null ? signal.getTradingSymbol() : signal.getInstrumentName())
                .exchange(signal.getExchange() != null ? signal.getExchange() : "NSE")
                .transactionType(signal.getTransactionType())
                .entryPrice(signal.getEntryPrice())
                .stopLoss(signal.getStopLoss() != null ? signal.getStopLoss() : 0.0)
                .target1(signal.getTarget1())
                .target2(signal.getTarget2())
                .target3(signal.getTarget3())
                .totalQuantity(quantity)
                .remainingQuantity(quantity)
                .status(TradePosition.PositionStatus.ACTIVE)
                .userId(userId)
                .createdAt(Instant.now())
                .build();

        activePositions.put(position.getPositionId(), position);
        log.info("Registered position {} for {} qty={} entry={} SL={} T1={} T2={} T3={}",
                position.getPositionId(), signal.getInstrumentName(), quantity,
                signal.getEntryPrice(), signal.getStopLoss(),
                signal.getTarget1(), signal.getTarget2(), signal.getTarget3());
        return position;
    }

    public List<TradePosition> getActivePositions() {
        return activePositions.values().stream()
                .filter(p -> p.getStatus() == TradePosition.PositionStatus.ACTIVE
                        || p.getStatus() == TradePosition.PositionStatus.PARTIALLY_EXITED)
                .toList();
    }

    public List<TradePosition> getAllPositions() {
        return new ArrayList<>(activePositions.values());
    }

    public TradePosition getPosition(String positionId) {
        return activePositions.get(positionId);
    }

    public void updatePosition(TradePosition position) {
        activePositions.put(position.getPositionId(), position);
    }

    public void closePosition(String positionId, TradePosition.PositionStatus status) {
        TradePosition position = activePositions.get(positionId);
        if (position != null) {
            position.setStatus(status);
            position.setRemainingQuantity(0);
            log.info("Closed position {} with status {}", positionId, status);
        }
    }

    public int getActivePositionCount() {
        return (int) activePositions.values().stream()
                .filter(p -> p.getStatus() == TradePosition.PositionStatus.ACTIVE
                        || p.getStatus() == TradePosition.PositionStatus.PARTIALLY_EXITED)
                .count();
    }

    public void clearAll() {
        activePositions.clear();
    }
}
