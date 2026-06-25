@CAR-1006 @edit @priority_high
Feature: CAR-1006 - Edit Existing Car Part
  As a Salesforce user
  I want to edit an existing Car Part and update dropdown fields
  So that part information stays current and accurate

  # Jira Story: CAR-1006
  # Test Case: TC-006
  # Application: Car Parts Management - Salesforce Lightning
  # Framework: Lightning Web Components (LWC)

  Background:
    Given the user is logged in to Salesforce
    And the user navigates to the Car Parts application

  Scenario: Edit an existing Car Part and update dropdown fields
    Given the user is on the Car Parts list view
    And the user searches for "Turbocharger Assembly" in the list
    When the user opens the first matching record
    And the user clicks the "Edit" button

    And the user changes the "Condition" dropdown to "Refurbished"
    And the user changes the "Availability Status" dropdown to "Low Stock"
    And the user changes the "Warehouse Location" dropdown to "Warehouse D - West"
    And the user changes the "Quality Grade" dropdown to "Aftermarket Premium"
    And the user updates the "Unit Price" field to "1899.99"
    And the user updates the "Stock Quantity" field to "10"

    When the user clicks the "Save" button
    Then a success toast message "was saved" should be displayed
    And the "Condition" field should display "Refurbished"
    And the "Availability Status" field should display "Low Stock"
