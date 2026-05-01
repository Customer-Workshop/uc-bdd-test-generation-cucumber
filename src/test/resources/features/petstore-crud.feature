@petstore
Feature: Petstore API - CRUD Operations
  As a pet store manager
  I want to manage pets through the REST API
  So that I can maintain an accurate inventory of available animals

  Background:
    Given http baseUri is /api/
    And I set http headers to:
      | Accept        | application/json  |
      | Content-Type  | application/json  |

  # -------------------------------------------------------------------------
  # Positive Scenarios — Create
  # -------------------------------------------------------------------------

  Scenario: Create a new pet with all fields
    When I set http body to {"id":"1","name":"Max","species":"Dog","breed":"Labrador","age":5,"status":"available","tags":["friendly","vaccinated"]}
    And I POST /pets
    Then http response code should be 201
    And http response header Content-Type should be application/json
    And http response body should be valid json
    And http response body path $.id should be 1
    And http response body path $.name should be Max
    And http response body path $.species should be Dog
    And http response body path $.breed should be Labrador
    And http response body path $.age should be 5
    And http response body path $.status should be available
    And http response body path $.tags should be ["friendly","vaccinated"]
    And I store the value of http body path $.id as petId in scenario scope

  Scenario: Create a pet with minimal required fields
    When I set http body to {"id":"2","name":"Whiskers","species":"Cat","age":2}
    And I POST /pets
    Then http response code should be 201
    And http response body path $.id should be 2
    And http response body path $.name should be Whiskers
    And http response body path $.species should be Cat
    And http response body path $.status should be available

  Scenario: Create a pet using a JSON fixture file
    When I set http body with file fixtures/golden-retriever.pet.json
    And I POST /pets
    Then http response code should be 201
    And http response body path $.id should be 3
    And http response body path $.name should be Buddy
    And http response body path $.species should be Dog
    And http response body path $.breed should be Golden Retriever
    And http response body path $.tags should be ["friendly","trained"]

  # -------------------------------------------------------------------------
  # Positive Scenarios — Read
  # -------------------------------------------------------------------------

  Scenario: Get a single pet by ID
    When I GET /pets/1
    Then http response code should be 200
    And http response header Content-Type should be application/json
    And http response body should be valid json
    And http response body path $.id should be 1
    And http response body path $.name should be Max
    And http response body path $.species should be Dog

  Scenario: List all pets
    When I GET /pets
    Then http response code should be 200
    And http response body should be valid json
    And http response body is typed as array for path $
    And http response body is typed as array using path $ with length 3
    And http response body path $.[0].id should be 1
    And http response body path $.[0].name should be Max
    And http response body path $.[1].id should be 2
    And http response body path $.[2].id should be 3

  Scenario: Verify stored scenario variable is accessible
    When I GET /pets/`$petId`
    Then http response code should be 200
    And http response body path $.id should be `$petId`
    And http value of scenario variable petId should be 1

  # -------------------------------------------------------------------------
  # Positive Scenarios — Update (PUT)
  # -------------------------------------------------------------------------

  Scenario: Full update of an existing pet
    When I set http body to {"id":"1","name":"Max","species":"Dog","breed":"Labrador","age":6,"status":"sold","tags":["friendly","senior"]}
    And I PUT /pets/1
    Then http response code should be 200
    And http response body path $.age should be 6
    And http response body path $.status should be sold
    When I GET /pets/1
    Then http response code should be 200
    And http response body path $.age should be 6
    And http response body path $.status should be sold

  # -------------------------------------------------------------------------
  # Positive Scenarios — Partial Update (PATCH)
  # -------------------------------------------------------------------------

  Scenario: Partial update of a pet name
    When I set http body to {"name":"Maxwell"}
    And I PATCH /pets/1
    Then http response code should be 200
    And http response body path $.name should be Maxwell
    And http response body path $.species should be Dog

  Scenario: Partial update of a pet status
    When I set http body to {"status":"pending"}
    And I PATCH /pets/1
    Then http response code should be 200
    And http response body path $.status should be pending

  # -------------------------------------------------------------------------
  # Positive Scenarios — Filter / Search
  # -------------------------------------------------------------------------

  Scenario: Filter pets by status
    And I set http query parameter status to available
    When I GET /pets
    Then http response code should be 200
    And http response body should be valid json
    And http response body is typed as array using path $ with length 2
    And http response body path $.[0].name should be Whiskers

  Scenario: Filter pets by species
    And I set http query parameter species to Cat
    When I GET /pets
    Then http response code should be 200
    And http response body is typed as array using path $ with length 1
    And http response body path $.[0].name should be Whiskers

  Scenario: Verify response headers contain pagination metadata
    When I GET /pets
    Then http response code should be 200
    And http response header X-Total-Count should exist
    And http response header X-Page should exist
    And http response header X-Page-Size should exist

  # -------------------------------------------------------------------------
  # Positive Scenarios — Delete
  # -------------------------------------------------------------------------

  Scenario: Delete a pet
    When I DELETE /pets/2
    Then http response code should be 200
    When I GET /pets/2
    Then http response code should be 404

  # -------------------------------------------------------------------------
  # Cleanup
  # -------------------------------------------------------------------------

  @petstore-cleanup
  Scenario: Cleanup - Delete remaining pets
    When I DELETE /pets/1
    Then http response code should be 200
    When I DELETE /pets/3
    Then http response code should be 200
    When I GET /pets
    Then http response code should be 200
    And http response body is typed as array using path $ with length 0
