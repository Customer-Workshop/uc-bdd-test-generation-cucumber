@CAR-1005 @dropdowns @traverse @priority_high
Feature: CAR-1005 - Traverse and Verify All Dropdown Fields
  As a Salesforce user
  I want to verify all dropdown fields display the correct values
  So that data integrity is maintained across all picklist fields

  # Jira Story: CAR-1005
  # Test Case: TC-005
  # Application: Car Parts Management - Salesforce Lightning
  # Framework: Lightning Web Components (LWC)

  Background:
    Given the user is logged in to Salesforce
    And the user navigates to the Car Parts application

  Scenario: Traverse and verify all dropdown fields and their values
    Given the user is on the Car Parts list view
    When the user clicks the "New" button
    Then the Car Part creation form should be displayed

    # Traverse Part Category dropdown (12 values)
    When the user opens the "Part Category" dropdown
    Then the dropdown should contain the following values:
      | Engine Components         |
      | Transmission & Drivetrain |
      | Braking System            |
      | Suspension & Steering     |
      | Electrical & Lighting     |
      | Exhaust System            |
      | Body & Exterior           |
      | Interior & Comfort        |
      | Cooling System            |
      | Fuel System               |
      | HVAC & Climate Control    |
      | Wheels & Tires            |

    # Traverse Manufacturer dropdown (18 values)
    When the user opens the "Manufacturer" dropdown
    Then the dropdown should contain the following values:
      | Bosch               |
      | Denso               |
      | Continental         |
      | Delphi              |
      | Valeo               |
      | ZF Friedrichshafen  |
      | Aisin               |
      | Magna International |
      | BorgWarner          |
      | Mahle               |
      | NGK                 |
      | ACDelco             |
      | Brembo              |
      | Monroe              |
      | KYB                 |
      | Gates               |
      | Hella               |
      | Moog                |

    # Traverse Condition dropdown (6 values)
    When the user opens the "Condition" dropdown
    Then the dropdown should contain the following values:
      | New              |
      | Refurbished      |
      | Used - Grade A   |
      | Used - Grade B   |
      | Used - Grade C   |
      | Salvage          |

    # Traverse Availability Status dropdown (7 values)
    When the user opens the "Availability Status" dropdown
    Then the dropdown should contain the following values:
      | In Stock      |
      | Low Stock     |
      | Out of Stock  |
      | Back Ordered  |
      | Discontinued  |
      | Pre-Order     |
      | Made to Order |

    # Traverse Vehicle Make dropdown (15 values)
    When the user opens the "Vehicle Make" dropdown
    Then the dropdown should contain the following values:
      | Toyota                |
      | Honda                 |
      | Ford                  |
      | Chevrolet             |
      | BMW                   |
      | Mercedes-Benz         |
      | Audi                  |
      | Volkswagen            |
      | Hyundai               |
      | Kia                   |
      | Nissan                |
      | Mazda                 |
      | Subaru                |
      | Volvo                 |
      | Jeep                  |
      | Universal / Multi-Fit |

    # Traverse Quality Grade dropdown (5 values)
    When the user opens the "Quality Grade" dropdown
    Then the dropdown should contain the following values:
      | OEM                   |
      | OES                   |
      | Aftermarket Premium   |
      | Aftermarket Standard  |
      | Economy               |

    # Traverse Shipping Class dropdown (7 values)
    When the user opens the "Shipping Class" dropdown
    Then the dropdown should contain the following values:
      | Standard Ground |
      | Express 2-Day   |
      | Overnight       |
      | Freight / LTL   |
      | Oversized       |
      | Hazmat          |
      | White Glove     |

    # Traverse Warranty Type dropdown (7 values)
    When the user opens the "Warranty Type" dropdown
    Then the dropdown should contain the following values:
      | No Warranty           |
      | 30-Day Limited        |
      | 90-Day Limited        |
      | 1-Year Limited        |
      | 2-Year Limited        |
      | Lifetime Limited      |
      | Manufacturer Warranty |
