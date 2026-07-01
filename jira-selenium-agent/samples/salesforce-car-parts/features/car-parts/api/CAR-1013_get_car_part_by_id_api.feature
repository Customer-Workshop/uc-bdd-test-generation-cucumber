@CAR-1013 @api @read @priority_high
Feature: CAR-1013 - Get Car Part by ID via API
  As an automation engineer
  I want to retrieve a specific car part by its ID
  So that I can verify individual record retrieval works correctly

  # Jira Story: CAR-1013
  # Test Case: TC-013
  # Type: API Test

  Scenario: Get car part CP-001 and verify fields
    Given the API base URL is "http://localhost:5555"
    When I send a GET request to "/api/car-parts/CP-001"
    Then the response status should be 200
    And the response body path "$.part_name" should be "Turbocharger Assembly"
    And the response body path "$.part_category" should be "Engine Components"
