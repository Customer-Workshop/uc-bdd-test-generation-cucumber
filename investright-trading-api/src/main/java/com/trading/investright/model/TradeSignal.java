package com.trading.investright.model;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class TradeSignal {

    private String date;
    private String instrumentName;
    private String underlying;
    private Double strikePrice;
    private String optionType;
    private InstrumentType instrumentType;
    private String transactionType;
    private Double entryPrice;
    private Double stopLoss;
    private Double target1;
    private Double target2;
    private Double target3;
    private Double target4;
    private String exchange;
    private String tradingSymbol;
    private String rawText;
    private String source;
    private Double capitalPerTrade;

    public enum InstrumentType {
        EQUITY,
        CALL_OPTION,
        PUT_OPTION
    }
}
