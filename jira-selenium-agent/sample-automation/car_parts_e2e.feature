@CAR_PARTS @salesforce @lwc @e2e @priority_high
Feature: Car Parts Salesforce Lightning Web Component End-to-End Automation
  # Application: Car Parts Management - Salesforce Lightning
  # Framework: Lightning Web Components (LWC)
  # This feature covers the complete E2E flow for managing car parts
  # including all dropdown fields, dependent picklists, and CRUD operations.

  Background:
    Given the user is logged in to Salesforce
    And the user navigates to the Car Parts application

  # ---------- Scenario 1: Create a new Engine Component car part ----------
  @create @engine
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

  # ---------- Scenario 2: Create a Braking System part ----------
  @create @braking
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

  # ---------- Scenario 3: Create a Suspension part ----------
  @create @suspension
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

  # ---------- Scenario 4: Create an Electrical part ----------
  @create @electrical
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

  # ---------- Scenario 5: Traverse all dropdown fields ----------
  @dropdowns @traverse
  Scenario: Traverse and verify all dropdown fields and their values
    Given the user is on the Car Parts list view
    When the user clicks the "New" button
    Then the Car Part creation form should be displayed

    # Traverse Part Category dropdown
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

    # Traverse Manufacturer dropdown
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

    # Traverse Condition dropdown
    When the user opens the "Condition" dropdown
    Then the dropdown should contain the following values:
      | New              |
      | Refurbished      |
      | Used - Grade A   |
      | Used - Grade B   |
      | Used - Grade C   |
      | Salvage          |

    # Traverse Availability Status dropdown
    When the user opens the "Availability Status" dropdown
    Then the dropdown should contain the following values:
      | In Stock      |
      | Low Stock     |
      | Out of Stock  |
      | Back Ordered  |
      | Discontinued  |
      | Pre-Order     |
      | Made to Order |

    # Traverse Vehicle Make dropdown
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

    # Traverse Quality Grade dropdown
    When the user opens the "Quality Grade" dropdown
    Then the dropdown should contain the following values:
      | OEM                   |
      | OES                   |
      | Aftermarket Premium   |
      | Aftermarket Standard  |
      | Economy               |

    # Traverse Shipping Class dropdown
    When the user opens the "Shipping Class" dropdown
    Then the dropdown should contain the following values:
      | Standard Ground |
      | Express 2-Day   |
      | Overnight       |
      | Freight / LTL   |
      | Oversized       |
      | Hazmat          |
      | White Glove     |

    # Traverse Warranty Type dropdown
    When the user opens the "Warranty Type" dropdown
    Then the dropdown should contain the following values:
      | No Warranty           |
      | 30-Day Limited        |
      | 90-Day Limited        |
      | 1-Year Limited        |
      | 2-Year Limited        |
      | Lifetime Limited      |
      | Manufacturer Warranty |

  # ---------- Scenario 6: Edit an existing car part ----------
  @edit
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

  # ---------- Scenario 7: Search and filter car parts ----------
  @search @filter
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

  # ---------- Scenario 8: Verify dependent picklist behavior ----------
  @dependent_picklist
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

  # ---------- Scenario 9: Delete a car part ----------
  @delete
  Scenario: Delete a Car Part record
    Given the user is on the Car Parts list view
    And the user searches for "LED Headlight Assembly" in the list
    When the user opens the first matching record
    And the user clicks "Delete" from the record actions
    And the user confirms the deletion
    Then a success toast message "was deleted" should be displayed
    And the user should be redirected to the list view

  # ---------- Scenario 10: Validate required fields ----------
  @validation
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
      | Condition        |
