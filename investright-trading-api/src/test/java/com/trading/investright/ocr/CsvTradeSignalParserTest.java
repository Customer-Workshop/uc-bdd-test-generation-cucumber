package com.trading.investright.ocr;

import com.trading.investright.model.TradeSignal;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

class CsvTradeSignalParserTest {

    private CsvTradeSignalParser parser;

    @TempDir
    Path tempDir;

    @BeforeEach
    void setUp() {
        parser = new CsvTradeSignalParser();
    }

    @Test
    void shouldParseSimpleCsvWithHeaders() throws IOException {
        String csv = """
                Symbol,Entry,SL,Target,Type
                RELIANCE,2500,2450,2600,BUY
                TCS,3800,3750,3900,BUY
                INFY,1500,1530,1450,SELL
                """;
        Path csvFile = tempDir.resolve("signals.csv");
        Files.writeString(csvFile, csv);

        List<TradeSignal> signals = parser.parseCsvFile(csvFile.toString());

        assertEquals(3, signals.size());

        assertEquals("RELIANCE", signals.get(0).getInstrumentName());
        assertEquals(2500.0, signals.get(0).getEntryPrice());
        assertEquals(2450.0, signals.get(0).getStopLoss());
        assertEquals(2600.0, signals.get(0).getTarget1());
        assertEquals("BUY", signals.get(0).getTransactionType());
        assertEquals(TradeSignal.InstrumentType.EQUITY, signals.get(0).getInstrumentType());

        assertEquals("INFY", signals.get(2).getInstrumentName());
        assertEquals("SELL", signals.get(2).getTransactionType());
    }

    @Test
    void shouldParseOptionsFromCsv() throws IOException {
        String csv = """
                Symbol,Entry,SL,Target,Type
                NIFTY 22400CE,150,120,180,BUY
                BANKNIFTY 48000PE,200,230,160,SELL
                """;
        Path csvFile = tempDir.resolve("options.csv");
        Files.writeString(csvFile, csv);

        List<TradeSignal> signals = parser.parseCsvFile(csvFile.toString());

        assertEquals(2, signals.size());

        assertEquals(TradeSignal.InstrumentType.CALL_OPTION, signals.get(0).getInstrumentType());
        assertEquals("NIFTY", signals.get(0).getUnderlying());
        assertEquals(22400.0, signals.get(0).getStrikePrice());
        assertEquals("CE", signals.get(0).getOptionType());

        assertEquals(TradeSignal.InstrumentType.PUT_OPTION, signals.get(1).getInstrumentType());
        assertEquals("BANKNIFTY", signals.get(1).getUnderlying());
        assertEquals("PE", signals.get(1).getOptionType());
    }

    @Test
    void shouldHandleAlternateHeaderNames() throws IOException {
        String csv = """
                Instrument Name,Buy Above,Stop Loss,TGT1,TGT2,Action
                MAZDOCK,5200,5100,5350,5500,BUY
                """;
        Path csvFile = tempDir.resolve("alt-headers.csv");
        Files.writeString(csvFile, csv);

        List<TradeSignal> signals = parser.parseCsvFile(csvFile.toString());

        assertEquals(1, signals.size());
        assertEquals("MAZDOCK", signals.get(0).getUnderlying());
    }

    @Test
    void shouldHandleMultipleTargets() throws IOException {
        String csv = """
                Symbol,Entry,SL,Target1,Target2,Target3,Type
                RELIANCE,2500,2450,2550,2600,2700,BUY
                """;
        Path csvFile = tempDir.resolve("targets.csv");
        Files.writeString(csvFile, csv);

        List<TradeSignal> signals = parser.parseCsvFile(csvFile.toString());

        assertEquals(1, signals.size());
        assertEquals(2550.0, signals.get(0).getTarget1());
        assertEquals(2600.0, signals.get(0).getTarget2());
        assertEquals(2700.0, signals.get(0).getTarget3());
    }

    @Test
    void shouldHandleEmptyCsvFile() throws IOException {
        Path csvFile = tempDir.resolve("empty.csv");
        Files.writeString(csvFile, "");

        List<TradeSignal> signals = parser.parseCsvFile(csvFile.toString());
        assertTrue(signals.isEmpty());
    }

    @Test
    void shouldHandleMissingFile() {
        List<TradeSignal> signals = parser.parseCsvFile("/nonexistent/file.csv");
        assertTrue(signals.isEmpty());
    }

    @Test
    void shouldParseCsvFilesFromFolder() throws IOException {
        String csv1 = """
                Symbol,Entry,SL,Target,Type
                RELIANCE,2500,2450,2600,BUY
                """;
        String csv2 = """
                Symbol,Entry,SL,Target,Type
                TCS,3800,3750,3900,BUY
                """;
        Files.writeString(tempDir.resolve("signals1.csv"), csv1);
        Files.writeString(tempDir.resolve("signals2.csv"), csv2);
        Files.writeString(tempDir.resolve("ignore.txt"), "not a csv");

        List<TradeSignal> signals = parser.parseCsvFilesFromFolder(tempDir.toString());

        assertEquals(2, signals.size());
    }

    @Test
    void shouldDefaultToBuyWhenNoTypeColumn() throws IOException {
        String csv = """
                Symbol,Entry,SL,Target
                RELIANCE,2500,2450,2600
                """;
        Path csvFile = tempDir.resolve("no-type.csv");
        Files.writeString(csvFile, csv);

        List<TradeSignal> signals = parser.parseCsvFile(csvFile.toString());

        assertEquals(1, signals.size());
        assertEquals("BUY", signals.get(0).getTransactionType());
    }

    @Test
    void shouldHandleQuotedCsvValues() throws IOException {
        String csv = """
                Symbol,Entry,SL,Target,Type
                "RELIANCE",2500,2450,2600,"BUY"
                """;
        Path csvFile = tempDir.resolve("quoted.csv");
        Files.writeString(csvFile, csv);

        List<TradeSignal> signals = parser.parseCsvFile(csvFile.toString());

        assertEquals(1, signals.size());
        assertEquals("RELIANCE", signals.get(0).getInstrumentName());
    }
}
