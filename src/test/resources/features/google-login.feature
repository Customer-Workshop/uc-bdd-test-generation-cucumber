Feature: Google Login Page Tests

  Background:
    Given http baseUri is /api/
    And I set Accept-Language http header to en-US
    And I set http headers to:
      | Accept       | application/json |
      | Content-Type | application/json |

  Scenario: Successful login with valid Google credentials
    And I set http body to {"email":"testuser@gmail.com","password":"validPassword123"}
    When I POST auth/google-login
    Then http response code should be 200
    And http response body path $.token should not be null
    And http response body path $.email should be testuser@gmail.com

  Scenario: Login fails with invalid Google credentials
    And I set http body to {"email":"testuser@gmail.com","password":"wrongPassword"}
    When I POST auth/google-login
    Then http response code should be 401
    And http response body path $.message should be Invalid credentials

  Scenario: Login fails with empty email
    And I set http body to {"email":"","password":"somePassword"}
    When I POST auth/google-login
    Then http response code should be 400
    And http response body path $.message should be Email is required

  Scenario: Login fails with empty password
    And I set http body to {"email":"testuser@gmail.com","password":""}
    When I POST auth/google-login
    Then http response code should be 400
    And http response body path $.message should be Password is required

  Scenario: Login fails with malformed email format
    And I set http body to {"email":"not-an-email","password":"validPassword123"}
    When I POST auth/google-login
    Then http response code should be 400
    And http response body path $.message should be Invalid email format
