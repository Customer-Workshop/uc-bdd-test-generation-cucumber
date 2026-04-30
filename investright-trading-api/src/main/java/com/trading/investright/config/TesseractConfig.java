package com.trading.investright.config;

import lombok.RequiredArgsConstructor;
import net.sourceforge.tess4j.Tesseract;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
@RequiredArgsConstructor
public class TesseractConfig {

    private final TesseractProperties tesseractProperties;

    @Bean
    public Tesseract tesseract() {
        Tesseract tesseract = new Tesseract();
        tesseract.setDatapath(tesseractProperties.getDataPath());
        tesseract.setLanguage(tesseractProperties.getLanguage());
        tesseract.setPageSegMode(6); // Assume uniform block of text
        tesseract.setOcrEngineMode(1); // LSTM neural net mode
        return tesseract;
    }
}
