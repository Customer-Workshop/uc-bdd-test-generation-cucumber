package com.trading.investright.service;

import com.trading.investright.model.TradePosition;
import com.trading.investright.model.TradeReport;
import com.trading.investright.model.TradeReport.PositionDetail;
import com.trading.investright.model.TradeReport.SourceSummary;
import com.trading.investright.model.TradeReport.Summary;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@Service
@RequiredArgsConstructor
public class TradeReportService {

    private final PositionTracker positionTracker;

    public TradeReport generateReport() {
        List<TradePosition> allPositions = positionTracker.getAllPositions();
        List<PositionDetail> allDetails = allPositions.stream().map(this::toDetail).toList();

        Map<String, List<TradePosition>> bySource = new LinkedHashMap<>();
        for (TradePosition p : allPositions) {
            String source = p.getSource() != null ? p.getSource() : "unknown";
            bySource.computeIfAbsent(source, k -> new ArrayList<>()).add(p);
        }

        List<SourceSummary> sourceSummaries = bySource.entrySet().stream()
                .map(entry -> buildSourceSummary(entry.getKey(), entry.getValue()))
                .toList();

        return TradeReport.builder()
                .overall(buildOverallSummary(allPositions))
                .bySource(sourceSummaries)
                .positions(allDetails)
                .build();
    }

    public TradeReport generateReportBySource(String source) {
        List<TradePosition> allPositions = positionTracker.getAllPositions();
        List<TradePosition> filtered = allPositions.stream()
                .filter(p -> source.equalsIgnoreCase(p.getSource()))
                .toList();

        List<PositionDetail> details = filtered.stream().map(this::toDetail).toList();
        SourceSummary sourceSummary = buildSourceSummary(source, filtered);

        return TradeReport.builder()
                .overall(buildOverallSummary(filtered))
                .bySource(List.of(sourceSummary))
                .positions(details)
                .build();
    }

    private Summary buildOverallSummary(List<TradePosition> positions) {
        int active = 0, exitTarget = 0, exitSl = 0, closed = 0;
        double totalCapital = 0, totalPnl = 0;

        for (TradePosition p : positions) {
            totalCapital += p.getCapitalPerTrade();
            if (p.getRealisedPnl() != null) totalPnl += p.getRealisedPnl();

            switch (p.getStatus()) {
                case ACTIVE, PARTIALLY_EXITED -> active++;
                case EXITED_TARGET -> exitTarget++;
                case EXITED_STOPLOSS -> exitSl++;
                case CLOSED -> closed++;
            }
        }

        return Summary.builder()
                .totalTrades(positions.size())
                .activeTrades(active)
                .exitedByTarget(exitTarget)
                .exitedByStopLoss(exitSl)
                .closedTrades(closed)
                .totalCapitalDeployed(totalCapital)
                .totalRealisedPnl(totalPnl)
                .build();
    }

    private SourceSummary buildSourceSummary(String source, List<TradePosition> positions) {
        Summary summary = buildOverallSummary(positions);
        double capitalPerTrade = positions.isEmpty() ? 0 :
                positions.stream().mapToDouble(TradePosition::getCapitalPerTrade).max().orElse(0);

        return SourceSummary.builder()
                .source(source)
                .capitalPerTrade(capitalPerTrade)
                .totalTrades(summary.getTotalTrades())
                .activeTrades(summary.getActiveTrades())
                .exitedByTarget(summary.getExitedByTarget())
                .exitedByStopLoss(summary.getExitedByStopLoss())
                .totalCapitalDeployed(summary.getTotalCapitalDeployed())
                .totalRealisedPnl(summary.getTotalRealisedPnl())
                .positions(positions.stream().map(this::toDetail).toList())
                .build();
    }

    private PositionDetail toDetail(TradePosition p) {
        return PositionDetail.builder()
                .positionId(p.getPositionId())
                .instrumentName(p.getInstrumentName())
                .tradingSymbol(p.getTradingSymbol())
                .exchange(p.getExchange())
                .transactionType(p.getTransactionType())
                .source(p.getSource())
                .entryPrice(p.getEntryPrice())
                .stopLoss(p.getStopLoss())
                .target1(p.getTarget1())
                .target2(p.getTarget2())
                .target3(p.getTarget3())
                .totalQuantity(p.getTotalQuantity())
                .remainingQuantity(p.getRemainingQuantity())
                .status(p.getStatus() != null ? p.getStatus().name() : "UNKNOWN")
                .target1Hit(p.isTarget1Hit())
                .target2Hit(p.isTarget2Hit())
                .target3Hit(p.isTarget3Hit())
                .stopLossHit(p.isStopLossHit())
                .exitPrice(p.getExitPrice())
                .realisedPnl(p.getRealisedPnl())
                .capitalPerTrade(p.getCapitalPerTrade())
                .createdAt(p.getCreatedAt() != null ? p.getCreatedAt().toString() : null)
                .build();
    }
}
