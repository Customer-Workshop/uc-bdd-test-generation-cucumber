# Jira Story: CAR-1028
# Test Case: TC-028
# Type: Relationship - Central Data Hub
# Priority: Medium

@CAR-1028 @relationship @data_hub @priority_medium
Feature: CAR-1028 - Multi-Relationship Central Data Hub

  As a Salesforce architect
  I want Car Part to function as a central data hub
  So that related records are accessible through explicit relationship paths

  Scenario: Car Part is connected to Manufacturer, Warehouse, Orders, and Claims
    Given the API base URL is "http://localhost:5555"
    When I send a GET request to "/api/car-parts/CP-001/related"
    Then the response status should be 200
    And the part should have parent "Manufacturer__r" (Lookup)
    And the part should have parent "Warehouse__r" (Lookup)
    And the part should have children "Orders__r" (Master-Detail)
    And the part should have children "Warranty_Claims__r" (Lookup)

  Scenario: Manufacturer is connected to Supplier and Car Parts
    Given the API base URL is "http://localhost:5555"
    When I send a GET request to "/api/manufacturers/MFR-001"
    Then the response status should be 200
    And the manufacturer should have parent "Primary_Supplier__r"
    And the manufacturer should have children "Car_Parts__r"

  Scenario: Warehouse serves as hub for Car Parts and Orders
    Given the API base URL is "http://localhost:5555"
    When I send a GET request to "/api/warehouses/WH-001"
    Then the response status should be 200
    And the warehouse should have children "Car_Parts__r"
    And the warehouse should have children "Orders__r"
