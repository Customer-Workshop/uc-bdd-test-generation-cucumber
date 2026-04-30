package com.trading.investright.config;

import lombok.RequiredArgsConstructor;
import net.sourceforge.tess4j.Tesseract;
import org.springframework.beans.factory.config.ConfigurableBeanFactory;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Scope;

@Configuration
@RequiredArgsConstructor
public class TesseractConfig {

    private final TesseractProperties tesseractProperties;

    @Bean
    @Scope(ConfigurableBeanFactory.SCOPE_PROTOTYPE)
    public Tesseract tesseract() {
        Tesseract tesseract = new Tesseract();
        tesseract.setDatapath(tesseractProperties.getDataPath());
        tesseract.setLanguage(tesseractProperties.getLanguage());
        tesseract.setPageSegMode(6);
        tesseract.setOcrEngineMode(1);
        return tesseract;
    }
}
