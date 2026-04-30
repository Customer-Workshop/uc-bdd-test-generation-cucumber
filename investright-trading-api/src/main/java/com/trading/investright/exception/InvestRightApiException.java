package com.trading.investright.exception;

import lombok.Getter;

@Getter
public class InvestRightApiException extends RuntimeException {

    private final int statusCode;
    private final String responseBody;

    public InvestRightApiException(String message) {
        super(message);
        this.statusCode = 500;
        this.responseBody = null;
    }

    public InvestRightApiException(String message, int statusCode, String responseBody) {
        super(message);
        this.statusCode = statusCode;
        this.responseBody = responseBody;
    }

    public InvestRightApiException(String message, Throwable cause) {
        super(message, cause);
        this.statusCode = 500;
        this.responseBody = null;
    }
}
