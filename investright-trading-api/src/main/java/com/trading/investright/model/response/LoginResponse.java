package com.trading.investright.model.response;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.Map;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class LoginResponse {

    private Boolean recaptcha;
    private String loginId;
    private Map<String, Object> twofa;
    private Boolean twoFAEnabled;
}
