@CAR-1009 @delete @priority_medium
Feature: CAR-1009 - Delete Car Part Record
  As a Salesforce user
  I want to delete a Car Part record
  So that obsolete or incorrect parts are removed from the inventory

  # Jira Story: CAR-1009
  # Test Case: TC-009
  # Application: Car Parts Management - Salesforce Lightning
  # Framework: Lightning Web Components (LWC)

  Background:
    Given the user is logged in to Salesforce
    And the user navigates to the Car Parts application

  Scenario: Delete a Car Part record
    Given the user is on the Car Parts list view
    And the user searches for "LED Headlight Assembly" in the list
    When the user opens the first matching record
    And the user clicks "Delete" from the record actions
    And the user confirms the deletion
    Then a success toast message "was deleted" should be displayed
    And the user should be redirected to the list view
