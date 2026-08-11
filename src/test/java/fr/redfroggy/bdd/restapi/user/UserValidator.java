package fr.redfroggy.bdd.restapi.user;

import fr.redfroggy.bdd.restapi.support.ApiError;
import wiremock.org.apache.commons.lang3.StringUtils;

import java.util.regex.Pattern;

final class UserValidator {

    static final int MAX_NAME_LENGTH = 50;

    static final int MAX_AGE = 150;

    private static final Pattern EMAIL_PATTERN = Pattern.compile("^[^\\s@]+@[^\\s@.]+\\.[^\\s@]{2,}$");

    private UserValidator() {
    }

    /**
     * @return an {@link ApiError} describing the first invalid field, null when the user is valid
     */
    static ApiError validate(UserDTO user) {
        if (user == null) {
            return new ApiError("a user payload is required", "body");
        }
        if (StringUtils.isBlank(user.getId())) {
            return new ApiError("id is required", "id");
        }
        if (StringUtils.isBlank(user.getFirstName())) {
            return new ApiError("firstName is required", "firstName");
        }
        if (StringUtils.isBlank(user.getLastName())) {
            return new ApiError("lastName is required", "lastName");
        }
        if (user.getFirstName().length() > MAX_NAME_LENGTH) {
            return new ApiError("firstName must not exceed " + MAX_NAME_LENGTH + " characters", "firstName");
        }
        if (user.getLastName().length() > MAX_NAME_LENGTH) {
            return new ApiError("lastName must not exceed " + MAX_NAME_LENGTH + " characters", "lastName");
        }
        if (user.getAge() < 0 || user.getAge() > MAX_AGE) {
            return new ApiError("age must be between 0 and " + MAX_AGE, "age");
        }
        if (StringUtils.isNotBlank(user.getEmail()) && !EMAIL_PATTERN.matcher(user.getEmail()).matches()) {
            return new ApiError("email is not a valid email address", "email");
        }
        return null;
    }
}
