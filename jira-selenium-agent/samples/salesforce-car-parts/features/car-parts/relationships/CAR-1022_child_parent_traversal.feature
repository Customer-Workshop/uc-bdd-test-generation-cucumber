# Jira Story: CAR-1022
# Test Case: TC-022
# Type: Relationship - Child-to-Parent Traversal
# Priority: High

@CAR-1022 @relationship @child_parent @priority_high
Feature: CAR-1022 - Child-to-Parent Relationship Traversal

  As a Salesforce administrator
  I want to traverse child-to-parent relationships using __r references
  So that I can access parent record fields from a child object

  Scenario: Retrieve Order with Car_Part__r parent traversal
    Given the API base URL is "http://localhost:5555"
    When I send a GET request to "/api/orders/ORD-001"
    Then the response status should be 200
    And the response should contain "Car_Part__r" parent reference
    And "Car_Part__r.part_name" should be "Turbocharger Assembly"

  Scenario: Retrieve Order with Ship_From_Warehouse__r parent traversal
    Given the API base URL is "http://localhost:5555"
    When I send a GET request to "/api/orders/ORD-001"
    Then the response status should be 200
    And the response should contain "Ship_From_Warehouse__r" parent reference
    And "Ship_From_Warehouse__r.Name" should be "Main Warehouse - A1"

  Scenario: Retrieve Warranty Claim with multiple parent references
    Given the API base URL is "http://localhost:5555"
    When I send a GET request to "/api/warranty-claims"
    Then the response status should be 200
    And each record should contain "Car_Part__r" with "part_name"
    And each record should contain "Order__r" with "Name"
