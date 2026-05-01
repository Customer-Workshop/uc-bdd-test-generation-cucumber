package com.trading.investright.ocr;

import com.trading.investright.model.TradeSignal;
import com.trading.investright.model.TradeSignal.InstrumentType;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

@Slf4j
@Component
public class TelegramMessageParser {

    private static final Pattern BUY_SELL_PATTERN = Pattern.compile(
            "(?i)(BUY|SELL)\\s+([A-Z]+)\\s+(\\d+(?:\\.\\d+)?)(CE|PE)\\s+(?:ABV|ABOVE|BLW|BELOW)\\s+(\\d+(?:\\.\\d+)?)(?:\\s*[-–]\\s*(\\d+(?:\\.\\d+)?))?");

    private static final Pattern INLINE_TGT_PATTERN = Pattern.compile(
            "(?i)TGT\\s+([\\d.]+(?:\\s*[-–]\\s*[\\d.]+)*)");

    private static final Pattern STANDALONE_TARGET_LINE = Pattern.compile(
            "^([\\d.]+(?:\\s*[-–]\\s*[\\d.]+)+)$");

    private static final Pattern SL_PATTERN = Pattern.compile(
            "(?i)SL\\s+(\\d+(?:\\.\\d+)?)(?:\\s*[-–]\\s*(\\d+(?:\\.\\d+)?))?");

    private static final Set<String> BSE_INDICES = Set.of("SENSEX", "BANKEX");

    public List<TradeSignal> parseMessage(String messageText) {
        if (messageText == null || messageText.isBlank()) {
            return List.of();
        }

        List<TradeSignal> signals = new ArrayList<>();
        String[] blocks = messageText.split("\\n\\s*\\n");

        for (String block : blocks) {
            try {
                TradeSignal signal = parseBlock(block.trim());
                if (signal != null) {
                    signals.add(signal);
                }
            } catch (Exception ex) {
                log.warn("Failed to parse Telegram message block: {}", ex.getMessage());
            }
        }

        if (signals.isEmpty()) {
            TradeSignal signal = parseBlock(messageText.trim());
            if (signal != null) {
                signals.add(signal);
            }
        }

        return signals;
    }

    TradeSignal parseBlock(String block) {
        String[] lines = block.split("\\n");
        String combined = String.join(" ", lines).trim();

        Matcher buySellMatcher = BUY_SELL_PATTERN.matcher(combined);
        if (!buySellMatcher.find()) {
            return null;
        }

        String transactionType = buySellMatcher.group(1).toUpperCase();
        String underlying = buySellMatcher.group(2).toUpperCase();
        double strikePrice = Double.parseDouble(buySellMatcher.group(3));
        String optionType = buySellMatcher.group(4).toUpperCase();
        double entryPrice1 = Double.parseDouble(buySellMatcher.group(5));
        Double entryPrice2 = buySellMatcher.group(6) != null ?
                Double.parseDouble(buySellMatcher.group(6)) : null;

        double entryPrice;
        if (entryPrice2 != null) {
            entryPrice = "BUY".equals(transactionType) ?
                    Math.max(entryPrice1, entryPrice2) : Math.min(entryPrice1, entryPrice2);
        } else {
            entryPrice = entryPrice1;
        }

        String instrumentName = underlying + " " + (int) strikePrice + optionType;
        InstrumentType instrumentType = "CE".equals(optionType) ?
                InstrumentType.CALL_OPTION : InstrumentType.PUT_OPTION;

        String exchange = determineExchange(underlying);

        TradeSignal.TradeSignalBuilder builder = TradeSignal.builder()
                .instrumentName(instrumentName)
                .underlying(underlying)
                .strikePrice(strikePrice)
                .optionType(optionType)
                .instrumentType(instrumentType)
                .transactionType(transactionType)
                .entryPrice(entryPrice)
                .exchange(exchange)
                .rawText(block)
                .source("telegram");

        parseTargetsAndSl(combined, lines, transactionType, builder);

        TradeSignal signal = builder.build();

        if (!isValidSignal(signal)) {
            log.warn("Skipping incomplete/invalid signal: {} (entry={}, sl={}, target1={})",
                    signal.getInstrumentName(), signal.getEntryPrice(),
                    signal.getStopLoss(), signal.getTarget1());
            return null;
        }

        return signal;
    }

