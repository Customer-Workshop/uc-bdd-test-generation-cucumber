package com.trading.investright.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

import java.util.ArrayList;
import java.util.List;

@Data
@Configuration
@ConfigurationProperties(prefix = "scheduler")
public class SchedulerProperties {

    private boolean enabled = false;
    private String cron = "0 55 8 * * *";
    private String timezone = "Asia/Kolkata";

    private String imageSource = "local";
    private String localFolderPath;
    private boolean useDateSubfolder = false;

    private String imageSourceUrl;
    private List<String> imageSourceUrls = new ArrayList<>();

    private String userId;
    private String username;
    private String password;
    private String twoFaAnswer;

    private boolean autoLogin = true;
    private int retryAttempts = 3;
    private long retryDelayMs = 2000;
}
