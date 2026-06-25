@CAR-1008 @dependent_picklist @priority_high
Feature: CAR-1008 - Verify Dependent Picklist Behavior
  As a Salesforce user
  I want to verify that dependent picklist values change based on parent selection
  So that Part Sub-Category correctly reflects the selected Part Category

  # Jira Story: CAR-1008
  # Test Case: TC-008
  # Application: Car Parts Management - Salesforce Lightning
  # Framework: Lightning Web Components (LWC)

  Background:
    Given the user is logged in to Salesforce
    And the user navigates to the Car Parts application

  Scenario: Verify dependent picklist values change based on parent selection
    Given the user is on the Car Parts list view
    When the user clicks the "New" button

    # Select Engine Components and verify sub-categories
    When the user selects "Engine Components" from the "Part Category" dropdown
    Then the "Part Sub-Category" dropdown should contain engine-related sub-categories:
      | Cylinder Head  |
      | Piston         |
      | Crankshaft     |
      | Camshaft       |
      | Valve          |
      | Gasket Set     |
      | Timing Belt    |
      | Oil Pump       |
      | Engine Block   |
      | Turbocharger   |

    # Change to Braking System and verify sub-categories change
    When the user selects "Braking System" from the "Part Category" dropdown
    Then the "Part Sub-Category" dropdown should contain braking-related sub-categories:
      | Brake Pad       |
      | Brake Disc      |
      | Brake Caliper   |
      | Brake Line      |
      | Master Cylinder |
      | ABS Module      |
      | Brake Drum      |
      | Brake Shoe      |

    # Change to Electrical & Lighting
    When the user selects "Electrical & Lighting" from the "Part Category" dropdown
    Then the "Part Sub-Category" dropdown should contain electrical sub-categories:
      | Alternator      |
      | Starter Motor   |
      | Battery         |
      | Ignition Coil   |
      | Spark Plug      |
      | Headlight       |
      | Tail Light      |
      | Wiring Harness  |
