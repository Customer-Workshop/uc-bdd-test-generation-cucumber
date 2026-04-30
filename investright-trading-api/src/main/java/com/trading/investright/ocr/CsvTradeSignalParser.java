package com.trading.investright.ocr;

import com.trading.investright.model.TradeSignal;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

import java.io.BufferedReader;
import java.io.IOException;
import java.nio.file.DirectoryStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

@Slf4j
@Component
public class CsvTradeSignalParser {

    private static final Pattern OPTION_PATTERN = Pattern.compile("^(.+?)\\s*(\\d+(?:\\.\\d+)?)(CE|PE)$");

    public List<TradeSignal> parseCsvFile(String filePath) {
        Path path = Paths.get(filePath);
        if (!Files.exists(path)) {
            log.warn("CSV file not found: {}", filePath);
            return List.of();
        }

        List<TradeSignal> signals = new ArrayList<>();
        try (BufferedReader reader = Files.newBufferedReader(path)) {
            String headerLine = reader.readLine();
            if (headerLine == null) {
                log.warn("Empty CSV file: {}", filePath);
                return List.of();
            }

            String[] headers = parseHeaders(headerLine);
            String line;
            int lineNum = 1;
            while ((line = reader.readLine()) != null) {
                lineNum++;
                line = line.trim();
                if (line.isEmpty()) continue;

                try {
                    TradeSignal signal = parseCsvRow(headers, line);
                    if (signal != null) {
                        signals.add(signal);
                    }
                } catch (Exception ex) {
                    log.warn("Failed to parse CSV line {}: {}", lineNum, ex.getMessage());
                }
            }
        } catch (IOException ex) {
            log.error("Failed to read CSV file {}: {}", filePath, ex.getMessage());
        }

        log.info("Parsed {} trade signals from CSV: {}", signals.size(), filePath);
        return signals;
    }

    public List<TradeSignal> parseCsvFilesFromFolder(String folderPath) {
        Path folder = Paths.get(folderPath);
        if (!Files.exists(folder) || !Files.isDirectory(folder)) {
            log.warn("CSV folder not found: {}", folderPath);
            return List.of();
        }

        List<TradeSignal> allSignals = new ArrayList<>();
        try (DirectoryStream<Path> stream = Files.newDirectoryStream(folder, "*.csv")) {
            for (Path file : stream) {
                List<TradeSignal> signals = parseCsvFile(file.toString());
                allSignals.addAll(signals);
            }
        } catch (IOException ex) {
            log.error("Failed to read CSV folder {}: {}", folderPath, ex.getMessage());
        }
        return allSignals;
    }

    String[] parseHeaders(String headerLine) {
        String[] raw = headerLine.split(",");
        String[] headers = new String[raw.length];
        for (int i = 0; i < raw.length; i++) {
            headers[i] = raw[i].trim().toLowerCase()
                    .replace(" ", "_")
                    .replace("\"", "");
        }
        return headers;
    }

    TradeSignal parseCsvRow(String[] headers, String line) {
        String[] values = splitCsvLine(line);
        if (values.length < 2) return null;

        TradeSignal.TradeSignalBuilder builder = TradeSignal.builder();
        builder.rawText(line);

        for (int i = 0; i < Math.min(headers.length, values.length); i++) {
            String header = headers[i];
            String value = values[i].trim().replace("\"", "");
            if (value.isEmpty()) continue;

            switch (header) {
                case "symbol", "stock", "instrument", "instrument_name", "name", "scrip" ->
                        setInstrumentInfo(builder, value);
                case "entry", "entry_price", "price", "buy_above", "sell_below", "cmp" ->
                        builder.entryPrice(parseDouble(value));
                case "sl", "stop_loss", "stoploss" ->
                        builder.stopLoss(parseDouble(value));
                case "target", "tgt", "target1", "tgt1", "t1" ->
                        builder.target1(parseDouble(value));
                case "target2", "tgt2", "t2" ->
                        builder.target2(parseDouble(value));
                case "target3", "tgt3", "t3" ->
                        builder.target3(parseDouble(value));
                case "type", "transaction_type", "txn_type", "side", "action", "buy_sell" ->
                        builder.transactionType(value.toUpperCase());
                case "exchange" ->
                        builder.exchange(value.toUpperCase());
                case "date" ->
                        builder.date(value);
                default -> { }
            }
        }

        TradeSignal signal = builder.build();

        if (signal.getInstrumentName() == null || signal.getInstrumentName().isBlank()) {
            return null;
        }

        if (signal.getTransactionType() == null) {
            if (signal.getEntryPrice() != null && signal.getEntryPrice() > 0) {
                signal.setTransactionType("BUY");
            }
        }

        if (signal.getExchange() == null) {
            signal.setExchange(signal.getInstrumentType() != TradeSignal.InstrumentType.EQUITY ? "NFO" : "NSE");
        }

        return signal;
    }

    private void setInstrumentInfo(TradeSignal.TradeSignalBuilder builder, String instrumentName) {
        builder.instrumentName(instrumentName);

        Matcher matcher = OPTION_PATTERN.matcher(instrumentName.toUpperCase().trim());
        if (matcher.matches()) {
            String underlying = matcher.group(1).trim();
            double strike = Double.parseDouble(matcher.group(2));
            String optionType = matcher.group(3);

            builder.underlying(underlying)
                    .strikePrice(strike)
                    .optionType(optionType)
                    .instrumentType("CE".equals(optionType) ?
                            TradeSignal.InstrumentType.CALL_OPTION :
                            TradeSignal.InstrumentType.PUT_OPTION);
        } else {
            builder.underlying(instrumentName.toUpperCase().trim())
                    .instrumentType(TradeSignal.InstrumentType.EQUITY);
        }
    }

    private String[] splitCsvLine(String line) {
        List<String> values = new ArrayList<>();
        boolean inQuotes = false;
        StringBuilder current = new StringBuilder();

        for (char c : line.toCharArray()) {
            if (c == '"') {
                inQuotes = !inQuotes;
            } else if (c == ',' && !inQuotes) {
                values.add(current.toString());
                current = new StringBuilder();
            } else {
                current.append(c);
            }
        }
        values.add(current.toString());
        return values.toArray(new String[0]);
    }

    private Double parseDouble(String value) {
        try {
            return Double.parseDouble(value.replaceAll("[^0-9.]", ""));
        } catch (NumberFormatException ex) {
            return null;
        }
    }
}
