package com.trading.investright.service;

import com.trading.investright.model.TradeSignal;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

class TradeSignalValidatorTest {

    private TradeSignalValidator validator;

    @BeforeEach
    void setUp() {
        validator = new TradeSignalValidator();
    }

    private TradeSignal.TradeSignalBuilder validBuySignal() {
        return TradeSignal.builder()
                .instrumentName("NIFTY 24500CE")
                .underlying("NIFTY")
                .strikePrice(24500.0)
                .optionType("CE")
                .transactionType("BUY")
                .entryPrice(150.0)
                .stopLoss(120.0)
                .target1(180.0)
                .exchange("NFO");
    }

    private TradeSignal.TradeSignalBuilder validSellSignal() {
        return TradeSignal.builder()
                .instrumentName("BANKNIFTY 52000PE")
                .underlying("BANKNIFTY")
                .strikePrice(52000.0)
                .optionType("PE")
                .transactionType("SELL")
                .entryPrice(300.0)
                .stopLoss(350.0)
                .target1(250.0)
                .exchange("NFO");
    }

    @Test
    void shouldAcceptValidBuySignal() {
        List<String> errors = validator.validate(validBuySignal().build());
        assertTrue(errors.isEmpty(), "Expected no errors but got: " + errors);
    }

    @Test
    void shouldAcceptValidSellSignal() {
        List<String> errors = validator.validate(validSellSignal().build());
        assertTrue(errors.isEmpty(), "Expected no errors but got: " + errors);
    }

    @Test
    void shouldRejectMissingInstrumentName() {
        TradeSignal signal = validBuySignal().instrumentName(null).build();
        List<String> errors = validator.validate(signal);
        assertTrue(errors.stream().anyMatch(e -> e.contains("instrument name")));
    }

    @Test
    void shouldRejectMissingTransactionType() {
        TradeSignal signal = validBuySignal().transactionType(null).build();
        List<String> errors = validator.validate(signal);
        assertTrue(errors.stream().anyMatch(e -> e.contains("transaction type")));
    }

    @Test
    void shouldRejectInvalidTransactionType() {
        TradeSignal signal = validBuySignal().transactionType("HOLD").build();
        List<String> errors = validator.validate(signal);
        assertTrue(errors.stream().anyMatch(e -> e.contains("invalid transaction type")));
    }

    @Test
    void shouldRejectMissingEntryPrice() {
        TradeSignal signal = validBuySignal().entryPrice(null).build();
        List<String> errors = validator.validate(signal);
        assertTrue(errors.stream().anyMatch(e -> e.contains("entry price")));
    }

    @Test
    void shouldRejectZeroEntryPrice() {
        TradeSignal signal = validBuySignal().entryPrice(0.0).build();
        List<String> errors = validator.validate(signal);
        assertTrue(errors.stream().anyMatch(e -> e.contains("entry price")));
    }

    @Test
    void shouldRejectMissingStopLoss() {
        TradeSignal signal = validBuySignal().stopLoss(null).build();
        List<String> errors = validator.validate(signal);
        assertTrue(errors.stream().anyMatch(e -> e.contains("stop loss")));
    }

    @Test
    void shouldRejectMissingTarget() {
        TradeSignal signal = validBuySignal().target1(null).build();
        List<String> errors = validator.validate(signal);
        assertTrue(errors.stream().anyMatch(e -> e.contains("target")));
    }

    @Test
    void shouldRejectBuyWithSlAboveEntry() {
        TradeSignal signal = validBuySignal().stopLoss(160.0).build();
        List<String> errors = validator.validate(signal);
        assertTrue(errors.stream().anyMatch(e -> e.contains("SL") && e.contains("below entry")));
    }

    @Test
    void shouldRejectSellWithSlBelowEntry() {
        TradeSignal signal = validSellSignal().stopLoss(280.0).build();
        List<String> errors = validator.validate(signal);
        assertTrue(errors.stream().anyMatch(e -> e.contains("SL") && e.contains("above entry")));
    }

    @Test
    void shouldRejectBuyWithTargetBelowEntry() {
        TradeSignal signal = validBuySignal().target1(100.0).build();
        List<String> errors = validator.validate(signal);
        assertTrue(errors.stream().anyMatch(e -> e.contains("target1") && e.contains("above entry")));
    }

    @Test
    void shouldRejectSellWithTargetAboveEntry() {
        TradeSignal signal = validSellSignal().target1(400.0).build();
        List<String> errors = validator.validate(signal);
        assertTrue(errors.stream().anyMatch(e -> e.contains("target1") && e.contains("below entry")));
    }

    @Test
    void shouldRejectInvalidExchange() {
        TradeSignal signal = validBuySignal().exchange("XYZZ").build();
        List<String> errors = validator.validate(signal);
        assertTrue(errors.stream().anyMatch(e -> e.contains("invalid exchange")));
    }

    @Test
    void shouldAcceptNullExchange() {
        TradeSignal signal = validBuySignal().exchange(null).build();
        List<String> errors = validator.validate(signal);
        assertTrue(errors.isEmpty());
    }

    @Test
    void shouldCollectMultipleErrors() {
        TradeSignal signal = TradeSignal.builder()
                .instrumentName(null)
                .transactionType(null)
                .entryPrice(null)
                .stopLoss(null)
                .target1(null)
                .build();
        List<String> errors = validator.validate(signal);
        assertTrue(errors.size() >= 5, "Expected at least 5 errors but got " + errors.size());
    }

    @Test
    void shouldFilterValidSignalsFromList() {
        TradeSignal valid = validBuySignal().build();
        TradeSignal invalid = validBuySignal().stopLoss(null).build();
        TradeSignal alsoInvalid = validBuySignal().entryPrice(null).build();

        List<TradeSignal> result = validator.filterValid(List.of(valid, invalid, alsoInvalid), "test");
        assertEquals(1, result.size());
        assertEquals("NIFTY 24500CE", result.get(0).getInstrumentName());
    }

    @Test
    void shouldReturnEmptyListWhenAllInvalid() {
        TradeSignal invalid1 = validBuySignal().stopLoss(null).build();
        TradeSignal invalid2 = validBuySignal().target1(null).build();

        List<TradeSignal> result = validator.filterValid(List.of(invalid1, invalid2), "test");
        assertTrue(result.isEmpty());
    }

    @Test
    void shouldReturnAllWhenAllValid() {
        TradeSignal valid1 = validBuySignal().build();
        TradeSignal valid2 = validSellSignal().build();

        List<TradeSignal> result = validator.filterValid(List.of(valid1, valid2), "test");
        assertEquals(2, result.size());
    }
}
