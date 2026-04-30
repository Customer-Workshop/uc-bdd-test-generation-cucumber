package com.trading.investright.client;

import com.trading.investright.exception.InvestRightApiException;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpStatusCode;
import org.springframework.web.reactive.function.client.WebClientResponseException;

import java.util.concurrent.atomic.AtomicInteger;

import static org.junit.jupiter.api.Assertions.*;

class ApiRetryHandlerTest {

    @Test
    void shouldReturnOnFirstSuccess() {
        String result = ApiRetryHandler.executeWithRetry(() -> "success", "test-op");
        assertEquals("success", result);
    }

    @Test
    void shouldRetryAndSucceedOnSecondAttempt() {
        AtomicInteger attempts = new AtomicInteger(0);
        String result = ApiRetryHandler.executeWithRetry(() -> {
            if (attempts.incrementAndGet() == 1) {
                throw new RuntimeException("transient error");
            }
            return "recovered";
        }, "test-op");

        assertEquals("recovered", result);
        assertEquals(2, attempts.get());
    }

    @Test
    void shouldRetryOnServerError() {
        AtomicInteger attempts = new AtomicInteger(0);
        String result = ApiRetryHandler.executeWithRetry(() -> {
            if (attempts.incrementAndGet() <= 2) {
                throw new InvestRightApiException("server error", 500, "Internal Server Error");
            }
            return "recovered";
        }, "test-op");

        assertEquals("recovered", result);
        assertEquals(3, attempts.get());
    }

    @Test
    void shouldNotRetryOn400BadRequest() {
        AtomicInteger attempts = new AtomicInteger(0);
        assertThrows(InvestRightApiException.class, () ->
                ApiRetryHandler.executeWithRetry(() -> {
                    attempts.incrementAndGet();
                    throw new InvestRightApiException("bad request", 400, "Bad Request");
                }, "test-op"));

        assertEquals(1, attempts.get());
    }

    @Test
    void shouldNotRetryOn401Unauthorized() {
        AtomicInteger attempts = new AtomicInteger(0);
        assertThrows(InvestRightApiException.class, () ->
                ApiRetryHandler.executeWithRetry(() -> {
                    attempts.incrementAndGet();
                    throw new InvestRightApiException("unauthorized", 401, "Unauthorized");
                }, "test-op"));

        assertEquals(1, attempts.get());
    }

    @Test
    void shouldNotRetryOn422UnprocessableEntity() {
        AtomicInteger attempts = new AtomicInteger(0);
        assertThrows(InvestRightApiException.class, () ->
                ApiRetryHandler.executeWithRetry(() -> {
                    attempts.incrementAndGet();
                    throw new InvestRightApiException("unprocessable", 422, "Unprocessable");
                }, "test-op"));

        assertEquals(1, attempts.get());
    }

    @Test
    void shouldFailAfterMaxRetries() {
        AtomicInteger attempts = new AtomicInteger(0);
        assertThrows(RuntimeException.class, () ->
                ApiRetryHandler.executeWithRetry(() -> {
                    attempts.incrementAndGet();
                    throw new RuntimeException("persistent failure");
                }, "test-op", 3));

        assertEquals(4, attempts.get());
    }

    @Test
    void shouldRespectCustomMaxRetries() {
        AtomicInteger attempts = new AtomicInteger(0);
        String result = ApiRetryHandler.executeWithRetry(() -> {
            if (attempts.incrementAndGet() <= 1) {
                throw new RuntimeException("transient");
            }
            return "ok";
        }, "test-op", 1);

        assertEquals("ok", result);
        assertEquals(2, attempts.get());
    }
}