    private boolean isValidSignal(TradeSignal signal) {
        if (signal.getEntryPrice() <= 0) {
            log.warn("Invalid entry price: {}", signal.getEntryPrice());
            return false;
        }
        if (signal.getStopLoss() == null || signal.getStopLoss() <= 0) {
            log.warn("Missing or invalid stop loss for {}", signal.getInstrumentName());
            return false;
        }
        if (signal.getTarget1() == null || signal.getTarget1() <= 0) {
            log.warn("Missing target for {}", signal.getInstrumentName());
            return false;
        }
        if (signal.getStrikePrice() <= 0) {
            log.warn("Invalid strike price: {}", signal.getStrikePrice());
            return false;
        }
        if ("BUY".equals(signal.getTransactionType()) && signal.getStopLoss() >= signal.getEntryPrice()) {
            log.warn("BUY signal SL ({}) >= entry ({}) for {} — likely parsing error",
                    signal.getStopLoss(), signal.getEntryPrice(), signal.getInstrumentName());
            return false;
        }
        if ("SELL".equals(signal.getTransactionType()) && signal.getStopLoss() <= signal.getEntryPrice()) {
            log.warn("SELL signal SL ({}) <= entry ({}) for {} — likely parsing error",
                    signal.getStopLoss(), signal.getEntryPrice(), signal.getInstrumentName());
            return false;
        }
        return true;
    }

    private void parseTargetsAndSl(String combined, String[] lines, String transactionType,
                                    TradeSignal.TradeSignalBuilder builder) {
        Matcher slMatcher = SL_PATTERN.matcher(combined);
        if (slMatcher.find()) {
            double sl1 = Double.parseDouble(slMatcher.group(1));
            Double sl2 = slMatcher.group(2) != null ? Double.parseDouble(slMatcher.group(2)) : null;

            if (sl2 != null) {
                builder.stopLoss("BUY".equals(transactionType) ?
                        Math.min(sl1, sl2) : Math.max(sl1, sl2));
            } else {
                builder.stopLoss(sl1);
            }
        }

        Matcher inlineTgtMatcher = INLINE_TGT_PATTERN.matcher(combined);
        if (inlineTgtMatcher.find()) {
            parseTargetValues(inlineTgtMatcher.group(1), builder);
            return;
        }

        for (String line : lines) {
            line = line.trim();
            Matcher targetMatcher = STANDALONE_TARGET_LINE.matcher(line);
            if (targetMatcher.matches()) {
                parseTargetValues(line, builder);
                return;
            }
        }
    }

    private void parseTargetValues(String targetStr, TradeSignal.TradeSignalBuilder builder) {
        String[] parts = targetStr.split("\\s*[-–]\\s*");
        List<Double> targets = new ArrayList<>();
        for (String part : parts) {
            try {
                targets.add(Double.parseDouble(part.trim()));
            } catch (NumberFormatException ignored) {
            }
        }
        if (targets.size() >= 1) builder.target1(targets.get(0));
        if (targets.size() >= 2) builder.target2(targets.get(1));
        if (targets.size() >= 3) builder.target3(targets.get(2));
        if (targets.size() >= 4) builder.target4(targets.get(3));
    }

    private String determineExchange(String underlying) {
        if (BSE_INDICES.contains(underlying)) {
            return "BFO";
        }
        return "NFO";
    }

    public boolean isTradeSignalMessage(String text) {
        if (text == null || text.isBlank()) return false;
        return BUY_SELL_PATTERN.matcher(text).find();
    }
}
