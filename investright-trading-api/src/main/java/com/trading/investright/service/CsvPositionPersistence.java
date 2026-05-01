package com.trading.investright.service;

import com.trading.investright.config.SchedulerProperties;
import com.trading.investright.model.TradePosition;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.Instant;
import java.time.LocalDate;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;

@Slf4j
@Service
@RequiredArgsConstructor
public class CsvPositionPersistence {

    private final SchedulerProperties schedulerProperties;

    private static final DateTimeFormatter DATE_FMT = DateTimeFormatter.ofPattern("yyyy-MM-dd");
    private static final String POSITIONS_FILE = "positions.csv";
    private static final String CSV_HEADER = "positionId,orderId,instrumentName,tradingSymbol,exchange,instrumentSegment," +
            "transactionType,entryPrice,stopLoss,target1,target2,target3,totalQuantity,remainingQuantity,filledQuantity," +
            "status,target1Hit,target2Hit,target3Hit,stopLossHit,protectiveSlPlaced,amoExecuted,regularOrderPlaced," +
            "openPrice,activeSlOrderId,userId,createdAt,lastCheckedAt,source,capitalPerTrade,exitPrice,realisedPnl";

    public void savePositions(List<TradePosition> positions) {
        Path folder = getDateFolder();
        try {
            Files.createDirectories(folder);
            Path file = folder.resolve(POSITIONS_FILE);
            try (BufferedWriter writer = Files.newBufferedWriter(file)) {
                writer.write(CSV_HEADER);
                writer.newLine();
                for (TradePosition p : positions) {
                    writer.write(toCsvLine(p));
                    writer.newLine();
                }
            }
            log.debug("Saved {} positions to {}", positions.size(), file);
        } catch (IOException ex) {
            log.error("Failed to save positions to CSV: {}", ex.getMessage());
        }
    }

    public List<TradePosition> loadPositions() {
        Path file = getDateFolder().resolve(POSITIONS_FILE);
        if (!Files.exists(file)) {
            log.debug("No positions CSV found at {}", file);
            return new ArrayList<>();
        }

        List<TradePosition> positions = new ArrayList<>();
        try (BufferedReader reader = Files.newBufferedReader(file)) {
            String header = reader.readLine();
            if (header == null) return positions;

            String line;
            while ((line = reader.readLine()) != null) {
                if (line.isBlank()) continue;
                try {
                    positions.add(fromCsvLine(line));
                } catch (Exception ex) {
                    log.warn("Skipping malformed CSV line: {}", ex.getMessage());
                }
            }
            log.info("Loaded {} positions from {}", positions.size(), file);
        } catch (IOException ex) {
            log.error("Failed to load positions from CSV: {}", ex.getMessage());
        }
        return positions;
    }

    public Path getDateFolder() {
        String basePath = schedulerProperties.getLocalFolderPath();
        if (basePath == null || basePath.isBlank()) {
            basePath = System.getProperty("user.home") + "/trades";
        }
        String timezone = schedulerProperties.getTimezone() != null ? schedulerProperties.getTimezone() : "Asia/Kolkata";
        String dateStr = LocalDate.now(ZoneId.of(timezone)).format(DATE_FMT);
        return Paths.get(basePath, dateStr);
    }

    private String toCsvLine(TradePosition p) {
        return String.join(",",
                escapeCsv(p.getPositionId()),
                escapeCsv(p.getOrderId()),
                escapeCsv(p.getInstrumentName()),
                escapeCsv(p.getTradingSymbol()),
                escapeCsv(p.getExchange()),
                escapeCsv(p.getInstrumentSegment()),
                escapeCsv(p.getTransactionType()),
                String.valueOf(p.getEntryPrice()),
                String.valueOf(p.getStopLoss()),
                doubleToStr(p.getTarget1()),
                doubleToStr(p.getTarget2()),
                doubleToStr(p.getTarget3()),
                String.valueOf(p.getTotalQuantity()),
                String.valueOf(p.getRemainingQuantity()),
                String.valueOf(p.getFilledQuantity()),
                p.getStatus() != null ? p.getStatus().name() : "",
                String.valueOf(p.isTarget1Hit()),
                String.valueOf(p.isTarget2Hit()),
                String.valueOf(p.isTarget3Hit()),
                String.valueOf(p.isStopLossHit()),
                String.valueOf(p.isProtectiveSlPlaced()),
                String.valueOf(p.isAmoExecuted()),
                String.valueOf(p.isRegularOrderPlaced()),
                doubleToStr(p.getOpenPrice()),
                escapeCsv(p.getActiveSlOrderId()),
                escapeCsv(p.getUserId()),
                p.getCreatedAt() != null ? p.getCreatedAt().toString() : "",
                p.getLastCheckedAt() != null ? p.getLastCheckedAt().toString() : "",
                escapeCsv(p.getSource()),
                String.valueOf(p.getCapitalPerTrade()),
                doubleToStr(p.getExitPrice()),
                doubleToStr(p.getRealisedPnl())
        );
    }

