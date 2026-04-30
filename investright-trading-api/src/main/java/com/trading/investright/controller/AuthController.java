package com.trading.investright.controller;

import com.trading.investright.client.InvestRightAuthClient;
import com.trading.investright.model.AuthSession;
import com.trading.investright.model.request.LoginRequest;
import com.trading.investright.model.request.MpinLoginRequest;
import com.trading.investright.model.request.TwoFaRequest;
import com.trading.investright.model.response.AccessTokenResponse;
import com.trading.investright.model.response.ApiResponse;
import com.trading.investright.model.response.AuthorizeResponse;
import com.trading.investright.model.response.LoginResponse;
import com.trading.investright.model.response.TokenIdResponse;
import com.trading.investright.model.response.TwoFaResponse;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@RestController
@RequestMapping("/api/auth")
@RequiredArgsConstructor
@Tag(name = "Authentication", description = "InvestRight authentication endpoints")
public class AuthController {

    private final InvestRightAuthClient authClient;

    @PostMapping("/token")
    @Operation(summary = "Fetch Token ID", description = "Fetches a token ID for initiating the login flow")
    public ResponseEntity<ApiResponse<TokenIdResponse>> fetchTokenId() {
        TokenIdResponse response = authClient.fetchTokenId();
        return ResponseEntity.ok(ApiResponse.success(response));
    }

    @PostMapping("/login")
    @Operation(summary = "Login with credentials", description = "Authenticate with username and password. Returns 2FA info if enabled.")
    public ResponseEntity<ApiResponse<LoginResponse>> login(
            @Valid @RequestBody LoginRequest request,
            @RequestParam String tokenId) {
        LoginResponse response = authClient.loginWithCredentials(
                request.getUsername(), request.getPassword(), tokenId);
        return ResponseEntity.ok(ApiResponse.success(response));
    }

    @PostMapping("/login-mpin")
    @Operation(summary = "Login with MPIN", description = "Authenticate with client ID and MPIN")
    public ResponseEntity<ApiResponse<LoginResponse>> loginMpin(
            @Valid @RequestBody MpinLoginRequest request,
            @RequestParam String tokenId) {
        LoginResponse response = authClient.loginWithCredentials(
                request.getClientId(), request.getMpin(), tokenId);
        return ResponseEntity.ok(ApiResponse.success(response));
    }

    @PostMapping("/validate-2fa")
    @Operation(summary = "Validate 2FA code", description = "Submit OTP or 2FA answer to complete authentication")
    public ResponseEntity<ApiResponse<TwoFaResponse>> validateTwoFa(
            @Valid @RequestBody TwoFaRequest request,
            @RequestParam String tokenId) {
        TwoFaResponse response = authClient.validateTwoFa(request.getAnswer(), tokenId);
        return ResponseEntity.ok(ApiResponse.success(response));
    }

    @PostMapping("/authorize")
    @Operation(summary = "Authorize access", description = "Authorize application access with consent and request token")
    public ResponseEntity<ApiResponse<AuthorizeResponse>> authorize(
            @RequestParam String tokenId,
            @RequestParam String requestToken,
            @RequestParam(defaultValue = "true") boolean consent) {
        AuthorizeResponse response = authClient.authorize(tokenId, requestToken, consent);
        return ResponseEntity.ok(ApiResponse.success(response));
    }

    @PostMapping("/access-token")
    @Operation(summary = "Get access token", description = "Exchange request token for an access token")
    public ResponseEntity<ApiResponse<AccessTokenResponse>> getAccessToken(
            @RequestParam String requestToken) {
        AccessTokenResponse response = authClient.fetchAccessToken(requestToken);
        return ResponseEntity.ok(ApiResponse.success(response));
    }

    @PostMapping("/full-login")
    @Operation(summary = "Complete login flow", description = "Perform full login with credentials and 2FA in one call")
    public ResponseEntity<ApiResponse<Map<String, String>>> fullLogin(
            @Valid @RequestBody LoginRequest request,
            @RequestParam String twoFaAnswer) {
        AuthSession session = authClient.performFullLogin(
                request.getUsername(), request.getPassword(), twoFaAnswer);
        return ResponseEntity.ok(ApiResponse.success(Map.of(
                "accessToken", session.getAccessToken(),
                "loginId", session.getLoginId(),
                "message", "Login successful"
        )));
    }
}
