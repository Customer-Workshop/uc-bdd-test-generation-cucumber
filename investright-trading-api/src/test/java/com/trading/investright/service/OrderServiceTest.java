package com.trading.investright.service;

import com.trading.investright.client.InvestRightAuthClient;
import com.trading.investright.client.InvestRightOrderClient;
import com.trading.investright.config.TradingProperties;
import com.trading.investright.model.TradeSignal;
import com.trading.investright.model.request.OrderRequest;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class OrderServiceTest {

    @Mock
    private InvestRightOrderClient orderClient;

    @Mock
    private InvestRightAuthClient authClient;

    @Mock
    private SymbolMappingService symbolMappingService;

    @Mock
    private TradingProperties tradingProperties;

    @InjectMocks
    private OrderService orderService;

    @Test
    void shouldCalculateQuantityFromCapitalPerTrade() {
        when(tradingProperties.getCapitalPerTrade()).thenReturn(100000.0);
        when(tradingProperties.getDefaultValidity()).thenReturn("DAY");
        when(tradingProperties.getSlippagePercent()).thenReturn(0.5);
        when(symbolMappingService.mapToSecurityId("RELIANCE")).thenReturn("RELIANCE");

        TradeSignal signal = TradeSignal.builder()
                .instrumentName("RELIANCE")
                .underlying("RELIANCE")
                .instrumentType(TradeSignal.InstrumentType.EQUITY)
                .transactionType("BUY")
                .entryPrice(2500.0)
                .build();

        OrderRequest order = orderService.buildOrderFromSignal(signal, null);

        assertEquals(40, order.getQuantity());
    }

    @Test
    void shouldCalculateQuantityForOptions() {
        when(tradingProperties.getCapitalPerTrade()).thenReturn(100000.0);
        when(tradingProperties.getDefaultValidity()).thenReturn("DAY");
        when(tradingProperties.getSlippagePercent()).thenReturn(0.5);
        when(symbolMappingService.determineInstrumentSegment("MAZDOCK", "CE", false)).thenReturn("OPTSTK");
        when(symbolMappingService.mapToSecurityId("MAZDOCK")).thenReturn("MAZDOCK");
        when(symbolMappingService.determineUnderlyingSymbol("MAZDOCK")).thenReturn("MAZDOCKEQEQNR");

        TradeSignal signal = TradeSignal.builder()
                .instrumentName("MAZDOCK 2760CE")
                .underlying("MAZDOCK")
                .strikePrice(2760.0)
                .optionType("CE")
                .instrumentType(TradeSignal.InstrumentType.CALL_OPTION)
                .transactionType("BUY")
                .entryPrice(153.0)
                .build();

        OrderRequest order = orderService.buildOrderFromSignal(signal, null);

        assertEquals(653, order.getQuantity());
    }

    @Test
    void shouldUseQuantityOverrideWhenProvided() {
        when(tradingProperties.getDefaultValidity()).thenReturn("DAY");
        when(tradingProperties.getSlippagePercent()).thenReturn(0.5);
        when(symbolMappingService.mapToSecurityId("RELIANCE")).thenReturn("RELIANCE");

        TradeSignal signal = TradeSignal.builder()
                .instrumentName("RELIANCE")
                .underlying("RELIANCE")
                .instrumentType(TradeSignal.InstrumentType.EQUITY)
                .transactionType("BUY")
                .entryPrice(2500.0)
                .build();

        OrderRequest order = orderService.buildOrderFromSignal(signal, 25);

        assertEquals(25, order.getQuantity());
    }

    @Test
    void shouldDefaultToLotSizeWhenNoEntryPrice() {
        when(tradingProperties.getDefaultLotSize()).thenReturn(1);
        when(tradingProperties.getDefaultValidity()).thenReturn("DAY");
        when(symbolMappingService.mapToSecurityId("RELIANCE")).thenReturn("RELIANCE");

        TradeSignal signal = TradeSignal.builder()
                .instrumentName("RELIANCE")
                .underlying("RELIANCE")
                .instrumentType(TradeSignal.InstrumentType.EQUITY)
                .transactionType("BUY")
                .build();

        OrderRequest order = orderService.buildOrderFromSignal(signal, null);

        assertEquals(1, order.getQuantity());
    }

    @Test
    void shouldEnsureMinimumQuantityOfOne() {
        when(tradingProperties.getCapitalPerTrade()).thenReturn(100.0);
        when(tradingProperties.getDefaultValidity()).thenReturn("DAY");
        when(tradingProperties.getSlippagePercent()).thenReturn(0.5);
        when(symbolMappingService.mapToSecurityId("RELIANCE")).thenReturn("RELIANCE");

        TradeSignal signal = TradeSignal.builder()
                .instrumentName("RELIANCE")
                .underlying("RELIANCE")
                .instrumentType(TradeSignal.InstrumentType.EQUITY)
                .transactionType("BUY")
                .entryPrice(50000.0)
                .build();

        OrderRequest order = orderService.buildOrderFromSignal(signal, null);

        assertEquals(1, order.getQuantity());
    }
}
