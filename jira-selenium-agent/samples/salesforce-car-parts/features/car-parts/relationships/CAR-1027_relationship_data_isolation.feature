# Jira Story: CAR-1027
# Test Case: TC-027
# Type: Relationship - Data Isolation
# Priority: High

@CAR-1027 @relationship @data_isolation @priority_high
Feature: CAR-1027 - Relationship Data Isolation Between Paths

  As a Salesforce administrator
  I want to verify that data does not blend between relationship paths
  So that each relationship field has a distinct API identity

  Scenario: Manufacturer__c and Warehouse__c are separate relationship paths
    Given the API base URL is "http://localhost:5555"
    When I send a GET request to "/api/car-parts/CP-001/related"
    Then the response status should be 200
    And "Manufacturer__r" should resolve to a Manufacturer record
    And "Warehouse__r" should resolve to a Warehouse record
    And "Manufacturer__r.id" should not equal "Warehouse__r.id"

  Scenario: Order has two distinct parent paths that do not blend
    Given the API base URL is "http://localhost:5555"
    When I send a GET request to "/api/orders/ORD-001"
    Then the response status should be 200
    And "Car_Part__r" should be a Car Part record
    And "Ship_From_Warehouse__r" should be a Warehouse record
    And the two parent references should be independent objects

  Scenario: Warranty Claim has two Lookup paths to different parents
    Given the API base URL is "http://localhost:5555"
    When I send a GET request to "/api/warranty-claims"
    Then each claim should have "Car_Part__r" pointing to Car_Part__c
    And each claim should have "Order__r" pointing to Order__c
    And Car_Part__r and Order__r should never reference the same object type
