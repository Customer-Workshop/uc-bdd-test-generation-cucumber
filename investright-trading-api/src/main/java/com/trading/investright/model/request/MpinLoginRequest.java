package com.trading.investright.model.request;

import jakarta.validation.constraints.NotBlank;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class MpinLoginRequest {

    @NotBlank(message = "Client ID is required")
    private String clientId;

    @NotBlank(message = "MPIN is required")
    private String mpin;
}
