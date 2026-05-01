package com.trading.investright.service;

import com.trading.investright.model.TradeSignal;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.List;

@Slf4j
@Component
public class TradeSignalValidator {

    public List<TradeSignal> filterValid(List<TradeSignal> signals, String source) {
        List<TradeSignal> valid = new ArrayList<>();
        for (TradeSignal signal : signals) {
            List<String> errors = validate(signal);
            if (errors.isEmpty()) {
                valid.add(signal);
            } else {
                log.warn("Rejecting {} signal '{}': {}",
                        source, signal.getInstrumentName(), String.join("; ", errors));
            }
        }
        if (signals.size() != valid.size()) {
            log.info("Validation: {}/{} {} signals passed", valid.size(), signals.size(), source);
        }
        return valid;
    }

    public List<String> validate(TradeSignal signal) {
        List<String> errors = new ArrayList<>();

        if (signal.getInstrumentName() == null || signal.getInstrumentName().isBlank()) {
            errors.add("missing instrument name");
        }

        if (signal.getTransactionType() == null || signal.getTransactionType().isBlank()) {
            errors.add("missing transaction type (BUY/SELL)");
        } else if (!"BUY".equalsIgnoreCase(signal.getTransactionType())
                && !"SELL".equalsIgnoreCase(signal.getTransactionType())) {
            errors.add("invalid transaction type: " + signal.getTransactionType());
        }

        if (signal.getEntryPrice() == null || signal.getEntryPrice() <= 0) {
            errors.add("missing or invalid entry price");
        }

        if (signal.getStopLoss() == null || signal.getStopLoss() <= 0) {
            errors.add("missing stop loss");
        }

        if (signal.getTarget1() == null || signal.getTarget1() <= 0) {
            errors.add("missing at least one target");
        }

        if (signal.getEntryPrice() != null && signal.getEntryPrice() > 0
                && signal.getStopLoss() != null && signal.getStopLoss() > 0
                && signal.getTransactionType() != null) {
            if ("BUY".equalsIgnoreCase(signal.getTransactionType())
                    && signal.getStopLoss() >= signal.getEntryPrice()) {
                errors.add("BUY signal: SL (" + signal.getStopLoss()
                        + ") must be below entry (" + signal.getEntryPrice() + ")");
            }
            if ("SELL".equalsIgnoreCase(signal.getTransactionType())
                    && signal.getStopLoss() <= signal.getEntryPrice()) {
                errors.add("SELL signal: SL (" + signal.getStopLoss()
                        + ") must be above entry (" + signal.getEntryPrice() + ")");
            }
        }

        if (signal.getEntryPrice() != null && signal.getEntryPrice() > 0
                && signal.getTarget1() != null && signal.getTarget1() > 0
                && signal.getTransactionType() != null) {
            if ("BUY".equalsIgnoreCase(signal.getTransactionType())
                    && signal.getTarget1() <= signal.getEntryPrice()) {
                errors.add("BUY signal: target1 (" + signal.getTarget1()
                        + ") must be above entry (" + signal.getEntryPrice() + ")");
            }
            if ("SELL".equalsIgnoreCase(signal.getTransactionType())
                    && signal.getTarget1() >= signal.getEntryPrice()) {
                errors.add("SELL signal: target1 (" + signal.getTarget1()
                        + ") must be below entry (" + signal.getEntryPrice() + ")");
            }
        }

        if (signal.getStrikePrice() != null && signal.getStrikePrice() < 0) {
            errors.add("invalid strike price: " + signal.getStrikePrice());
        }

        String exchange = signal.getExchange();
        if (exchange != null && !exchange.isBlank()
                && !List.of("NSE", "BSE", "NFO", "BFO").contains(exchange.toUpperCase())) {
            errors.add("invalid exchange: " + exchange);
        }

        return errors;
    }
}
