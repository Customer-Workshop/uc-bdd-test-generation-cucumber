package com.trading.investright.service;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

class SymbolMappingServiceTest {

    private SymbolMappingService service;

    @BeforeEach
    void setUp() {
        service = new SymbolMappingService();
    }

    @Test
    void shouldMapKnownSymbol() {
        assertEquals("RELIANCE", service.mapToSecurityId("RELIANCE"));
        assertEquals("TCS", service.mapToSecurityId("tcs"));
        assertEquals("INFY", service.mapToSecurityId("Infy"));
    }

    @Test
    void shouldReturnOriginalForUnknownSymbol() {
        assertEquals("UNKNOWNSYMBOL", service.mapToSecurityId("UnknownSymbol"));
    }

    @Test
    void shouldConstructOptionTradingSymbol() {
        String symbol = service.constructOptionTradingSymbol("MAZDOCK", "20240425", 2760.0, "CE");
        assertEquals("MAZDOCK202404252760CE", symbol);
    }

    @Test
    void shouldDetermineInstrumentSegmentForIndexOption() {
        assertEquals("OPTIDX", service.determineInstrumentSegment("NIFTY", "CE", false));
        assertEquals("OPTIDX", service.determineInstrumentSegment("BANKNIFTY", "PE", false));
    }

    @Test
    void shouldDetermineInstrumentSegmentForStockOption() {
        assertEquals("OPTSTK", service.determineInstrumentSegment("RELIANCE", "CE", false));
    }

    @Test
    void shouldDetermineInstrumentSegmentForEquity() {
        assertEquals("EQUITY", service.determineInstrumentSegment("RELIANCE", null, false));
    }

    @Test
    void shouldDetermineInstrumentSegmentForIndexFuture() {
        assertEquals("FUTIDX", service.determineInstrumentSegment("NIFTY", null, true));
    }

    @Test
    void shouldDetermineInstrumentSegmentForStockFuture() {
        assertEquals("FUTSTK", service.determineInstrumentSegment("RELIANCE", null, true));
    }

    @Test
    void shouldIdentifyIndexSymbol() {
        assertTrue(service.isIndexSymbol("NIFTY"));
        assertTrue(service.isIndexSymbol("BANKNIFTY"));
        assertTrue(service.isIndexSymbol("FINNIFTY"));
        assertFalse(service.isIndexSymbol("RELIANCE"));
        assertFalse(service.isIndexSymbol("TCS"));
    }

    @Test
    void shouldDetermineExchange() {
        assertEquals("NSE", service.determineExchange("OPTIDX"));
        assertEquals("NSE", service.determineExchange("EQUITY"));
    }

    @Test
    void shouldDetermineUnderlyingSymbol() {
        assertEquals("NIFTYEQEQNR", service.determineUnderlyingSymbol("NIFTY"));
        assertEquals("RELIANCEEQEQNR", service.determineUnderlyingSymbol("RELIANCE"));
    }
}
