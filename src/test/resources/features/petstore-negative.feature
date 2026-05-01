@petstore @negative
Feature: Petstore API - Negative Scenarios
  As a pet store manager
  I want the API to properly reject invalid requests
  So that data integrity is maintained

  Background:
    Given http baseUri is /api/
    And I set http headers to:
      | Accept        | application/json  |
      | Content-Type  | application/json  |

  # -------------------------------------------------------------------------
  # Missing required fields
  # -------------------------------------------------------------------------

  Scenario: Reject pet creation without a name
    When I set http body to {"id":"100","species":"Dog","breed":"Poodle","age":3}
    And I POST /pets
    Then http response code should be 400

  Scenario: Reject pet creation without a species
    When I set http body to {"id":"101","name":"Rex","breed":"Shepherd","age":2}
    And I POST /pets
    Then http response code should be 400

  Scenario: Reject pet creation with empty name
    When I set http body to {"id":"102","name":"","species":"Dog","age":1}
    And I POST /pets
    Then http response code should be 400

  Scenario: Reject pet creation with blank species
    When I set http body to {"id":"103","name":"Fido","species":"  ","age":4}
    And I POST /pets
    Then http response code should be 400

  # -------------------------------------------------------------------------
  # Not-found cases
  # -------------------------------------------------------------------------

  Scenario: Return 404 when getting a non-existent pet
    When I GET /pets/99999
    Then http response code should be 404
    And http response body path $ should not have content

  Scenario: Return 404 when updating a non-existent pet
    When I set http body to {"id":"99999","name":"Ghost","species":"Unknown","age":0}
    And I PUT /pets/99999
    Then http response code should be 404

  Scenario: Return 404 when patching a non-existent pet
    When I set http body to {"name":"Ghost"}
    And I PATCH /pets/99999
    Then http response code should be 404

  Scenario: Return 404 when deleting a non-existent pet
    When I DELETE /pets/99999
    Then http response code should be 404

  # -------------------------------------------------------------------------
  # Duplicate / Conflict
  # -------------------------------------------------------------------------

  Scenario: Setup - Create a pet for conflict testing
    When I set http body to {"id":"200","name":"Luna","species":"Cat","breed":"Siamese","age":2,"status":"available"}
    And I POST /pets
    Then http response code should be 201
    And http response body path $.id should be 200

  Scenario: Reject creating a pet with a duplicate ID
    When I set http body to {"id":"200","name":"DuplicateLuna","species":"Cat","age":3}
    And I POST /pets
    Then http response code should be 409

  # -------------------------------------------------------------------------
  # Filter returns empty
  # -------------------------------------------------------------------------

  Scenario: Return empty list when filtering by non-existent status
    And I set http query parameter status to nonexistent_status
    When I GET /pets
    Then http response code should be 200
    And http response body is typed as array using path $ with length 0

  Scenario: Return empty list when filtering by non-existent species
    And I set http query parameter species to Unicorn
    When I GET /pets
    Then http response code should be 200
    And http response body is typed as array using path $ with length 0

  # -------------------------------------------------------------------------
  # Cleanup
  # -------------------------------------------------------------------------

  @petstore-cleanup
  Scenario: Cleanup - Remove conflict test data
    When I DELETE /pets/200
    Then http response code should be 200
