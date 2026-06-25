@CAR-1007 @search @filter @priority_medium
Feature: CAR-1007 - Search and Filter Car Parts
  As a Salesforce user
  I want to search and filter Car Parts by different criteria
  So that I can quickly find specific parts in the inventory

  # Jira Story: CAR-1007
  # Test Case: TC-007
  # Application: Car Parts Management - Salesforce Lightning
  # Framework: Lightning Web Components (LWC)

  Background:
    Given the user is logged in to Salesforce
    And the user navigates to the Car Parts application

  Scenario: Search and filter Car Parts by different criteria
    Given the user is on the Car Parts list view

    # Search by part name
    When the user searches for "Brake" in the list
    Then the list should display parts containing "Brake"

    # Filter by list view
    When the user selects the "All Car Parts" list view
    Then all car parts should be displayed

    When the user selects the "In Stock Parts" list view
    Then only parts with availability "In Stock" should be displayed

    # Sort by column
    When the user sorts by the "Part Name" column
    Then the list should be sorted alphabetically

    When the user sorts by the "Unit Price" column
    Then the list should be sorted by price
