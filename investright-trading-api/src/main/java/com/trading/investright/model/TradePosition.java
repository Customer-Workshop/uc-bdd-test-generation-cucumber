package com.trading.investright.model;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.Instant;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class TradePosition {

    private String positionId;
    private String orderId;
    private String instrumentName;
    private String tradingSymbol;
    private String exchange;
    private String instrumentSegment;
    private String transactionType;
    private double entryPrice;
    private double stopLoss;
    private Double target1;
    private Double target2;
    private Double target3;
    private int totalQuantity;
    private int remainingQuantity;
    private PositionStatus status;
    private boolean target1Hit;
    private boolean target2Hit;
    private boolean target3Hit;
    private boolean stopLossHit;
    private boolean protectiveSlPlaced;
    private Double openPrice;
    private String userId;
    private Instant createdAt;
    private Instant lastCheckedAt;

    public enum PositionStatus {
        ACTIVE,
        PARTIALLY_EXITED,
        EXITED_TARGET,
        EXITED_STOPLOSS,
        CLOSED
    }

    public int getPartialQuantity() {
        if (target1 != null && target2 != null && target3 != null) {
            return Math.max(1, totalQuantity / 3);
        } else if (target1 != null && target2 != null) {
            return Math.max(1, totalQuantity / 2);
        }
        return totalQuantity;
    }
}
