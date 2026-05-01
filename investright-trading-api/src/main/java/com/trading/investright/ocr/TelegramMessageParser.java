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

    private static final Pattern BUY_SELL_LINE = Pattern.compile(
            "(?i)(BUY|SELL)\\s+([A-Z]+)\\s+(\\d+(?:\\.\\d+)?)(CE|PE)\\s+(?:ABV|ABOVE|BLW|BELOW)\\s+(\\d+(?:\\.\\d+)?)(?:\\s+TGT)?");

    private static final Pattern TARGET_LINE = Pattern.compile(
            "^([\\d.]+(?:\\s*[-–]\\s*[\\d.]+)+)$");

    private static final Pattern SL_LINE = Pattern.compile(
            "(?i)SL\\s+(\\d+(?:\\.\\d+)?)");

    private static final Set<String> BSE_INDICES = Set.of("SENSEX", "BANKEX");
    private static final Set<String> SKIP_LINES = Set.of(
            "HERO ZERO", "INTRADAY", "DELIVERY", "POSITIONAL");

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

        Matcher buySellMatcher = BUY_SELL_LINE.matcher(combined);
        if (!buySellMatcher.find()) {
            return null;
        }

        String transactionType = buySellMatcher.group(1).toUpperCase();
        String underlying = buySellMatcher.group(2).toUpperCase();
        double strikePrice = Double.parseDouble(buySellMatcher.group(3));
        String optionType = buySellMatcher.group(4).toUpperCase();
        double entryPrice = Double.parseDouble(buySellMatcher.group(5));

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

        parseTargetsAndSl(lines, builder);

        return builder.build();
    }

    private void parseTargetsAndSl(String[] lines, TradeSignal.TradeSignalBuilder builder) {
        for (String line : lines) {
            line = line.trim();

            Matcher slMatcher = SL_LINE.matcher(line);
            if (slMatcher.find()) {
                builder.stopLoss(Double.parseDouble(slMatcher.group(1)));
                continue;
            }

            Matcher targetMatcher = TARGET_LINE.matcher(line);
            if (targetMatcher.matches()) {
                String[] parts = line.split("\\s*[-–]\\s*");
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
        }
    }

    private String determineExchange(String underlying) {
        if (BSE_INDICES.contains(underlying)) {
            return "BFO";
        }
        return "NFO";
    }

    public boolean isTradeSignalMessage(String text) {
        if (text == null || text.isBlank()) return false;
        return BUY_SELL_LINE.matcher(text).find();
    }
}
