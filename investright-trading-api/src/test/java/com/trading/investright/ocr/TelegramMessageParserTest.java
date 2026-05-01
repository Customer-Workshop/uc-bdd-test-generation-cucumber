package com.trading.investright.ocr;

import com.trading.investright.model.TradeSignal;
import com.trading.investright.model.TradeSignal.InstrumentType;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

class TelegramMessageParserTest {

    private TelegramMessageParser parser;

    @BeforeEach
    void setUp() {
        parser = new TelegramMessageParser();
    }

    @Test
    void shouldParseIndianBankPutOption() {
        String message = """
                HERO ZERO
                BUY INDIANB 820PE ABV 29 TGT
                30.50-32-35-45
                SL 27.50
                INTRADAY""";

        List<TradeSignal> signals = parser.parseMessage(message);

        assertEquals(1, signals.size());
        TradeSignal signal = signals.get(0);
        assertEquals("INDIANB", signal.getUnderlying());
        assertEquals(820.0, signal.getStrikePrice());
        assertEquals("PE", signal.getOptionType());
        assertEquals(InstrumentType.PUT_OPTION, signal.getInstrumentType());
        assertEquals("BUY", signal.getTransactionType());
        assertEquals(29.0, signal.getEntryPrice());
        assertEquals(27.50, signal.getStopLoss());
        assertEquals(30.50, signal.getTarget1());
        assertEquals(32.0, signal.getTarget2());
        assertEquals(35.0, signal.getTarget3());
        assertEquals(45.0, signal.getTarget4());
        assertEquals("NFO", signal.getExchange());
        assertEquals("telegram", signal.getSource());
    }

    @Test
    void shouldParseSensexPutOption() {
        String message = """
                HERO ZERO
                BUY SENSEX 76600PE ABV 200 TGT
                240-280-350
                SL 165
                INTRADAY""";

        List<TradeSignal> signals = parser.parseMessage(message);

        assertEquals(1, signals.size());
        TradeSignal signal = signals.get(0);
        assertEquals("SENSEX", signal.getUnderlying());
        assertEquals(76600.0, signal.getStrikePrice());
        assertEquals("PE", signal.getOptionType());
        assertEquals(InstrumentType.PUT_OPTION, signal.getInstrumentType());
        assertEquals("BUY", signal.getTransactionType());
        assertEquals(200.0, signal.getEntryPrice());
        assertEquals(165.0, signal.getStopLoss());
        assertEquals(240.0, signal.getTarget1());
        assertEquals(280.0, signal.getTarget2());
        assertEquals(350.0, signal.getTarget3());
        assertEquals("BFO", signal.getExchange());
    }

    @Test
    void shouldParseSensex76900PEOption() {
        String message = """
                HERO ZERO
                BUY SENSEX 76900PE ABV 400 TGT
                440-480-600
                SL 365
                INTRADAY""";

        List<TradeSignal> signals = parser.parseMessage(message);

        assertEquals(1, signals.size());
        TradeSignal signal = signals.get(0);
        assertEquals("SENSEX", signal.getUnderlying());
        assertEquals(76900.0, signal.getStrikePrice());
        assertEquals("PE", signal.getOptionType());
        assertEquals(400.0, signal.getEntryPrice());
        assertEquals(365.0, signal.getStopLoss());
        assertEquals(440.0, signal.getTarget1());
        assertEquals(480.0, signal.getTarget2());
        assertEquals(600.0, signal.getTarget3());
    }

    @Test
    void shouldParseCallOption() {
        String message = """
                BUY NIFTY 24500CE ABV 150 TGT
                180-200-230
                SL 120
                INTRADAY""";

        List<TradeSignal> signals = parser.parseMessage(message);

        assertEquals(1, signals.size());
        TradeSignal signal = signals.get(0);
        assertEquals("NIFTY", signal.getUnderlying());
        assertEquals(24500.0, signal.getStrikePrice());
        assertEquals("CE", signal.getOptionType());
        assertEquals(InstrumentType.CALL_OPTION, signal.getInstrumentType());
        assertEquals("BUY", signal.getTransactionType());
        assertEquals(150.0, signal.getEntryPrice());
        assertEquals(120.0, signal.getStopLoss());
        assertEquals("NFO", signal.getExchange());
    }

    @Test
    void shouldHandleEmptyMessage() {
        assertTrue(parser.parseMessage("").isEmpty());
        assertTrue(parser.parseMessage(null).isEmpty());
    }

    @Test
    void shouldSkipNonTradeMessages() {
        assertFalse(parser.isTradeSignalMessage("BANDHANBNK 8.70"));
        assertFalse(parser.isTradeSignalMessage("169"));
        assertFalse(parser.isTradeSignalMessage("some random text"));
    }

    @Test
    void shouldDetectTradeSignalMessages() {
        assertTrue(parser.isTradeSignalMessage("BUY INDIANB 820PE ABV 29 TGT"));
        assertTrue(parser.isTradeSignalMessage("SELL NIFTY 24000PE BLW 100 TGT"));
    }

    @Test
    void shouldParseBlockDirectly() {
        String block = "BUY RELIANCE 2800CE ABV 55 TGT\n65-75-90\nSL 45\nINTRADAY";
        TradeSignal signal = parser.parseBlock(block);

        assertNotNull(signal);
        assertEquals("RELIANCE", signal.getUnderlying());
        assertEquals(2800.0, signal.getStrikePrice());
        assertEquals("CE", signal.getOptionType());
        assertEquals(55.0, signal.getEntryPrice());
        assertEquals(45.0, signal.getStopLoss());
        assertEquals(65.0, signal.getTarget1());
        assertEquals(75.0, signal.getTarget2());
        assertEquals(90.0, signal.getTarget3());
    }

    @Test
    void shouldReturnNullForNonMatchingBlock() {
        assertNull(parser.parseBlock("just some random text"));
        assertNull(parser.parseBlock("BANDHANBNK 8.70"));
    }

    @Test
    void shouldHandleSellSignal() {
        String message = "SELL BANKNIFTY 52000PE BLW 300 TGT\n250-200-150\nSL 350\nINTRADAY";

        List<TradeSignal> signals = parser.parseMessage(message);

        assertEquals(1, signals.size());
        TradeSignal signal = signals.get(0);
        assertEquals("SELL", signal.getTransactionType());
        assertEquals("BANKNIFTY", signal.getUnderlying());
        assertEquals(52000.0, signal.getStrikePrice());
        assertEquals(300.0, signal.getEntryPrice());
        assertEquals(350.0, signal.getStopLoss());
    }

    @Test
    void shouldUseBfoForBankex() {
        String message = "BUY BANKEX 55000CE ABV 100 TGT\n120-140\nSL 80";

        List<TradeSignal> signals = parser.parseMessage(message);

        assertEquals(1, signals.size());
        assertEquals("BFO", signals.get(0).getExchange());
    }

    @Test
    void shouldSetInstrumentNameCorrectly() {
        String message = "BUY INDIANB 820PE ABV 29 TGT\n30-32-35\nSL 27";

        List<TradeSignal> signals = parser.parseMessage(message);

        assertEquals(1, signals.size());
        assertEquals("INDIANB 820PE", signals.get(0).getInstrumentName());
    }
}
