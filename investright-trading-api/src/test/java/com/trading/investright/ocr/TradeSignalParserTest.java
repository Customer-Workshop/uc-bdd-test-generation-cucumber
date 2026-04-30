package com.trading.investright.ocr;

import com.trading.investright.model.TradeSignal;
import com.trading.investright.model.TradeSignal.InstrumentType;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

class TradeSignalParserTest {

    private TradeSignalParser parser;

    @BeforeEach
    void setUp() {
        parser = new TradeSignalParser();
    }

    @Test
    void shouldParseCallOption() {
        String ocrText = "MAZDOCK 2760CE BUY ABOVE 150 SL 120 TGT 180 200 220";
        List<TradeSignal> signals = parser.parseOcrText(ocrText);

        assertFalse(signals.isEmpty());
        TradeSignal signal = signals.get(0);
        assertEquals("MAZDOCK", signal.getUnderlying());
        assertEquals(2760.0, signal.getStrikePrice());
        assertEquals("CE", signal.getOptionType());
        assertEquals(InstrumentType.CALL_OPTION, signal.getInstrumentType());
        assertEquals("BUY", signal.getTransactionType());
        assertEquals(150.0, signal.getEntryPrice());
        assertEquals(120.0, signal.getStopLoss());
    }

    @Test
    void shouldParsePutOption() {
        String ocrText = "RECLTD 370PE SELL BELOW 45 SL 55 TARGET 35 25";
        List<TradeSignal> signals = parser.parseOcrText(ocrText);

        assertFalse(signals.isEmpty());
        TradeSignal signal = signals.get(0);
        assertEquals("RECLTD", signal.getUnderlying());
        assertEquals(370.0, signal.getStrikePrice());
        assertEquals("PE", signal.getOptionType());
        assertEquals(InstrumentType.PUT_OPTION, signal.getInstrumentType());
        assertEquals("SELL", signal.getTransactionType());
        assertEquals(45.0, signal.getEntryPrice());
    }

    @Test
    void shouldParseEquity() {
        String ocrText = "RELIANCE BUY ABOVE 2500 SL 2450 TGT 2550 2600";
        List<TradeSignal> signals = parser.parseOcrText(ocrText);

        assertFalse(signals.isEmpty());
        TradeSignal signal = signals.get(0);
        assertEquals("RELIANCE", signal.getUnderlying());
        assertEquals(InstrumentType.EQUITY, signal.getInstrumentType());
        assertEquals("BUY", signal.getTransactionType());
        assertEquals(2500.0, signal.getEntryPrice());
        assertEquals(2450.0, signal.getStopLoss());
    }

    @Test
    void shouldParseMultipleLines() {
        String ocrText = """
                MAZDOCK 2760CE BUY ABOVE 150 SL 120 TGT 180
                RECLTD 370PE SELL BELOW 45 SL 55 TARGET 35
                RELIANCE BUY ABOVE 2500 SL 2450 TGT 2550
                """;
        List<TradeSignal> signals = parser.parseOcrText(ocrText);
        assertEquals(3, signals.size());
    }

    @Test
    void shouldHandleEmptyText() {
        List<TradeSignal> signals = parser.parseOcrText("");
        assertTrue(signals.isEmpty());
    }

    @Test
    void shouldHandleMalformedText() {
        List<TradeSignal> signals = parser.parseOcrText("some random garbage text 123 456");
        // Should not crash; may return empty or partial results
        assertNotNull(signals);
    }

    @Test
    void shouldParseInstrumentTypeCorrectly() {
        TradeSignal.TradeSignalBuilder builder = TradeSignal.builder();

        parser.parseInstrumentType("MAZDOCK 2760CE", builder);
        TradeSignal signal = builder.build();

        assertEquals("MAZDOCK", signal.getUnderlying());
        assertEquals(2760.0, signal.getStrikePrice());
        assertEquals("CE", signal.getOptionType());
        assertEquals(InstrumentType.CALL_OPTION, signal.getInstrumentType());
    }

