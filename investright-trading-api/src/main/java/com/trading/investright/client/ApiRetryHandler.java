package com.trading.investright.client;

import com.trading.investright.exception.InvestRightApiException;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.reactive.function.client.WebClientResponseException;

import java.util.Set;
import java.util.function.Supplier;

@Slf4j
public final class ApiRetryHandler {

    private static final int DEFAULT_MAX_RETRIES = 3;
    private static final long DEFAULT_INITIAL_DELAY_MS = 500;
    private static final double DEFAULT_BACKOFF_MULTIPLIER = 2.0;
    private static final Set<Integer> NON_RETRYABLE_STATUS_CODES = Set.of(400, 401, 403, 422);

    private ApiRetryHandler() {}

    public static <T> T executeWithRetry(Supplier<T> apiCall, String operationName) {
        return executeWithRetry(apiCall, operationName, DEFAULT_MAX_RETRIES);
    }

    public static <T> T executeWithRetry(Supplier<T> apiCall, String operationName, int maxRetries) {
        int attempt = 0;
        long delayMs = DEFAULT_INITIAL_DELAY_MS;

        while (true) {
            try {
                return apiCall.get();
            } catch (WebClientResponseException ex) {
                if (NON_RETRYABLE_STATUS_CODES.contains(ex.getStatusCode().value())) {
                    log.warn("{} failed with non-retryable status {}: {}",
                            operationName, ex.getStatusCode().value(), ex.getResponseBodyAsString());
                    throw new InvestRightApiException(
                            operationName + " failed: " + ex.getResponseBodyAsString(),
                            ex.getStatusCode().value(),
                            ex.getResponseBodyAsString());
                }
                attempt++;
                if (attempt > maxRetries) {
                    log.error("{} failed after {} retries. Last error: {} {}",
                            operationName, maxRetries, ex.getStatusCode().value(), ex.getResponseBodyAsString());
                    throw new InvestRightApiException(
                            operationName + " failed after " + maxRetries + " retries: " + ex.getResponseBodyAsString(),
                            ex.getStatusCode().value(),
                            ex.getResponseBodyAsString());
                }
                log.warn("{} attempt {}/{} failed (HTTP {}). Retrying in {}ms...",
                        operationName, attempt, maxRetries, ex.getStatusCode().value(), delayMs);
                sleep(delayMs);
                delayMs = (long) (delayMs * DEFAULT_BACKOFF_MULTIPLIER);
            } catch (InvestRightApiException ex) {
                if (NON_RETRYABLE_STATUS_CODES.contains(ex.getStatusCode())) {
                    throw ex;
                }
                attempt++;
                if (attempt > maxRetries) {
                    log.error("{} failed after {} retries: {}", operationName, maxRetries, ex.getMessage());
                    throw ex;
                }
                log.warn("{} attempt {}/{} failed. Retrying in {}ms...",
                        operationName, attempt, maxRetries, delayMs);
                sleep(delayMs);
                delayMs = (long) (delayMs * DEFAULT_BACKOFF_MULTIPLIER);
            } catch (Exception ex) {
                attempt++;
                if (attempt > maxRetries) {
                    log.error("{} failed after {} retries: {}", operationName, maxRetries, ex.getMessage());
                    throw ex;
                }
                log.warn("{} attempt {}/{} failed ({}). Retrying in {}ms...",
                        operationName, attempt, maxRetries, ex.getMessage(), delayMs);
                sleep(delayMs);
                delayMs = (long) (delayMs * DEFAULT_BACKOFF_MULTIPLIER);
            }
        }
    }

    private static void sleep(long ms) {
        try {
            Thread.sleep(ms);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new RuntimeException("Retry interrupted", e);
        }
    }
}
