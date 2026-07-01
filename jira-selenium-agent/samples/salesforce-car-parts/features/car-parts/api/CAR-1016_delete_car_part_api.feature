@CAR-1016 @api @delete @priority_medium
Feature: CAR-1016 - Delete Car Part via API
  As an automation engineer
  I want to delete a car part through the REST API
  So that I can verify the delete endpoint removes the record

  # Jira Story: CAR-1016
  # Test Case: TC-016
  # Type: API Test

  Scenario: Create and delete a car part via API
    Given the API base URL is "http://localhost:5555"
    When I create a temporary car part via POST
    Then the response status should be 201
    When I send a DELETE request to the created part URL
    Then the response status should be 200
    When I send a GET request to the deleted part URL
    Then the response status should be 404
