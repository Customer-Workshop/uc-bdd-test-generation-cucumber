package com.trading.investright.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

@Data
@Configuration
@ConfigurationProperties(prefix = "aws")
public class AwsProperties {

    private String region = "ap-south-1";
    private S3Properties s3 = new S3Properties();

    @Data
    public static class S3Properties {
        private String bucketName;
        private String prefix = "trade-signals/";
    }
}