    TradePosition fromCsvLine(String line) {
        String[] parts = parseCsvLine(line);
        if (parts.length < 28) {
            throw new IllegalArgumentException(
                    "CSV line has " + parts.length + " fields, expected at least 28");
        }
        return TradePosition.builder()
                .positionId(parts[0])
                .orderId(parts[1])
                .instrumentName(parts[2])
                .tradingSymbol(parts[3])
                .exchange(parts[4])
                .instrumentSegment(parts[5])
                .transactionType(parts[6])
                .entryPrice(parseDouble(parts[7]))
                .stopLoss(parseDouble(parts[8]))
                .target1(parseNullableDouble(parts[9]))
                .target2(parseNullableDouble(parts[10]))
                .target3(parseNullableDouble(parts[11]))
                .totalQuantity(parseInt(parts[12]))
                .remainingQuantity(parseInt(parts[13]))
                .filledQuantity(parseInt(parts[14]))
                .status(parseStatus(parts[15]))
                .target1Hit(parseBoolean(parts[16]))
                .target2Hit(parseBoolean(parts[17]))
                .target3Hit(parseBoolean(parts[18]))
                .stopLossHit(parseBoolean(parts[19]))
                .protectiveSlPlaced(parseBoolean(parts[20]))
                .amoExecuted(parseBoolean(parts[21]))
                .regularOrderPlaced(parseBoolean(parts[22]))
                .openPrice(parseNullableDouble(parts[23]))
                .activeSlOrderId(emptyToNull(parts[24]))
                .userId(parts[25])
                .createdAt(parseInstant(parts[26]))
                .lastCheckedAt(parseInstant(parts[27]))
                .source(parts.length > 28 ? emptyToNull(parts[28]) : null)
                .capitalPerTrade(parts.length > 29 ? parseDouble(parts[29]) : 0.0)
                .exitPrice(parts.length > 30 ? parseNullableDouble(parts[30]) : null)
                .realisedPnl(parts.length > 31 ? parseNullableDouble(parts[31]) : null)
                .build();
    }

    private String[] parseCsvLine(String line) {
        List<String> fields = new ArrayList<>();
        StringBuilder sb = new StringBuilder();
        boolean inQuotes = false;
        for (int i = 0; i < line.length(); i++) {
            char c = line.charAt(i);
            if (c == '"') {
                inQuotes = !inQuotes;
            } else if (c == ',' && !inQuotes) {
                fields.add(sb.toString());
                sb.setLength(0);
            } else {
                sb.append(c);
            }
        }
        fields.add(sb.toString());
        return fields.toArray(new String[0]);
    }

    private String escapeCsv(String value) {
        if (value == null) return "";
        if (value.contains(",") || value.contains("\"") || value.contains("\n")) {
            return "\"" + value.replace("\"", "\"\"") + "\"";
        }
        return value;
    }

    private String doubleToStr(Double value) {
        return value != null ? String.valueOf(value) : "";
    }

    private double parseDouble(String s) {
        if (s == null || s.isBlank()) return 0.0;
        return Double.parseDouble(s.trim());
    }

    private Double parseNullableDouble(String s) {
        if (s == null || s.isBlank()) return null;
        return Double.parseDouble(s.trim());
    }

    private int parseInt(String s) {
        if (s == null || s.isBlank()) return 0;
        return Integer.parseInt(s.trim());
    }

    private boolean parseBoolean(String s) {
        return "true".equalsIgnoreCase(s != null ? s.trim() : "");
    }

    private TradePosition.PositionStatus parseStatus(String s) {
        if (s == null || s.isBlank()) return TradePosition.PositionStatus.ACTIVE;
        try {
            return TradePosition.PositionStatus.valueOf(s.trim());
        } catch (IllegalArgumentException e) {
            return TradePosition.PositionStatus.ACTIVE;
        }
    }

    private Instant parseInstant(String s) {
        if (s == null || s.isBlank()) return null;
        try {
            return Instant.parse(s.trim());
        } catch (Exception e) {
            return null;
        }
    }

    private String emptyToNull(String s) {
        if (s == null || s.isBlank()) return null;
        return s;
    }
}
