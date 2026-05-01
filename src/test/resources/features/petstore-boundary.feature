@petstore @boundary
Feature: Petstore API - Boundary Scenarios
  As a pet store manager
  I want the API to handle edge cases and boundary values correctly
  So that the system remains stable under unusual input

  Background:
    Given http baseUri is /api/
    And I set http headers to:
      | Accept        | application/json  |
      | Content-Type  | application/json  |

  # -------------------------------------------------------------------------
  # Age boundary values
  # -------------------------------------------------------------------------

  Scenario: Create a pet with age zero (newborn)
    When I set http body to {"id":"300","name":"Newborn","species":"Hamster","age":0,"status":"available"}
    And I POST /pets
    Then http response code should be 201
    And http response body path $.age should be 0

  Scenario: Create a pet with a large age value
    When I set http body to {"id":"301","name":"Tortoise","species":"Reptile","age":150,"status":"available"}
    And I POST /pets
    Then http response code should be 201
    And http response body path $.age should be 150

  # -------------------------------------------------------------------------
  # Name boundary values
  # -------------------------------------------------------------------------

  Scenario: Create a pet with a single-character name
    When I set http body to {"id":"302","name":"X","species":"Fish","age":1,"status":"available"}
    And I POST /pets
    Then http response code should be 201
    And http response body path $.name should be X

  Scenario: Create a pet with a very long name
    When I set http body to {"id":"303","name":"Abcdefghijklmnopqrstuvwxyz-Abcdefghijklmnopqrstuvwxyz-Abcdefghijklmnopqrstuvwxyz-Abcdefghijklmnopqrstuvwxyz","species":"Dog","age":5,"status":"available"}
    And I POST /pets
    Then http response code should be 201
    And http response body path $.name should be Abcdefghijklmnopqrstuvwxyz-Abcdefghijklmnopqrstuvwxyz-Abcdefghijklmnopqrstuvwxyz-Abcdefghijklmnopqrstuvwxyz

  # -------------------------------------------------------------------------
  # Special characters
  # -------------------------------------------------------------------------

  Scenario: Create a pet with special characters in the name
    When I set http body to {"id":"304","name":"Mr. Whiskers III","species":"Cat","age":7,"status":"available"}
    And I POST /pets
    Then http response code should be 201
    And http response body path $.name should be Mr. Whiskers III

  # -------------------------------------------------------------------------
  # Tags boundary
  # -------------------------------------------------------------------------

  Scenario: Create a pet with an empty tags list
    When I set http body to {"id":"305","name":"TaglessPet","species":"Bird","age":2,"status":"available","tags":[]}
    And I POST /pets
    Then http response code should be 201
    And http response body is typed as array using path $.tags with length 0

  Scenario: Create a pet with many tags
    When I set http body to {"id":"306","name":"TaggedPet","species":"Dog","age":4,"status":"available","tags":["tag1","tag2","tag3","tag4","tag5","tag6","tag7","tag8","tag9","tag10"]}
    And I POST /pets
    Then http response code should be 201
    And http response body is typed as array using path $.tags with length 10

  # -------------------------------------------------------------------------
  # Pagination boundary
  # -------------------------------------------------------------------------

  Scenario: Request page zero returns results
    And I set http query parameter page to 0
    And I set http query parameter size to 2
    When I GET /pets
    Then http response code should be 200
    And http response body is typed as array using path $ with length 2

  Scenario: Request a page beyond available data returns empty list
    And I set http query parameter page to 100
    And I set http query parameter size to 10
    When I GET /pets
    Then http response code should be 200
    And http response body is typed as array using path $ with length 0

  Scenario: Request with page size of 1 returns single result
    And I set http query parameter page to 0
    And I set http query parameter size to 1
    When I GET /pets
    Then http response code should be 200
    And http response body is typed as array using path $ with length 1

  # -------------------------------------------------------------------------
  # Empty collection
  # -------------------------------------------------------------------------

  @petstore-cleanup
  Scenario: Cleanup boundary test data and verify empty collection
    When I DELETE /pets/300
    Then http response code should be 200
    When I DELETE /pets/301
    Then http response code should be 200
    When I DELETE /pets/302
    Then http response code should be 200
    When I DELETE /pets/303
    Then http response code should be 200
    When I DELETE /pets/304
    Then http response code should be 200
    When I DELETE /pets/305
    Then http response code should be 200
    When I DELETE /pets/306
    Then http response code should be 200
    When I GET /pets
    Then http response code should be 200
    And http response body is typed as array using path $ with length 0
    And http response body path $ should not have content
