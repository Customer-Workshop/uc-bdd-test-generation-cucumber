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
public class TwoFaResponse {

    private String requestToken;
    private Map<String, Object> termsAndConditions;
}
