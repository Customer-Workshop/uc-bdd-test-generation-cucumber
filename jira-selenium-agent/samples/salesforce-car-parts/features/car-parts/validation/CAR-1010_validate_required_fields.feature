@CAR-1010 @validation @priority_high
Feature: CAR-1010 - Validate Required Fields on Car Part Form
  As a Salesforce user
  I want to see validation errors when required fields are missing
  So that data quality is enforced before saving a record

  # Jira Story: CAR-1010
  # Test Case: TC-010
  # Application: Car Parts Management - Salesforce Lightning
  # Framework: Lightning Web Components (LWC)

  Background:
    Given the user is logged in to Salesforce
    And the user navigates to the Car Parts application

  Scenario: Validate required fields on Car Part form
    Given the user is on the Car Parts list view
    When the user clicks the "New" button
    And the user clicks the "Save" button without filling required fields
    Then validation error messages should be displayed for:
      | Part Name        |
      | Part Number      |
      | Part Category    |
      | Part Sub-Category|
      | Manufacturer     |
