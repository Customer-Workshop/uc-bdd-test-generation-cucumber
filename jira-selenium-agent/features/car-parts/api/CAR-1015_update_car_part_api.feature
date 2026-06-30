@CAR-1015 @api @update @priority_high
Feature: CAR-1015 - Update Car Part via API
  As an automation engineer
  I want to update an existing car part through the REST API
  So that I can verify partial updates work correctly

  # Jira Story: CAR-1015
  # Test Case: TC-015
  # Type: API Test

  Scenario: Update car part CP-002 fields
    Given the API base URL is "http://localhost:5555"
    When I send a PUT request to "/api/car-parts/CP-002" with body:
      | condition    | Refurbished |
      | unit_price   | 999.99      |
      | availability | Low Stock   |
    Then the response status should be 200
    And the response body path "$.condition" should be "Refurbished"
    And the response body path "$.unit_price" should be 999.99
