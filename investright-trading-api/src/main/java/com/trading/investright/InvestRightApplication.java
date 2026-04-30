package com.trading.investright;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling;

@SpringBootApplication
@EnableScheduling
public class InvestRightApplication {

    public static void main(String[] args) {
        SpringApplication.run(InvestRightApplication.class, args);
    }
}
