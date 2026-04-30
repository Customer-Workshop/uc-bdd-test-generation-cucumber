package com.trading.investright.scheduler;

import com.trading.investright.config.SchedulerProperties;
import com.trading.investright.model.TradePosition;
import com.trading.investright.service.CsvPositionPersistence;
import com.trading.investright.service.PositionTracker;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

import java.io.BufferedWriter;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.LocalDate;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import java.util.List;

@Slf4j
@Component
@RequiredArgsConstructor
@ConditionalOnProperty(name = "scheduler.enabled", havingValue = "true")
public class DailyReportService {

    private final PositionTracker positionTracker;
    private final CsvPositionPersistence csvPersistence;
    private final SchedulerProperties schedulerProperties;

    private static final DateTimeFormatter DATE_FMT = DateTimeFormatter.ofPattern("yyyy-MM-dd");

    @Scheduled(cron = "0 28 15 * * *", zone = "${scheduler.timezone:Asia/Kolkata}")
    public void generateDailyReport() {
        log.info("Generating daily P&L report at 3:28 PM IST...");
        List<TradePosition> allPositions = positionTracker.getAllPositions();
        if (allPositions.isEmpty()) {
            log.info("No trades today — skipping report generation.");
            return;
        }

        Path reportFile = getReportFilePath();
        try {
            Files.createDirectories(reportFile.getParent());
            writeReport(allPositions, reportFile);
            log.info("Daily report saved to {}", reportFile);
        } catch (IOException ex) {
            log.error("Failed to generate daily report: {}", ex.getMessage());
        }
    }

    void writeReport(List<TradePosition> positions, Path reportFile) throws IOException {
        double totalInvested = 0;
        double totalPnl = 0;
        int wins = 0;
        int losses = 0;
        int active = 0;

        try (BufferedWriter writer = Files.newBufferedWriter(reportFile)) {
            writer.write("DAILY TRADE REPORT — " + LocalDate.now(ZoneId.of(schedulerProperties.getTimezone())).format(DATE_FMT));
            writer.newLine();
            writer.write("=".repeat(100));
            writer.newLine();
            writer.newLine();

            writer.write(String.format("%-25s %-6s %-8s %-10s %-10s %-10s %-12s %-10s %-12s%n",
                    "INSTRUMENT", "TYPE", "QTY", "ENTRY", "SL", "CURRENT_SL", "STATUS", "P&L/UNIT", "TOTAL_P&L"));
            writer.write("-".repeat(100));
            writer.newLine();

            for (TradePosition p : positions) {
                double pnlPerUnit = calculatePnlPerUnit(p);
                int qty = p.getFilledQuantity() > 0 ? p.getFilledQuantity() : p.getTotalQuantity();
                double totalPositionPnl = pnlPerUnit * qty;
                double invested = p.getEntryPrice() * qty;

                totalInvested += invested;
                totalPnl += totalPositionPnl;

                if (isClosedPosition(p)) {
                    if (totalPositionPnl >= 0) wins++;
                    else losses++;
                } else {
                    active++;
                }

                writer.write(String.format("%-25s %-6s %-8d ₹%-9.2f ₹%-9.2f ₹%-9.2f %-12s ₹%-9.2f ₹%-11.2f%n",
                        truncate(p.getInstrumentName(), 25),
                        p.getTransactionType(),
                        qty,
                        p.getEntryPrice(),
                        p.getStopLoss(),
                        p.getStopLoss(),
                        p.getStatus(),
                        pnlPerUnit,
                        totalPositionPnl));
            }

            writer.newLine();
            writer.write("=".repeat(100));
            writer.newLine();
            writer.write(String.format("TOTAL TRADES:     %d%n", positions.size()));
            writer.write(String.format("WINS:             %d%n", wins));
            writer.write(String.format("LOSSES:           %d%n", losses));
            writer.write(String.format("ACTIVE:           %d%n", active));
            writer.write(String.format("WIN RATE:         %.1f%%%n", (wins + losses) > 0 ? (wins * 100.0 / (wins + losses)) : 0));
            writer.write(String.format("TOTAL INVESTED:   ₹%,.2f%n", totalInvested));
            writer.write(String.format("TOTAL P&L:        ₹%,.2f%n", totalPnl));
            writer.write(String.format("ROI:              %.2f%%%n", totalInvested > 0 ? (totalPnl / totalInvested * 100) : 0));
            writer.newLine();

            writer.write("TARGET PROGRESS:");
            writer.newLine();
            for (TradePosition p : positions) {
                String targets = String.format("  %-25s T1:%s T2:%s T3:%s",
                        truncate(p.getInstrumentName(), 25),
                        p.isTarget1Hit() ? "HIT" : "---",
                        p.isTarget2Hit() ? "HIT" : "---",
                        p.isTarget3Hit() ? "HIT" : "---");
                if (p.isStopLossHit()) targets += " [SL HIT]";
                writer.write(targets);
                writer.newLine();
            }
        }
    }

    private double calculatePnlPerUnit(TradePosition p) {
        if (p.isStopLossHit()) {
            if ("BUY".equalsIgnoreCase(p.getTransactionType())) {
                return p.getStopLoss() - p.getEntryPrice();
            } else {
                return p.getEntryPrice() - p.getStopLoss();
            }
        }
        if (p.isTarget3Hit()) {
            if (p.getTarget3() != null) {
                return "BUY".equalsIgnoreCase(p.getTransactionType())
                        ? p.getTarget3() - p.getEntryPrice()
                        : p.getEntryPrice() - p.getTarget3();
            }
        }
        return 0.0;
    }

    private boolean isClosedPosition(TradePosition p) {
        return p.getStatus() == TradePosition.PositionStatus.EXITED_TARGET
                || p.getStatus() == TradePosition.PositionStatus.EXITED_STOPLOSS
                || p.getStatus() == TradePosition.PositionStatus.CLOSED;
    }

    Path getReportFilePath() {
        return csvPersistence.getDateFolder().resolve("report.txt");
    }

    private String truncate(String s, int maxLen) {
        if (s == null) return "";
        return s.length() > maxLen ? s.substring(0, maxLen) : s;
    }
}
