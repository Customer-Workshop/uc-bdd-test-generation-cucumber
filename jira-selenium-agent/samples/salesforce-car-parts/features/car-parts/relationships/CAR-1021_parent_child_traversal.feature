# Jira Story: CAR-1021
# Test Case: TC-021
# Type: Relationship - Parent-to-Child Traversal
# Priority: High

@CAR-1021 @relationship @parent_child @priority_high
Feature: CAR-1021 - Parent-to-Child Relationship Traversal

  As a Salesforce administrator
  I want to traverse parent-to-child relationships using __r references
  So that I can query child records from a parent object without data blending

  Scenario: Retrieve Car Part with child Orders via Orders__r
    Given the API base URL is "http://localhost:5555"
    And a Car Part "CP-001" exists with manufacturer "BorgWarner"
    When I send a GET request to "/api/car-parts/CP-001/related"
    Then the response status should be 200
    And the response should contain "Orders__r" child relationship
    And the "Orders__r.totalSize" should be greater than 0
    And each record in "Orders__r.records" should have field "Car_Part__c" equal to "CP-001"

  Scenario: Retrieve Car Part with child Warranty Claims via Warranty_Claims__r
    Given the API base URL is "http://localhost:5555"
    When I send a GET request to "/api/car-parts/CP-001/related"
    Then the response status should be 200
    And the response should contain "Warranty_Claims__r" child relationship
    And the "Warranty_Claims__r.totalSize" should be greater than 0
