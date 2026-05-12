# Google Login BDD Test Report Analysis

## 1. Overview

This document provides an analysis of the BDD test scenarios for the **Google Login Page** REST API endpoint, implemented using the Spring Boot Cucumber REST API testing framework.

| Item               | Details                                                                 |
|--------------------|-------------------------------------------------------------------------|
| **Feature File**   | `src/test/resources/features/google-login.feature`                      |
| **Step Definition**| `src/test/java/fr/redfroggy/bdd/restapi/glue/GoogleLoginStepDefinition.java` |
| **API Endpoint**   | `POST /api/auth/google-login`                                           |
| **Framework**      | Spring Boot + Cucumber + Gherkin                                        |
| **Assertion Libs** | AssertJ, Jayway JsonPath                                                |

## 2. Test Scenario Summary

| #  | Scenario                                      | HTTP Method | Expected Status | Key Assertion                          |
|----|-----------------------------------------------|-------------|-----------------|----------------------------------------|
| 1  | Successful login with valid Google credentials| POST        | 200             | Response contains `token` and `email`  |
| 2  | Login fails with invalid Google credentials   | POST        | 401             | `$.message` = "Invalid credentials"    |
| 3  | Login fails with empty email                  | POST        | 400             | `$.message` = "Email is required"      |
| 4  | Login fails with empty password               | POST        | 400             | `$.message` = "Password is required"   |
| 5  | Login fails with malformed email format       | POST        | 400             | `$.message` = "Invalid email format"   |

**Total Scenarios:** 5  
**Positive Tests:** 1  
**Negative Tests:** 4

## 3. Test Coverage Analysis

### 3.1 Covered Areas

| Category                  | Coverage | Details                                                        |
|---------------------------|----------|----------------------------------------------------------------|
| Valid credentials         | Yes      | Verifies 200 response, JWT token, and email in response body   |
| Invalid password          | Yes      | Verifies 401 response with "Invalid credentials" message       |
| Empty email validation    | Yes      | Verifies 400 response with "Email is required" message         |
| Empty password validation | Yes      | Verifies 400 response with "Password is required" message      |
| Malformed email format    | Yes      | Verifies 400 response with "Invalid email format" message      |
| HTTP headers              | Yes      | Background sets `Accept`, `Content-Type`, `Accept-Language`    |
| JSON response validation  | Yes      | Uses JsonPath assertions (`$.token`, `$.email`, `$.message`)   |

### 3.2 Areas for Future Enhancement

| Category                        | Priority | Recommendation                                                    |
|---------------------------------|----------|-------------------------------------------------------------------|
| Rate limiting (429)             | Medium   | Add scenario for too many login attempts                          |
| SQL injection in email          | High     | Test with `'; DROP TABLE users;--` in email field                 |
| XSS in email field              | Medium   | Test with `<script>alert(1)</script>` in email field              |
| Token expiry validation         | Medium   | Verify token has correct TTL/expiry claims                        |
| Missing request body            | Low      | Send POST with no body, expect 400                                |
| Concurrent login attempts       | Low      | Stress test with multiple simultaneous requests                   |
| OAuth service unavailable       | Medium   | Mock Google OAuth as down, verify graceful 503 response           |
| Account lockout after N fails   | Medium   | Test consecutive failed attempts trigger lockout                  |

## 4. Step Definition Analysis

### 4.1 Built-in Steps Used (from `DefaultRestApiBddStepDefinition`)

| Step Pattern                                       | Purpose                         |
|----------------------------------------------------|---------------------------------|
| `Given http baseUri is /api/`                      | Sets the base URI for requests  |
| `I set {header} http header to {value}`            | Sets individual HTTP headers    |
| `I set http headers to:`                           | Sets multiple HTTP headers      |
| `I set http body to {json}`                        | Sets the JSON request body      |
| `I POST {resource}`                                | Sends a POST request            |
| `http response code should be {code}`              | Asserts HTTP status code        |
| `http response body path {path} should be {value}` | Asserts a JSON path value       |
| `http response body path {path} should not be null`| Asserts a JSON path is not null |

### 4.2 Custom Steps (from `GoogleLoginStepDefinition`)

| Step Pattern                                       | Purpose                                        | Status       |
|----------------------------------------------------|-------------------------------------------------|--------------|
| `the response should contain a valid JWT token`    | Validates JWT token structure (3-part format)   | Placeholder  |
| `the Google OAuth service is available`            | Setup/verify mock Google OAuth connectivity     | Placeholder  |

> **Note:** The custom steps are currently placeholder implementations. They should be completed when the actual API contract and OAuth integration details are finalized.

## 5. Test Execution

### 5.1 Running the Tests

```bash
mvn test
```

The existing Cucumber runner (`RestApiCucumberTest`) automatically picks up:
- Feature files from `src/test/resources/features/`
- Step definitions from the `fr.redfroggy.bdd.restapi.glue` package

### 5.2 Expected Results (Before API Implementation)

Since the `POST /api/auth/google-login` endpoint does not yet exist in the test application, all 5 scenarios will fail with a connection or 404 error. This is expected — the tests are designed to validate the API contract once the endpoint is implemented.

### 5.3 Prerequisites for Green Tests

1. Implement the `POST /api/auth/google-login` endpoint in the test application (or add a mock controller under `src/test/java/`)
2. The endpoint must accept JSON body: `{"email": "...", "password": "..."}`
3. The endpoint must return:
   - `200` with `{"token": "...", "email": "..."}` on success
   - `401` with `{"message": "Invalid credentials"}` on auth failure
   - `400` with `{"message": "..."}` on validation errors
4. If the endpoint calls an external Google OAuth service, configure WireMock stubs using the built-in `I mock third party api call` step

## 6. Architecture & Integration

```
src/
├── main/java/.../glue/
│   ├── AbstractBddStepDefinition.java     # Base class with HTTP & assertion logic
│   └── DefaultRestApiBddStepDefinition.java # Built-in Gherkin step definitions
├── test/java/.../glue/
│   ├── DefaultRestApiStepDefinitionTest.java # Spring context + Cucumber config
│   └── GoogleLoginStepDefinition.java       # Custom Google login steps
└── test/resources/features/
    ├── users.feature                        # Existing user CRUD tests
    ├── users-import.feature                 # Existing CSV import tests
    └── google-login.feature                 # New Google login tests
```

## 7. Recommendations

1. **Implement the login endpoint** — Create a mock controller (similar to `UserController`) under `src/test/java/` to make the tests executable.
2. **Complete custom step definitions** — Flesh out JWT token validation logic in `GoogleLoginStepDefinition` once the token format is defined.
3. **Add WireMock stubs** — If the login flow calls external Google OAuth APIs, use the framework's built-in WireMock step to mock those calls.
4. **Expand negative test coverage** — Add scenarios for rate limiting, SQL injection, and account lockout as listed in section 3.2.
5. **Add scenario tags** — Consider adding tags (e.g., `@google-login`, `@auth`) for selective test execution.
