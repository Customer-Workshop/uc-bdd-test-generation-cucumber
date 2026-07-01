@CAR-1001 @create @engine @priority_high
Feature: CAR-1001 - Create Engine Component Car Part
  As a Salesforce user
  I want to create a new Engine Component car part with all dropdown fields
  So that the part is available in the Car Parts inventory

  # Jira Story: CAR-1001
  # Test Case: TC-001
  # Application: Car Parts Management - Salesforce Lightning
  # Framework: Lightning Web Components (LWC)

  Background:
    Given the user is logged in to Salesforce
    And the user navigates to the Car Parts application

  Scenario: Create a new Engine Component car part with all dropdown fields
    Given the user is on the Car Parts list view
    When the user clicks the "New" button
    Then the Car Part creation form should be displayed

    # Text fields
    When the user enters "Turbocharger Assembly - GT3582R" in the "Part Name" field
    And the user enters "ENG-TURBO-3582R-001" in the "Part Number" field

    # Required dropdown fields
    And the user selects "Engine Components" from the "Part Category" dropdown
    And the dependent "Part Sub-Category" dropdown refreshes
    And the user selects "Turbocharger" from the "Part Sub-Category" dropdown
    And the user selects "BorgWarner" from the "Manufacturer" dropdown
    And the user selects "New" from the "Condition" dropdown

    # Numeric fields
    And the user enters "2499.99" in the "Unit Price" field
    And the user enters "25" in the "Stock Quantity" field

    # Optional dropdown fields - Vehicle compatibility
    And the user selects "Toyota" from the "Vehicle Make" dropdown
    And the user selects "2015-2019" from the "Model Year Range" dropdown

    # Optional dropdown fields - Inventory & logistics
    And the user selects "In Stock" from the "Availability Status" dropdown
    And the user selects "Warehouse A - North" from the "Warehouse Location" dropdown
    And the user selects "OEM" from the "Quality Grade" dropdown
    And the user selects "Freight / LTL" from the "Shipping Class" dropdown
    And the user selects "2-Year Limited" from the "Warranty Type" dropdown
    And the user selects "USD" from the "Currency" dropdown

    # Description
    And the user enters "High-performance turbocharger assembly for Toyota Supra MK5. Includes wastegate and blow-off valve." in the "Description" field

    # Save
    When the user clicks the "Save" button
    Then a success toast message "was created" should be displayed
    And the Car Part record page should show "Turbocharger Assembly - GT3582R"
    And the "Part Category" field should display "Engine Components"
    And the "Manufacturer" field should display "BorgWarner"
    And the "Condition" field should display "New"
