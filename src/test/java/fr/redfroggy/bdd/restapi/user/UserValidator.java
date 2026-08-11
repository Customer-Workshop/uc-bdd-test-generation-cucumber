package fr.redfroggy.bdd.restapi.user;

import fr.redfroggy.bdd.restapi.error.ApiError;
import wiremock.org.apache.commons.lang3.StringUtils;

import java.util.Optional;
import java.util.regex.Pattern;

final class UserValidator {

    static final int NAME_MAX_LENGTH = 50;

    static final int AGE_MIN = 1;

    static final int AGE_MAX = 149;

    private static final Pattern EMAIL_PATTERN = Pattern.compile("^[^@\\s]+@[^@\\s]+\\.[A-Za-z]{2,}$");

    private UserValidator() {
    }

    static Optional<ApiError> validate(UserDTO user) {
        if (StringUtils.isBlank(user.getId())) {
            return Optional.of(new ApiError("id", "id is required"));
        }
        Optional<ApiError> firstNameError = validateName("firstName", user.getFirstName());
        if (firstNameError.isPresent()) {
            return firstNameError;
        }
        Optional<ApiError> lastNameError = validateName("lastName", user.getLastName());
        if (lastNameError.isPresent()) {
            return lastNameError;
        }
        if (user.getAge() < AGE_MIN || user.getAge() > AGE_MAX) {
            return Optional.of(new ApiError("age", "age is out of the " + AGE_MIN + "-" + AGE_MAX + " range"));
        }
        if (StringUtils.isNotBlank(user.getEmail()) && !EMAIL_PATTERN.matcher(user.getEmail()).matches()) {
            return Optional.of(new ApiError("email", "email is invalid"));
        }
        return Optional.empty();
    }

    private static Optional<ApiError> validateName(String field, String value) {
        if (StringUtils.isBlank(value)) {
            return Optional.of(new ApiError(field, field + " is required"));
        }
        if (value.length() > NAME_MAX_LENGTH) {
            return Optional.of(new ApiError(field, field + " must not exceed " + NAME_MAX_LENGTH + " characters"));
        }
        return Optional.empty();
    }
}
