# Jira Story: CAR-1026
# Test Case: TC-026
# Type: Relationship - Cross-Object SOQL Query
# Priority: High

@CAR-1026 @relationship @soql @cross_object @priority_high
Feature: CAR-1026 - Cross-Object SOQL Query Traversal

  As a Salesforce developer
  I want to query across multiple object relationships using SOQL-style syntax
  So that I can retrieve related data in a single query

  Scenario: Query Car Parts with Manufacturer relationship
    Given the API base URL is "http://localhost:5555"
    When I send a SOQL query "SELECT Name, Manufacturer__r.Name FROM Car_Part__c"
    Then the response status should be 200
    And each record should contain "Manufacturer__r"
    And the "totalSize" should be greater than 0

  Scenario: Query Car Parts with child Orders subquery
    Given the API base URL is "http://localhost:5555"
    When I send a SOQL query "SELECT Name, (SELECT Name FROM Orders__r) FROM Car_Part__c"
    Then the response status should be 200
    And records with orders should have "Orders__r.records" array

  Scenario: Query Warranty Claims traversing two parent objects
    Given the API base URL is "http://localhost:5555"
    When I send a SOQL query "SELECT Name, Car_Part__r.Name, Order__r.Name FROM Warranty_Claim__c"
    Then the response status should be 200
    And each record should contain both "Car_Part__r" and "Order__r" references
