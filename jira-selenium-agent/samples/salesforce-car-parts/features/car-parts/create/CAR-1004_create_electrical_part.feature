@CAR-1004 @create @electrical @priority_medium
Feature: CAR-1004 - Create Electrical and Lighting Car Part
  As a Salesforce user
  I want to create a new Electrical and Lighting car part
  So that electrical components are available in the inventory

  # Jira Story: CAR-1004
  # Test Case: TC-004
  # Application: Car Parts Management - Salesforce Lightning
  # Framework: Lightning Web Components (LWC)

  Background:
    Given the user is logged in to Salesforce
    And the user navigates to the Car Parts application

  Scenario: Create an Electrical and Lighting car part
    Given the user is on the Car Parts list view
    When the user clicks the "New" button
    And the user enters "LED Headlight Assembly - Projector" in the "Part Name" field
    And the user enters "ELC-LED-PROJ-012" in the "Part Number" field
    And the user selects "Electrical & Lighting" from the "Part Category" dropdown
    And the user selects "Headlight" from the "Part Sub-Category" dropdown
    And the user selects "Hella" from the "Manufacturer" dropdown
    And the user selects "New" from the "Condition" dropdown
    And the user enters "574.00" in the "Unit Price" field
    And the user enters "75" in the "Stock Quantity" field
    And the user selects "Mercedes-Benz" from the "Vehicle Make" dropdown
    And the user selects "2020-2026" from the "Model Year Range" dropdown
    And the user selects "In Stock" from the "Availability Status" dropdown
    And the user selects "Warehouse E - Central" from the "Warehouse Location" dropdown
    And the user selects "OEM" from the "Quality Grade" dropdown
    And the user selects "Oversized" from the "Shipping Class" dropdown
    And the user selects "Manufacturer Warranty" from the "Warranty Type" dropdown
    When the user clicks the "Save" button
    Then a success toast message "was created" should be displayed
