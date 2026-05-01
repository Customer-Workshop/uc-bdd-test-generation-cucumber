package com.trading.investright.config;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import software.amazon.awssdk.auth.credentials.DefaultCredentialsProvider;
import software.amazon.awssdk.regions.Region;
import software.amazon.awssdk.services.textract.TextractClient;

@Slf4j
@Configuration
@RequiredArgsConstructor
public class TextractConfig {

    private final AwsProperties awsProperties;

    @Bean
    public TextractClient textractClient() {
        log.info("Initializing AWS Textract client for region: {}", awsProperties.getRegion());
        return TextractClient.builder()
                .region(Region.of(awsProperties.getRegion()))
                .credentialsProvider(DefaultCredentialsProvider.create())
                .build();
    }
}
