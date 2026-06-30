@CAR-1019 @api @validation @priority_medium
Feature: CAR-1019 - Nonexistent Car Part Returns 404
  As an automation engineer
  I want to verify the API returns 404 for nonexistent resources
  So that I can confirm proper error handling

  # Jira Story: CAR-1019
  # Test Case: TC-019
  # Type: API Test

  Scenario: Verify 404 for nonexistent car part
    Given the API base URL is "http://localhost:5555"
    When I send a GET request to "/api/car-parts/NONEXISTENT-999"
    Then the response status should be 404
    When I send a DELETE request to "/api/car-parts/NONEXISTENT-999"
    Then the response status should be 404
