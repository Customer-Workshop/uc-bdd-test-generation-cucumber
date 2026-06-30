@CAR-1012 @api @read @priority_high
Feature: CAR-1012 - List All Car Parts via API
  As an automation engineer
  I want to retrieve all car parts through the REST API
  So that I can verify the data layer returns correct records

  # Jira Story: CAR-1012
  # Test Case: TC-012
  # Type: API Test

  Scenario: List all car parts and validate response structure
    Given the API base URL is "http://localhost:5555"
    When I send a GET request to "/api/car-parts"
    Then the response status should be 200
    And the response body should be a JSON array
    And each item should contain fields:
      | id             |
      | part_name      |
      | part_number    |
      | part_category  |