    @Test
    void shouldParseEquityInstrumentType() {
        TradeSignal.TradeSignalBuilder builder = TradeSignal.builder();

        parser.parseInstrumentType("RELIANCE", builder);
        TradeSignal signal = builder.build();

        assertEquals("RELIANCE", signal.getUnderlying());
        assertEquals(InstrumentType.EQUITY, signal.getInstrumentType());
        assertNull(signal.getOptionType());
    }

    @Test
    void shouldParseBuyAbovePrice() {
        TradeSignal signal = parser.parseLine("INFY BUY ABOVE 1500 SL 1470", "");
        assertNotNull(signal);
        assertEquals("BUY", signal.getTransactionType());
        assertEquals(1500.0, signal.getEntryPrice());
    }

    @Test
    void shouldParseSellBelowPrice() {
        TradeSignal signal = parser.parseLine("SBIN SELL BELOW 600 SL 620", "");
        assertNotNull(signal);
        assertEquals("SELL", signal.getTransactionType());
        assertEquals(600.0, signal.getEntryPrice());
    }

    @Test
    void shouldParseDatePrefixedLine() {
        String ocrText = "29-04-2026 MAZDOCK 2760CE BUY ABOVE 153 SL 135 TGT 160 175 190";
        List<TradeSignal> signals = parser.parseOcrText(ocrText);

        assertFalse(signals.isEmpty());
        TradeSignal signal = signals.get(0);
        assertEquals("MAZDOCK", signal.getUnderlying());
        assertEquals(2760.0, signal.getStrikePrice());
        assertEquals("CE", signal.getOptionType());
        assertEquals("BUY", signal.getTransactionType());
        assertEquals(153.0, signal.getEntryPrice());
    }

    @Test
    void shouldParseSlashSeparatedTargets() {
        String ocrText = "MAZDOCK 2760CE BUY ABOVE 153 SL 135 160/175/190";
        List<TradeSignal> signals = parser.parseOcrText(ocrText);

        assertFalse(signals.isEmpty());
        TradeSignal signal = signals.get(0);
        assertEquals(160.0, signal.getTarget1());
        assertEquals(175.0, signal.getTarget2());
        assertEquals(190.0, signal.getTarget3());
    }

    @Test
    void shouldInferStopLossFromContext() {
        String ocrText = "MAZDOCK 2760CE BUY ABOVE 153 135 160/175/190";
        List<TradeSignal> signals = parser.parseOcrText(ocrText);

        assertFalse(signals.isEmpty());
        TradeSignal signal = signals.get(0);
        assertEquals(153.0, signal.getEntryPrice());
        assertEquals(135.0, signal.getStopLoss());
    }

    @Test
    void shouldParseSampleImageFormat() {
        String ocrText = """
                29-04-2026 MAZDOCK 2760CE BUY ABOVE 153 135 160/175/190
                29-04-2026 INDUSINDBNK 900CE BUY ABOVE 37 33 39/42/45
                29-04-2026 RECLTD 370PE BUY ABOVE 18.75 17.25 19.75/21/23
                29-04-2026 RBLBANK 330CE BUY ABOVE 153 14 15.5/16.2/17
                29-04-2026 ABCAPITAL 345CE BUY ABOVE 19.2 18.2 19.6/20.4/21.2
                29-04-2026 CROMPTON 270CE BUY ABOVE 18.5 17 19.5/21/22.5
                """;
        List<TradeSignal> signals = parser.parseOcrText(ocrText);

        assertEquals(6, signals.size());

        assertEquals("MAZDOCK", signals.get(0).getUnderlying());
        assertEquals(2760.0, signals.get(0).getStrikePrice());
        assertEquals("BUY", signals.get(0).getTransactionType());
        assertEquals(153.0, signals.get(0).getEntryPrice());

        assertEquals("INDUSINDBNK", signals.get(1).getUnderlying());
        assertEquals(900.0, signals.get(1).getStrikePrice());
        assertEquals("CE", signals.get(1).getOptionType());
        assertEquals(37.0, signals.get(1).getEntryPrice());

        assertEquals("RECLTD", signals.get(2).getUnderlying());
        assertEquals("PE", signals.get(2).getOptionType());
        assertEquals(18.75, signals.get(2).getEntryPrice());
    }
}
