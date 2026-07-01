@CAR-1020 @api @validation @priority_high
Feature: CAR-1020 - Create Car Part with Invalid Data Returns 400
  As an automation engineer
  I want to verify the API rejects invalid create requests
  So that I can confirm input validation is enforced

  # Jira Story: CAR-1020
  # Test Case: TC-020
  # Type: API Test

  Scenario: Verify 400 for empty request body
    Given the API base URL is "http://localhost:5555"
    When I send a POST request to "/api/car-parts" with no body
    Then the response status should be 400
