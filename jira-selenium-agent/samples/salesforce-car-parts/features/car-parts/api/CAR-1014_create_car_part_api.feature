@CAR-1014 @api @create @priority_high
Feature: CAR-1014 - Create Car Part via API
  As an automation engineer
  I want to create a new car part through the REST API
  So that I can verify the create endpoint works with all dropdown fields

  # Jira Story: CAR-1014
  # Test Case: TC-014
  # Type: API Test

  Scenario: Create a new car part with all fields and verify
    Given the API base URL is "http://localhost:5555"
    When I send a POST request to "/api/car-parts" with body:
      | part_name          | API Test - Alternator    |
      | part_number        | ALT-API-2024-099         |
      | part_category      | Electrical & Lighting    |
      | part_sub_category  | Alternator               |
      | manufacturer       | Denso                    |
      | condition          | New                      |
      | vehicle_make       | Toyota                   |
      | unit_price         | 320.00                   |
      | availability       | In Stock                 |
    Then the response status should be 201
    And the response body should contain an "id" field
    When I send a GET request to the created part URL
    Then the response status should be 200
