@CAR-1017 @api @read @priority_medium
Feature: CAR-1017 - Get Dropdown Fields Metadata via API
  As an automation engineer
  I want to retrieve all dropdown field definitions
  So that I can verify picklist values match the application

  # Jira Story: CAR-1017
  # Test Case: TC-017
  # Type: API Test

  Scenario: Verify all 12 dropdown fields have values
    Given the API base URL is "http://localhost:5555"
    When I send a GET request to "/api/dropdown-fields"
    Then the response status should be 200
    And the response should contain dropdown fields:
      | part_category    |
      | condition        |
      | manufacturer     |
      | vehicle_make     |
      | availability     |
      | quality_grade    |
