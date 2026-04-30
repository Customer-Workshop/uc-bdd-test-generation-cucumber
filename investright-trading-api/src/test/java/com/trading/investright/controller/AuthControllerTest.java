package com.trading.investright.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.trading.investright.client.InvestRightAuthClient;
import com.trading.investright.config.SecurityConfig;
import com.trading.investright.model.request.LoginRequest;
import com.trading.investright.model.response.LoginResponse;
import com.trading.investright.model.response.TokenIdResponse;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.context.annotation.Import;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.when;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.csrf;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(AuthController.class)
@Import(SecurityConfig.class)
class AuthControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private InvestRightAuthClient authClient;

    @Autowired
    private ObjectMapper objectMapper;

    @Test
    void shouldFetchTokenId() throws Exception {
        when(authClient.fetchTokenId())
                .thenReturn(TokenIdResponse.builder().tokenId("test-token-123").build());

        mockMvc.perform(post("/api/auth/token")
                        .with(csrf()))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("success"))
                .andExpect(jsonPath("$.data.tokenId").value("test-token-123"));
    }

    @Test
    void shouldLoginWithCredentials() throws Exception {
        LoginResponse loginResponse = LoginResponse.builder()
                .loginId("12345")
                .twoFAEnabled(true)
                .build();
        when(authClient.loginWithCredentials(anyString(), anyString(), anyString()))
                .thenReturn(loginResponse);

        LoginRequest request = LoginRequest.builder()
                .username("testuser")
                .password("testpass")
                .build();

        mockMvc.perform(post("/api/auth/login")
                        .with(csrf())
                        .param("tokenId", "test-token")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("success"))
                .andExpect(jsonPath("$.data.loginId").value("12345"));
    }

    @Test
    void shouldRejectLoginWithoutUsername() throws Exception {
        LoginRequest request = LoginRequest.builder()
                .password("testpass")
                .build();

        mockMvc.perform(post("/api/auth/login")
                        .with(csrf())
                        .param("tokenId", "test-token")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isBadRequest());
    }
}
