# Jira Story: CAR-1025
# Test Case: TC-025
# Type: Relationship - Custom Object API Names
# Priority: Medium

@CAR-1025 @relationship @custom_object @priority_medium
Feature: CAR-1025 - Custom Object __c Suffix and API Identity

  As a Salesforce developer
  I want to verify all custom objects use __c suffix and have unique API identities
  So that the schema is Salesforce-compliant

  Scenario: Verify all custom objects have __c suffix
    Given the API base URL is "http://localhost:5555"
    When I send a GET request to "/api/relationship-schema"
    Then the response status should be 200
    And all object API names should end with "__c"
    And the schema should contain objects: Car_Part__c, Manufacturer__c, Warehouse__c, Supplier__c, Order__c, Warranty_Claim__c

  Scenario: Verify each object has a unique key prefix
    Given the API base URL is "http://localhost:5555"
    When I send a GET request to "/api/relationship-schema"
    Then the response status should be 200
    And "Car_Part__c" key_prefix should be "CP"
    And "Manufacturer__c" key_prefix should be "MFR"
    And "Warehouse__c" key_prefix should be "WH"
    And "Supplier__c" key_prefix should be "SUP"
    And "Order__c" key_prefix should be "ORD"
    And "Warranty_Claim__c" key_prefix should be "WC"
