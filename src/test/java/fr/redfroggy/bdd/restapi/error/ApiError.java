package fr.redfroggy.bdd.restapi.error;

import java.util.ArrayList;
import java.util.List;

/**
 * Error payload returned by the sample APIs when a request cannot be fulfilled.
 */
public class ApiError {

    private int status;

    private String message;

    private List<FieldError> errors = new ArrayList<>();

    public ApiError() {
        // Jackson
    }

    public ApiError(int status, String message) {
        this.status = status;
        this.message = message;
    }

    public int getStatus() {
        return status;
    }

    public void setStatus(int status) {
        this.status = status;
    }

    public String getMessage() {
        return message;
    }

    public void setMessage(String message) {
        this.message = message;
    }

    public List<FieldError> getErrors() {
        return errors;
    }

    public void setErrors(List<FieldError> errors) {
        this.errors = errors;
    }

    public void addError(String field, String message) {
        this.errors.add(new FieldError(field, message));
    }

    public static class FieldError {

        private String field;

        private String message;

        public FieldError() {
            // Jackson
        }

        public FieldError(String field, String message) {
            this.field = field;
            this.message = message;
        }

        public String getField() {
            return field;
        }

        public void setField(String field) {
            this.field = field;
        }

        public String getMessage() {
            return message;
        }

        public void setMessage(String message) {
            this.message = message;
        }
    }
}
