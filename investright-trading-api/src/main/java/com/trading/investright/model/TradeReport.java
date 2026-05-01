package com.trading.investright.model;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class TradeReport {

    private Summary overall;
    private List<SourceSummary> bySource;
    private List<PositionDetail> positions;

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class Summary {
        private int totalTrades;
        private int activeTrades;
        private int exitedByTarget;
        private int exitedByStopLoss;
        private int closedTrades;
        private double totalCapitalDeployed;
        private double totalRealisedPnl;
    }

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class SourceSummary {
        private String source;
        private double capitalPerTrade;
        private int totalTrades;
        private int activeTrades;
        private int exitedByTarget;
        private int exitedByStopLoss;
        private double totalCapitalDeployed;
        private double totalRealisedPnl;
        private List<PositionDetail> positions;
    }

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class PositionDetail {
        private String positionId;
        private String instrumentName;
        private String tradingSymbol;
        private String exchange;
        private String transactionType;
        private String source;
        private double entryPrice;
        private double stopLoss;
        private Double target1;
        private Double target2;
        private Double target3;
        private int totalQuantity;
        private int remainingQuantity;
        private String status;
        private boolean target1Hit;
        private boolean target2Hit;
        private boolean target3Hit;
        private boolean stopLossHit;
        private Double exitPrice;
        private Double realisedPnl;
        private double capitalPerTrade;
        private String createdAt;
    }
}
