package com.trading.investright.ocr;

import com.trading.investright.model.TradeSignal;
import com.trading.investright.model.TradeSignal.InstrumentType;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

@Slf4j
@Component
public class TradeSignalParser {

    private static final Pattern OPTION_PATTERN = Pattern.compile(
            "^(.+?)\\s+(\\d+(?:\\.\\d+)?)(CE|PE)$", Pattern.CASE_INSENSITIVE);

    private static final Pattern BUY_ABOVE_PATTERN = Pattern.compile(
            "BUY\\s+ABOVE\\s+(\\d+(?:\\.\\d+)?)", Pattern.CASE_INSENSITIVE);

    private static final Pattern SELL_BELOW_PATTERN = Pattern.compile(
            "SELL\\s+BELOW\\s+(\\d+(?:\\.\\d+)?)", Pattern.CASE_INSENSITIVE);

    private static final Pattern STOP_LOSS_PATTERN = Pattern.compile(
            "(?:SL|STOP\\s*LOSS|STOPLOSS)[:\\s]+(\\d+(?:\\.\\d+)?)", Pattern.CASE_INSENSITIVE);

    private static final Pattern TARGET_PATTERN = Pattern.compile(
            "(?:TGT|TARGET|T)[:\\s]*(\\d+(?:\\.\\d+)?)", Pattern.CASE_INSENSITIVE);

    private static final Pattern PRICE_PATTERN = Pattern.compile(
            "(\\d+(?:\\.\\d+)?)");

    public List<TradeSignal> parseOcrText(String ocrText) {
        List<TradeSignal> signals = new ArrayList<>();
        String[] lines = ocrText.split("\\n");

        for (int i = 0; i < lines.length; i++) {
            String line = lines[i].trim();
            if (line.isEmpty()) continue;

            try {
                TradeSignal signal = parseLine(line, i < lines.length - 1 ? lines[i + 1].trim() : "");
                if (signal != null) {
                    signals.add(signal);
                }
            } catch (Exception ex) {
                log.warn("Failed to parse line {}: '{}' - {}", i, line, ex.getMessage());
            }
        }

        return signals;
    }

    TradeSignal parseLine(String line, String nextLine) {
        String combined = line + " " + nextLine;

        String instrumentName = extractInstrumentName(line);
        if (instrumentName == null || instrumentName.isBlank()) {
            return null;
        }

        TradeSignal.TradeSignalBuilder builder = TradeSignal.builder()
                .rawText(line)
                .instrumentName(instrumentName);

        parseInstrumentType(instrumentName, builder);

        String transactionType = null;
        Double entryPrice = null;

        Matcher buyMatcher = BUY_ABOVE_PATTERN.matcher(combined);
        Matcher sellMatcher = SELL_BELOW_PATTERN.matcher(combined);

        if (buyMatcher.find()) {
            transactionType = "BUY";
            entryPrice = Double.parseDouble(buyMatcher.group(1));
        } else if (sellMatcher.find()) {
            transactionType = "SELL";
            entryPrice = Double.parseDouble(sellMatcher.group(1));
        }

        if (transactionType == null) {
            if (combined.toUpperCase().contains("BUY")) {
                transactionType = "BUY";
            } else if (combined.toUpperCase().contains("SELL")) {
                transactionType = "SELL";
            }
        }

        builder.transactionType(transactionType);
        builder.entryPrice(entryPrice);

        Matcher slMatcher = STOP_LOSS_PATTERN.matcher(combined);
        if (slMatcher.find()) {
            builder.stopLoss(Double.parseDouble(slMatcher.group(1)));
        } else if (entryPrice != null) {
            Double inferredSl = inferStopLossFromContext(combined, entryPrice);
            if (inferredSl != null) {
                builder.stopLoss(inferredSl);
            }
        }

        List<Double> targets = extractTargets(combined);
        if (targets.size() >= 1) builder.target1(targets.get(0));
        if (targets.size() >= 2) builder.target2(targets.get(1));
        if (targets.size() >= 3) builder.target3(targets.get(2));

        return builder.build();
    }

    private String extractInstrumentName(String line) {
        String cleaned = line.replaceFirst("^\\d{1,2}[-/]\\d{1,2}[-/]\\d{2,4}\\s*", "");

        String[] tokens = cleaned.split("\\s+");
        if (tokens.length == 0) return null;

        StringBuilder name = new StringBuilder();
        for (String token : tokens) {
            if (token.matches("(?i)(BUY|SELL|ABOVE|BELOW|SL|TARGET|TGT|STOP|LOSS|STOPLOSS)")) {
                break;
            }
            if (token.matches("\\d+\\.\\d+") || token.matches("\\d{4,}")) {
                if (name.isEmpty()) continue;
                break;
            }
            if (!name.isEmpty()) name.append(" ");
            name.append(token);
        }

        return name.toString().trim();
    }

    void parseInstrumentType(String instrumentName, TradeSignal.TradeSignalBuilder builder) {
        Matcher optionMatcher = OPTION_PATTERN.matcher(instrumentName.trim());
        if (optionMatcher.matches()) {
            String underlying = optionMatcher.group(1).trim();
            double strikePrice = Double.parseDouble(optionMatcher.group(2));
            String optionType = optionMatcher.group(3).toUpperCase();

            builder.underlying(underlying)
                    .strikePrice(strikePrice)
                    .optionType(optionType)
                    .instrumentType(optionType.equals("CE") ? InstrumentType.CALL_OPTION : InstrumentType.PUT_OPTION)
                    .exchange("NFO");
        } else {
            builder.underlying(instrumentName.trim())
                    .instrumentType(InstrumentType.EQUITY)
                    .exchange("NSE");
        }
    }

    private Double inferStopLossFromContext(String text, double entryPrice) {
        Pattern numberAfterEntry = Pattern.compile(
                "(?:BUY\\s+ABOVE|SELL\\s+BELOW)\\s+\\d+(?:\\.\\d+)?\\s+(\\d+(?:\\.\\d+)?)",
                Pattern.CASE_INSENSITIVE);
        Matcher matcher = numberAfterEntry.matcher(text);
        if (matcher.find()) {
            double value = Double.parseDouble(matcher.group(1));
            if (value < entryPrice && value > entryPrice * 0.5) {
                return value;
            }
        }
        return null;
    }

    private List<Double> extractTargets(String text) {
        List<Double> targets = new ArrayList<>();

        Pattern multiTargetPattern = Pattern.compile(
                "(?:TGT|TARGET|TARGETS?)[:\\s]*(\\d+(?:\\.\\d+)?)(?:[,/\\s]+(\\d+(?:\\.\\d+)?))?(?:[,/\\s]+(\\d+(?:\\.\\d+)?))?",
                Pattern.CASE_INSENSITIVE);
        Matcher matcher = multiTargetPattern.matcher(text);

        if (matcher.find()) {
            for (int i = 1; i <= matcher.groupCount(); i++) {
                if (matcher.group(i) != null) {
                    targets.add(Double.parseDouble(matcher.group(i)));
                }
            }
        }

        if (targets.isEmpty()) {
            Pattern slashSeparated = Pattern.compile(
                    "(\\d+(?:\\.\\d+)?)/(\\d+(?:\\.\\d+)?)(?:/(\\d+(?:\\.\\d+)?))?");
            Matcher slashMatcher = slashSeparated.matcher(text);
            if (slashMatcher.find()) {
                for (int i = 1; i <= slashMatcher.groupCount(); i++) {
                    if (slashMatcher.group(i) != null) {
                        targets.add(Double.parseDouble(slashMatcher.group(i)));
                    }
                }
            }
        }

        return targets;
    }
}
