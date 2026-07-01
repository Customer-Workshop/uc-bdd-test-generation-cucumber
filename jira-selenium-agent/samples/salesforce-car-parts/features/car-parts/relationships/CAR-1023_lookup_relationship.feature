# Jira Story: CAR-1023
# Test Case: TC-023
# Type: Relationship - Lookup Fields
# Priority: High

@CAR-1023 @relationship @lookup @priority_high
Feature: CAR-1023 - Lookup Relationship Field Handling

  As a Salesforce administrator
  I want to verify Lookup relationship fields have distinct __c and __r API names
  So that data is not blended between relationship paths

  Scenario: Car Part has distinct Manufacturer__c (ID) and Manufacturer__r (object)
    Given the API base URL is "http://localhost:5555"
    When I send a GET request to "/api/car-parts/CP-001/related"
    Then the response status should be 200
    And the response should contain field "Manufacturer__c" with value "MFR-001"
    And the response should contain object "Manufacturer__r" with field "Name" equal to "BorgWarner"

  Scenario: Car Part has distinct Warehouse__c (ID) and Warehouse__r (object)
    Given the API base URL is "http://localhost:5555"
    When I send a GET request to "/api/car-parts/CP-001/related"
    Then the response status should be 200
    And the response should contain field "Warehouse__c" with value "WH-001"
    And the response should contain object "Warehouse__r" with field "Name" equal to "Main Warehouse - A1"

  Scenario: Manufacturer has Lookup to Supplier via Primary_Supplier__r
    Given the API base URL is "http://localhost:5555"
    When I send a GET request to "/api/manufacturers/MFR-001"
    Then the response status should be 200
    And the response should contain "Primary_Supplier__r" parent reference
    And "Primary_Supplier__r.Name" should be "Global Steel Corp"
