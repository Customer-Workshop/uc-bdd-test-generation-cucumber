# Jira Story: CAR-1024
# Test Case: TC-024
# Type: Relationship - Master-Detail
# Priority: High

@CAR-1024 @relationship @master_detail @priority_high
Feature: CAR-1024 - Master-Detail Relationship Handling

  As a Salesforce administrator
  I want to verify Master-Detail relationships enforce cascade behavior
  So that child records are properly linked to parent records

  Scenario: Order has Master-Detail to Car Part via Car_Part__c
    Given the API base URL is "http://localhost:5555"
    When I send a GET request to "/api/orders/ORD-001"
    Then the response status should be 200
    And "Car_Part__c" should be "CP-001"
    And "Car_Part__r" should contain the full parent Car Part record

  Scenario: Car Part shows Orders as Master-Detail children
    Given the API base URL is "http://localhost:5555"
    When I send a GET request to "/api/relationship-schema"
    Then the response status should be 200
    And "Car_Part__c" child_relationships should include "Orders__r" with type "Master-Detail"
    And "Order__c" relationships should include "Car_Part__c" with type "Master-Detail"

  Scenario: Formula field Total_Amount__c references Car_Part__r.Unit_Price__c
    Given the API base URL is "http://localhost:5555"
    When I send a GET request to "/api/orders/ORD-001"
    Then the response status should be 200
    And "Total_Amount__c" should be a calculated value from Quantity * Car_Part__r.Unit_Price__c
