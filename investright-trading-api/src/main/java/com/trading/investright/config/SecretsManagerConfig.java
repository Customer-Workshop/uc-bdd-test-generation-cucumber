package com.trading.investright.config;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.context.annotation.Configuration;
import software.amazon.awssdk.auth.credentials.DefaultCredentialsProvider;
import software.amazon.awssdk.regions.Region;
import software.amazon.awssdk.services.secretsmanager.SecretsManagerClient;
import software.amazon.awssdk.services.secretsmanager.model.GetSecretValueRequest;
import software.amazon.awssdk.services.secretsmanager.model.GetSecretValueResponse;

import jakarta.annotation.PostConstruct;
import java.util.Map;

@Slf4j
@Configuration
@ConditionalOnProperty(name = "aws.secrets-manager.enabled", havingValue = "true")
public class SecretsManagerConfig {

    @Value("${aws.secrets-manager.secret-name:investright/trading-api/credentials}")
    private String secretName;

    @Value("${aws.region:ap-south-1}")
    private String region;

    private final InvestRightProperties investRightProperties;
    private final SchedulerProperties schedulerProperties;

    public SecretsManagerConfig(InvestRightProperties investRightProperties,
                                SchedulerProperties schedulerProperties) {
        this.investRightProperties = investRightProperties;
        this.schedulerProperties = schedulerProperties;
    }

    @PostConstruct
    public void loadSecrets() {
        log.info("Loading credentials from AWS Secrets Manager: {}", secretName);
        try (SecretsManagerClient client = SecretsManagerClient.builder()
                .region(Region.of(region))
                .credentialsProvider(DefaultCredentialsProvider.create())
                .build()) {

            GetSecretValueResponse response = client.getSecretValue(
                    GetSecretValueRequest.builder()
                            .secretId(secretName)
                            .build());

            String secretJson = response.secretString();
            ObjectMapper mapper = new ObjectMapper();
            Map<String, String> secrets = mapper.readValue(secretJson, new TypeReference<>() {});

            applySecret(secrets, "IR_API_KEY", this::setApiKey);
            applySecret(secrets, "IR_API_SECRET", this::setApiSecret);
            applySecret(secrets, "IR_USERNAME", this::setUsername);
            applySecret(secrets, "IR_PASSWORD", this::setPassword);
            applySecret(secrets, "IR_2FA_ANSWER", this::setTwoFaAnswer);

            log.info("Successfully loaded {} credentials from Secrets Manager", secrets.size());
        } catch (Exception ex) {
            log.error("Failed to load secrets from AWS Secrets Manager: {}", ex.getMessage());
            log.warn("Falling back to environment variables / application.yml for credentials");
        }
    }

    private void applySecret(Map<String, String> secrets, String key, java.util.function.Consumer<String> setter) {
        String value = secrets.get(key);
        if (value != null && !value.isBlank()) {
            setter.accept(value);
            log.debug("Applied secret: {}", key);
        }
    }

    private void setApiKey(String value) {
        investRightProperties.setApiKey(value);
    }

    private void setApiSecret(String value) {
        investRightProperties.setApiSecret(value);
    }

    private void setUsername(String value) {
        schedulerProperties.setUsername(value);
    }

    private void setPassword(String value) {
        schedulerProperties.setPassword(value);
    }

    private void setTwoFaAnswer(String value) {
        schedulerProperties.setTwoFaAnswer(value);
    }
}
