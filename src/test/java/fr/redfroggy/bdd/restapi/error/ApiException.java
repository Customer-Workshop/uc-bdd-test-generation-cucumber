package fr.redfroggy.bdd.restapi.error;

import org.springframework.http.HttpStatus;

/**
 * Exception carrying the http status to return to the client.
 */
public class ApiException extends RuntimeException {

    private final HttpStatus status;

    public ApiException(HttpStatus status, String message) {
        super(message);
        this.status = status;
    }

    public HttpStatus getStatus() {
        return status;
    }
}
