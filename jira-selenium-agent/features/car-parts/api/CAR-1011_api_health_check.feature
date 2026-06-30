@CAR-1011 @api @health @priority_high
Feature: CAR-1011 - API Health Check
  As an automation engineer
  I want to verify the Car Parts REST API is reachable
  So that I can confirm the application is running before executing tests

  # Jira Story: CAR-1011
  # Test Case: TC-011
  # Type: API Test

  Scenario: Verify API endpoints are reachable
    Given the API base URL is "http://localhost:5555"
    When I send a GET request to "/api/car-parts"
    Then the response status should be 200
    When I send a GET request to "/api/dropdown-fields"
    Then the response status should be 200
