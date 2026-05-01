package com.trading.investright.service;

import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.HashMap;
import java.util.Map;

@Slf4j
@Service
public class SymbolMappingService {

    private static final Map<String, String> SYMBOL_MAP = new HashMap<>();

    static {
        SYMBOL_MAP.put("MAZDOCK", "MAZDOCK");
        SYMBOL_MAP.put("RECLTD", "RECLTD");
        SYMBOL_MAP.put("INDUSINDBNK", "INDUSINDBK");
        SYMBOL_MAP.put("RELIANCE", "RELIANCE");
        SYMBOL_MAP.put("TCS", "TCS");
        SYMBOL_MAP.put("INFY", "INFY");
        SYMBOL_MAP.put("HDFCBANK", "HDFCBANK");
        SYMBOL_MAP.put("ICICIBANK", "ICICIBANK");
        SYMBOL_MAP.put("SBIN", "SBIN");
        SYMBOL_MAP.put("TATAMOTORS", "TATAMTRS");
        SYMBOL_MAP.put("WIPRO", "WIPRO");
        SYMBOL_MAP.put("NIFTY", "NIFTY");
        SYMBOL_MAP.put("BANKNIFTY", "BANKNIFTY");
        SYMBOL_MAP.put("FINNIFTY", "FINNIFTY");
        SYMBOL_MAP.put("SENSEX", "SENSEX");
    }

    public String mapToSecurityId(String shortName) {
        if (shortName == null) return null;
        String normalized = shortName.toUpperCase().trim();
        return SYMBOL_MAP.getOrDefault(normalized, normalized);
    }

    public String constructOptionTradingSymbol(String underlying, String expiryDate, double strikePrice, String optionType) {
        String mappedUnderlying = mapToSecurityId(underlying);
        int strikeInt = (int) strikePrice;
        return String.format("%s%s%d%s", mappedUnderlying, expiryDate, strikeInt, optionType);
    }

    public String determineExchange(String instrumentType) {
        return switch (instrumentType) {
            case "OPTIDX", "OPTSTK", "FUTIDX", "FUTSTK" -> "NSE";
            case "OPTCUR", "FUTCUR" -> "NSE";
            default -> "NSE";
        };
    }

    public String determineInstrumentSegment(String underlying, String optionType, boolean isFuture) {
        boolean isIndex = isIndexSymbol(underlying);
        if (optionType != null) {
            return isIndex ? "OPTIDX" : "OPTSTK";
        }
        if (isFuture) {
            return isIndex ? "FUTIDX" : "FUTSTK";
        }
        return "EQUITY";
    }

    public boolean isIndexSymbol(String symbol) {
        if (symbol == null) return false;
        String upper = symbol.toUpperCase().trim();
        return upper.equals("NIFTY") || upper.equals("BANKNIFTY") ||
               upper.equals("FINNIFTY") || upper.equals("SENSEX") ||
               upper.equals("MIDCPNIFTY");
    }

    public String determineUnderlyingSymbol(String underlying) {
        String mapped = mapToSecurityId(underlying);
        return mapped + "EQEQNR";
    }
}
