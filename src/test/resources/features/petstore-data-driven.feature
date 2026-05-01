@petstore @data-driven
Feature: Petstore API - Data-Driven Scenarios with Scenario Outlines
  As a pet store manager
  I want to validate the API with multiple data combinations
  So that I can ensure consistent behavior across different inputs

  Background:
    Given http baseUri is /api/
    And I set http headers to:
      | Accept        | application/json  |
      | Content-Type  | application/json  |

  # -------------------------------------------------------------------------
  # Scenario Outline — Create pets with various species
  # -------------------------------------------------------------------------

  Scenario Outline: Create pets of different species
    When I set http body to {"id":"<id>","name":"<name>","species":"<species>","breed":"<breed>","age":<age>,"status":"<status>"}
    And I POST /pets
    Then http response code should be 201
    And http response body path $.name should be <name>
    And http response body path $.species should be <species>
    And http response body path $.status should be <status>

    Examples: Common household pets
      | id  | name      | species | breed           | age | status    |
      | 400 | Charlie   | Dog     | Beagle          | 3   | available |
      | 401 | Mittens   | Cat     | Persian         | 5   | available |
      | 402 | Tweety    | Bird    | Canary          | 1   | available |
      | 403 | Goldie    | Fish    | Goldfish        | 2   | sold      |

    Examples: Exotic pets
      | id  | name      | species | breed           | age | status    |
      | 404 | Slither   | Reptile | Ball Python     | 4   | pending   |
      | 405 | Thumper   | Rabbit  | Holland Lop     | 1   | available |

  # -------------------------------------------------------------------------
  # Scenario Outline — Retrieve created pets and verify fields
  # -------------------------------------------------------------------------

  Scenario Outline: Retrieve and verify each created pet
    When I GET /pets/<id>
    Then http response code should be 200
    And http response body path $.id should be <id>
    And http response body path $.name should be <name>
    And http response body path $.species should be <species>

    Examples:
      | id  | name      | species |
      | 400 | Charlie   | Dog     |
      | 401 | Mittens   | Cat     |
      | 402 | Tweety    | Bird    |
      | 403 | Goldie    | Fish    |
      | 404 | Slither   | Reptile |
      | 405 | Thumper   | Rabbit  |

  # -------------------------------------------------------------------------
  # Scenario Outline — Update pet status transitions
  # -------------------------------------------------------------------------

  Scenario Outline: Update pet status
    When I set http body to {"status":"<new_status>"}
    And I PATCH /pets/<id>
    Then http response code should be 200
    And http response body path $.status should be <new_status>

    Examples: Status transitions
      | id  | new_status |
      | 400 | pending    |
      | 401 | sold       |
      | 402 | sold       |

  # -------------------------------------------------------------------------
  # Scenario Outline — Not-found for various IDs
  # -------------------------------------------------------------------------

  Scenario Outline: Return 404 for non-existent pet IDs
    When I GET /pets/<id>
    Then http response code should be 404

    Examples:
      | id      |
      | 9999    |
      | 0       |
      | abc     |

  # -------------------------------------------------------------------------
  # Cleanup
  # -------------------------------------------------------------------------

  @petstore-cleanup
  Scenario: Cleanup - Delete all data-driven test pets
    When I DELETE /pets/400
    Then http response code should be 200
    When I DELETE /pets/401
    Then http response code should be 200
    When I DELETE /pets/402
    Then http response code should be 200
    When I DELETE /pets/403
    Then http response code should be 200
    When I DELETE /pets/404
    Then http response code should be 200
    When I DELETE /pets/405
    Then http response code should be 200
