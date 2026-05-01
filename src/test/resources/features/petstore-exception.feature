@petstore @exception
Feature: Petstore API - Exception and Edge-Case Scenarios
  As a pet store manager
  I want the API to handle exceptional conditions gracefully
  So that clients receive meaningful error responses

  Background:
    Given http baseUri is /api/
    And I set http headers to:
      | Accept        | application/json  |
      | Content-Type  | application/json  |

  # -------------------------------------------------------------------------
  # Not-found edge cases
  # -------------------------------------------------------------------------

  Scenario: GET a pet with an alphanumeric ID that does not exist
    When I GET /pets/abc-123-xyz
    Then http response code should be 404

  Scenario: DELETE a pet that was already deleted
    When I set http body to {"id":"500","name":"TempPet","species":"Dog","age":1,"status":"available"}
    And I POST /pets
    Then http response code should be 201
    When I DELETE /pets/500
    Then http response code should be 200
    When I DELETE /pets/500
    Then http response code should be 404

  # -------------------------------------------------------------------------
  # Concurrent-style update scenarios (sequential simulation)
  # -------------------------------------------------------------------------

  Scenario: Sequential updates produce the last-write-wins result
    When I set http body to {"id":"501","name":"Racer","species":"Horse","age":5,"status":"available"}
    And I POST /pets
    Then http response code should be 201
    When I set http body to {"id":"501","name":"Racer","species":"Horse","age":5,"status":"sold"}
    And I PUT /pets/501
    Then http response code should be 200
    And http response body path $.status should be sold
    When I set http body to {"id":"501","name":"Racer","species":"Horse","age":5,"status":"pending"}
    And I PUT /pets/501
    Then http response code should be 200
    And http response body path $.status should be pending
    When I GET /pets/501
    Then http response code should be 200
    And http response body path $.status should be pending

  # -------------------------------------------------------------------------
  # Create-Read-Update-Delete lifecycle in a single scenario
  # -------------------------------------------------------------------------

  Scenario: Full CRUD lifecycle for a single pet
    # Create
    When I set http body to {"id":"502","name":"Lifecycle","species":"Cat","breed":"Tabby","age":3,"status":"available","tags":["test"]}
    And I POST /pets
    Then http response code should be 201
    And http response body path $.name should be Lifecycle
    # Read
    When I GET /pets/502
    Then http response code should be 200
    And http response body path $.breed should be Tabby
    # Update
    When I set http body to {"id":"502","name":"Lifecycle-Updated","species":"Cat","breed":"Tabby","age":4,"status":"sold","tags":["test","updated"]}
    And I PUT /pets/502
    Then http response code should be 200
    And http response body path $.name should be Lifecycle-Updated
    And http response body path $.age should be 4
    # Partial Update
    When I set http body to {"status":"available"}
    And I PATCH /pets/502
    Then http response code should be 200
    And http response body path $.status should be available
    # Delete
    When I DELETE /pets/502
    Then http response code should be 200
    When I GET /pets/502
    Then http response code should be 404

  # -------------------------------------------------------------------------
  # Re-creation after deletion
  # -------------------------------------------------------------------------

  Scenario: Re-create a pet after deletion succeeds
    When I set http body to {"id":"503","name":"Phoenix","species":"Bird","age":1,"status":"available"}
    And I POST /pets
    Then http response code should be 201
    When I DELETE /pets/503
    Then http response code should be 200
    When I set http body to {"id":"503","name":"Phoenix Reborn","species":"Bird","age":1,"status":"available"}
    And I POST /pets
    Then http response code should be 201
    And http response body path $.name should be Phoenix Reborn
    When I DELETE /pets/503
    Then http response code should be 200

  # -------------------------------------------------------------------------
  # Idempotency check on GET
  # -------------------------------------------------------------------------

  Scenario: Multiple GETs return the same result
    When I set http body to {"id":"504","name":"Stable","species":"Dog","age":2,"status":"available"}
    And I POST /pets
    Then http response code should be 201
    When I GET /pets/504
    Then http response code should be 200
    And http response body path $.name should be Stable
    When I GET /pets/504
    Then http response code should be 200
    And http response body path $.name should be Stable
    When I GET /pets/504
    Then http response code should be 200
    And http response body path $.name should be Stable

  # -------------------------------------------------------------------------
  # Cleanup
  # -------------------------------------------------------------------------

  @petstore-cleanup
  Scenario: Cleanup exception test data
    When I DELETE /pets/501
    Then http response code should be 200
    When I DELETE /pets/504
    Then http response code should be 200
