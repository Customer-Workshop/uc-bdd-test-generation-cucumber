@CAR-1003 @create @suspension @priority_medium
Feature: CAR-1003 - Create Suspension and Steering Car Part
  As a Salesforce user
  I want to create a new Suspension and Steering car part
  So that suspension components are tracked in the inventory

  # Jira Story: CAR-1003
  # Test Case: TC-003
  # Application: Car Parts Management - Salesforce Lightning
  # Framework: Lightning Web Components (LWC)

  Background:
    Given the user is logged in to Salesforce
    And the user navigates to the Car Parts application

  Scenario: Create a Suspension and Steering car part
    Given the user is on the Car Parts list view
    When the user clicks the "New" button
    And the user enters "Coilover Suspension Kit - Adjustable" in the "Part Name" field
    And the user enters "SUS-COIL-ADJ-007" in the "Part Number" field
    And the user selects "Suspension & Steering" from the "Part Category" dropdown
    And the user selects "Shock Absorber" from the "Part Sub-Category" dropdown
    And the user selects "KYB" from the "Manufacturer" dropdown
    And the user selects "New" from the "Condition" dropdown
    And the user enters "899.50" in the "Unit Price" field
    And the user enters "40" in the "Stock Quantity" field
    And the user selects "Honda" from the "Vehicle Make" dropdown
    And the user selects "2010-2014" from the "Model Year Range" dropdown
    And the user selects "Low Stock" from the "Availability Status" dropdown
    And the user selects "Warehouse C - East" from the "Warehouse Location" dropdown
    And the user selects "OES" from the "Quality Grade" dropdown
    And the user selects "Standard Ground" from the "Shipping Class" dropdown
    And the user selects "1-Year Limited" from the "Warranty Type" dropdown
    When the user clicks the "Save" button
    Then a success toast message "was created" should be displayed
