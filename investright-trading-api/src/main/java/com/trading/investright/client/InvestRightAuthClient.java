package com.trading.investright.client;

import com.trading.investright.config.InvestRightProperties;
import com.trading.investright.exception.AuthenticationException;
import com.trading.investright.exception.InvestRightApiException;
import com.trading.investright.model.AuthSession;
import com.trading.investright.model.response.AccessTokenResponse;
import com.trading.investright.model.response.AuthorizeResponse;
import com.trading.investright.model.response.LoginResponse;
import com.trading.investright.model.response.TokenIdResponse;
import com.trading.investright.model.response.TwoFaResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.reactive.function.client.WebClientResponseException;
import reactor.core.publisher.Mono;

import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

@Slf4j
@Component
@RequiredArgsConstructor
public class InvestRightAuthClient {

    private final WebClient investRightWebClient;
    private final InvestRightProperties properties;
    private final ConcurrentHashMap<String, AuthSession> sessions = new ConcurrentHashMap<>();

    public TokenIdResponse fetchTokenId() {
        log.debug("Fetching token ID from InvestRight");
        try {
            return investRightWebClient.get()
                    .uri(uriBuilder -> uriBuilder
                            .path("/login")
                            .queryParam("api_key", properties.getApiKey())
                            .build())
                    .retrieve()
                    .bodyToMono(TokenIdResponse.class)
                    .block();
        } catch (WebClientResponseException ex) {
            throw new InvestRightApiException("Failed to fetch token ID", ex.getStatusCode().value(), ex.getResponseBodyAsString());
        }
    }

    public LoginResponse loginWithCredentials(String username, String password, String tokenId) {
        log.debug("Logging in with credentials for token: {}", tokenId);
        try {
            return investRightWebClient.post()
                    .uri(uriBuilder -> uriBuilder
                            .path("/login/validate")
                            .queryParam("api_key", properties.getApiKey())
                            .queryParam("token_id", tokenId)
                            .build())
                    .bodyValue(Map.of("username", username, "password", password))
                    .retrieve()
                    .bodyToMono(LoginResponse.class)
                    .block();
        } catch (WebClientResponseException ex) {
            throw new AuthenticationException("Login failed: " + ex.getResponseBodyAsString());
        }
    }

    public TwoFaResponse validateTwoFa(String answer, String tokenId) {
        log.debug("Validating 2FA for token: {}", tokenId);
        try {
            return investRightWebClient.post()
                    .uri(uriBuilder -> uriBuilder
                            .path("/twofa/validate")
                            .queryParam("api_key", properties.getApiKey())
                            .queryParam("token_id", tokenId)
                            .build())
                    .bodyValue(Map.of("answer", answer))
                    .retrieve()
                    .bodyToMono(TwoFaResponse.class)
                    .block();
        } catch (WebClientResponseException ex) {
            throw new AuthenticationException("2FA validation failed: " + ex.getResponseBodyAsString());
        }
    }

    public AuthorizeResponse authorize(String tokenId, String requestToken, boolean consent) {
        log.debug("Authorizing for token: {}", tokenId);
        try {
            return investRightWebClient.get()
                    .uri(uriBuilder -> uriBuilder
                            .path("/authorise")
                            .queryParam("api_key", properties.getApiKey())
                            .queryParam("token_id", tokenId)
                            .queryParam("consent", consent)
                            .queryParam("request_token", requestToken)
                            .build())
                    .retrieve()
                    .bodyToMono(AuthorizeResponse.class)
                    .block();
        } catch (WebClientResponseException ex) {
            throw new AuthenticationException("Authorization failed: " + ex.getResponseBodyAsString());
        }
    }

    public AccessTokenResponse fetchAccessToken(String requestToken) {
        log.debug("Fetching access token");
        try {
            return investRightWebClient.post()
                    .uri(uriBuilder -> uriBuilder
                            .path("/access-token")
                            .queryParam("api_key", properties.getApiKey())
                            .queryParam("request_token", requestToken)
                            .build())
                    .bodyValue(Map.of("apiSecret", properties.getApiSecret()))
                    .retrieve()
                    .bodyToMono(AccessTokenResponse.class)
                    .block();
        } catch (WebClientResponseException ex) {
            throw new AuthenticationException("Failed to fetch access token: " + ex.getResponseBodyAsString());
        }
    }

    public Mono<Void> resendTwoFaCode(String tokenId) {
        log.debug("Resending 2FA code for token: {}", tokenId);
        return investRightWebClient.get()
                .uri(uriBuilder -> uriBuilder
                        .path("/twofa/resend")
                        .queryParam("api_key", properties.getApiKey())
                        .queryParam("token_id", tokenId)
                        .build())
                .retrieve()
                .bodyToMono(Void.class);
    }

    public void storeSession(String userId, AuthSession session) {
        sessions.put(userId, session);
    }

    public AuthSession getSession(String userId) {
        AuthSession session = sessions.get(userId);
        if (session == null) {
            throw new AuthenticationException("No active session found. Please login first.");
        }
        if (session.isExpired()) {
            sessions.remove(userId);
            throw new AuthenticationException("Session expired. Please login again.");
        }
        return session;
    }

    public String getAccessToken(String userId) {
        return getSession(userId).getAccessToken();
    }

    public AuthSession performFullLogin(String username, String password, String twoFaAnswer) {
        TokenIdResponse tokenIdResponse = fetchTokenId();
        String tokenId = tokenIdResponse.getTokenId();

        LoginResponse loginResponse = loginWithCredentials(username, password, tokenId);

        TwoFaResponse twoFaResponse = validateTwoFa(twoFaAnswer, tokenId);
        String requestToken = twoFaResponse.getRequestToken();

        AuthorizeResponse authorizeResponse = authorize(tokenId, requestToken, true);
        String authorizedRequestToken = authorizeResponse.getRequestToken();

        AccessTokenResponse accessTokenResponse = fetchAccessToken(authorizedRequestToken);

        AuthSession session = AuthSession.builder()
                .tokenId(tokenId)
                .loginId(loginResponse.getLoginId())
                .requestToken(authorizedRequestToken)
                .accessToken(accessTokenResponse.getAccessToken())
                .createdAt(Instant.now())
                .expiresAt(Instant.now().plus(8, ChronoUnit.HOURS))
                .build();

        storeSession(username, session);
        return session;
    }
}
