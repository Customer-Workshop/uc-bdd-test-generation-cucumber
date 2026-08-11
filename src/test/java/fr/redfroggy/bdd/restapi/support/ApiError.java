package fr.redfroggy.bdd.restapi.support;

public class ApiError {

    private final String error;

    private final String field;

    public ApiError(String error, String field) {
        this.error = error;
        this.field = field;
    }

    public String getError() {
        return error;
    }

    public String getField() {
        return field;
    }
}
