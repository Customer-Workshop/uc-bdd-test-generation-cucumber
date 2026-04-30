package com.trading.investright.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

@Data
@Configuration
@ConfigurationProperties(prefix = "trading")
public class TradingProperties {

    private int defaultLotSize = 1;
    private double capitalPerTrade = 100000.0;
    private String defaultProduct = "INTRADAY";
    private String defaultValidity = "DAY";
    private double slippagePercent = 0.5;
    private double trailingSlBufferPercent = 2.0;
}
