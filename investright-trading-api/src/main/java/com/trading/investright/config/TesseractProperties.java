package com.trading.investright.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

@Data
@Configuration
@ConfigurationProperties(prefix = "tesseract")
public class TesseractProperties {

    private String dataPath;
    private String language = "eng";
}
