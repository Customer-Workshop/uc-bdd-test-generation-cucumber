@CAR-1002 @create @braking @priority_high
Feature: CAR-1002 - Create Braking System Car Part
  As a Salesforce user
  I want to create a new Braking System car part with dependent picklists
  So that the part is catalogued with correct category-subcategory mapping

  # Jira Story: CAR-1002
  # Test Case: TC-002
  # Application: Car Parts Management - Salesforce Lightning
  # Framework: Lightning Web Components (LWC)

  Background:
    Given the user is logged in to Salesforce
    And the user navigates to the Car Parts application

  Scenario: Create a Braking System car part with dependent picklists
    Given the user is on the Car Parts list view
    When the user clicks the "New" button
    Then the Car Part creation form should be displayed

    When the user enters "Performance Brake Kit - Front Axle" in the "Part Name" field
    And the user enters "BRK-PERF-FA-004" in the "Part Number" field

    And the user selects "Braking System" from the "Part Category" dropdown
    And the dependent "Part Sub-Category" dropdown refreshes
    And the user selects "Brake Pad" from the "Part Sub-Category" dropdown
    And the user selects "Brembo" from the "Manufacturer" dropdown
    And the user selects "New" from the "Condition" dropdown
    And the user enters "349.99" in the "Unit Price" field
    And the user enters "150" in the "Stock Quantity" field
    And the user selects "BMW" from the "Vehicle Make" dropdown
    And the user selects "2020-2026" from the "Model Year Range" dropdown
    And the user selects "In Stock" from the "Availability Status" dropdown
    And the user selects "Warehouse B - South" from the "Warehouse Location" dropdown
    And the user selects "Aftermarket Premium" from the "Quality Grade" dropdown
    And the user selects "Express 2-Day" from the "Shipping Class" dropdown
    And the user selects "Manufacturer Warranty" from the "Warranty Type" dropdown

    When the user clicks the "Save" button
    Then a success toast message "was created" should be displayed
    And the "Part Category" field should display "Braking System"
    And the "Manufacturer" field should display "Brembo"
