@CAR-1018 @api @read @priority_medium
Feature: CAR-1018 - Get Dependent Sub-Categories via API
  As an automation engineer
  I want to verify the dependent picklist API returns correct sub-categories
  So that I can confirm the Part Category to Sub-Category cascade works

  # Jira Story: CAR-1018
  # Test Case: TC-018
  # Type: API Test

  Scenario: Verify sub-categories for each parent category
    Given the API base URL is "http://localhost:5555"
    When I send a GET request to "/api/sub-categories/Engine Components"
    Then the response status should be 200
    And the response should be a non-empty list
    When I send a GET request to "/api/sub-categories/Braking System"
    Then the response status should be 200
    And the response should be a non-empty list
    When I send a GET request to "/api/sub-categories/Electrical & Lighting"
    Then the response status should be 200
    And the response should be a non-empty list
