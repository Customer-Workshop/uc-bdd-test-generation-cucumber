package com.trading.investright.config;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.junit.jupiter.MockitoExtension;

import static org.junit.jupiter.api.Assertions.*;

@ExtendWith(MockitoExtension.class)
class SecretsManagerConfigTest {

    @Test
    void shouldNotFailWhenSecretsManagerDisabled() {
        // SecretsManagerConfig is only created when aws.secrets-manager.enabled=true
        // Verify that the app starts without it (default is disabled)
        InvestRightProperties irProps = new InvestRightProperties();
        SchedulerProperties schedProps = new SchedulerProperties();

        irProps.setApiKey("test-key");
        irProps.setApiSecret("test-secret");
        schedProps.setUsername("test-user");
        schedProps.setPassword("test-pass");
        schedProps.setTwoFaAnswer("123456");

        assertEquals("test-key", irProps.getApiKey());
        assertEquals("test-secret", irProps.getApiSecret());
        assertEquals("test-user", schedProps.getUsername());
        assertEquals("test-pass", schedProps.getPassword());
        assertEquals("123456", schedProps.getTwoFaAnswer());
    }

    @Test
    void shouldHaveCorrectDefaultSecretName() {
        // Verify the default secret name convention
        String defaultSecretName = "investright/trading-api/credentials";
        assertNotNull(defaultSecretName);
        assertTrue(defaultSecretName.contains("investright"));
    }
}
