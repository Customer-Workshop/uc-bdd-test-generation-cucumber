Feature: Users API edge cases

  Background:
    Given http baseUri is /api/
    And I set http headers to:
      | Accept        | application/json  |
      | Content-Type  | application/json  |

  # -----------------------------------------------------------------------
  # Validation: missing required fields
  # -----------------------------------------------------------------------

  Scenario: Should return 400 when creating user with missing id
    And I set http body to {"firstName":"Clark","lastName":"Kent","age":"30"}
    And I POST /users
    Then http response code should be 400
    And http response body should be valid json
    And http response body path $.error should be Bad Request
    And http response body path $.errors.id should be id is required

  Scenario: Should return 400 when creating user with missing firstName
    And I set http body to {"id":"edge-1","lastName":"Kent","age":"30"}
    And I POST /users
    Then http response code should be 400
    And http response body should be valid json
    And http response body path $.errors.firstName should be firstName is required

  Scenario: Should return 400 when creating user with missing lastName
    And I set http body to {"id":"edge-2","firstName":"Clark","age":"30"}
    And I POST /users
    Then http response code should be 400
    And http response body should be valid json
    And http response body path $.errors.lastName should be lastName is required

  Scenario: Should return 400 when creating user with all required fields missing
    And I set http body to {"age":"25"}
    And I POST /users
    Then http response code should be 400
    And http response body should be valid json
    And http response body path $.errors.id should be id is required
    And http response body path $.errors.firstName should be firstName is required
    And http response body path $.errors.lastName should be lastName is required

  # -----------------------------------------------------------------------
  # Duplicate ID handling
  # -----------------------------------------------------------------------

  Scenario: Should create a user successfully then return 409 on duplicate
    And I set http body to {"id":"dup-1","firstName":"Diana","lastName":"Prince","age":"30"}
    And I POST /users
    Then http response code should be 201
    And http response body path $.id should be dup-1
    And http response body path $.firstName should be Diana

  Scenario: Should return 409 when creating user with duplicate ID
    And I set http body to {"id":"dup-1","firstName":"Arthur","lastName":"Curry","age":"35"}
    And I POST /users
    Then http response code should be 409
    And http response body should be valid json
    And http response body path $.error should be Conflict
    And http response body path $.message should be User with id dup-1 already exists

  # -----------------------------------------------------------------------
  # Input validation: edge-case values
  # -----------------------------------------------------------------------

  Scenario: Should accept user with age zero
    And I set http body to {"id":"edge-3","firstName":"Baby","lastName":"Doe","age":"0"}
    And I POST /users
    Then http response code should be 201
    And http response body path $.age should be 0

  Scenario: Should accept user with empty sessionIds
    And I set http body to {"id":"edge-4","firstName":"Solo","lastName":"Rider","age":"25","sessionIds":[]}
    And I POST /users
    Then http response code should be 201
    And http response body path $.id should be edge-4

  Scenario: Should accept user with special characters in name
    And I set http body to {"id":"edge-5","firstName":"Jean-Luc","lastName":"O'Brien","age":"50"}
    And I POST /users
    Then http response code should be 201
    And http response body path $.firstName should be Jean-Luc

  # -----------------------------------------------------------------------
  # Pagination
  # -----------------------------------------------------------------------

  Scenario: Should return paginated results
    And I set http query parameter page to 0
    And I set http query parameter size to 2
    When I GET /users
    Then http response code should be 200
    And http response body should be valid json
    And http response body path $.page should be 0
    And http response body path $.size should be 2
    And http response body is typed as array for path $.content
    And http response body is typed as array using path $.content with length 2

  Scenario: Should return second page of paginated results
    And I set http query parameter page to 1
    And I set http query parameter size to 2
    When I GET /users
    Then http response code should be 200
    And http response body should be valid json
    And http response body path $.page should be 1
    And http response body path $.totalPages should be 2

  Scenario: Should return empty page when beyond range
    And I set http query parameter page to 99
    And I set http query parameter size to 2
    When I GET /users
    Then http response code should be 200
    And http response body should be valid json
    And http response body is typed as array using path $.content with length 0

  # -----------------------------------------------------------------------
  # Sorting
  # -----------------------------------------------------------------------

  Scenario: Should sort users by firstName ascending
    And I set http query parameter sort to firstName
    When I GET /users
    Then http response code should be 200
    And http response body should be valid json
    And http response body is typed as array for path $

  Scenario: Should sort users by age descending
    And I set http query parameter sort to -age
    When I GET /users
    Then http response code should be 200
    And http response body should be valid json
    And http response body is typed as array for path $
    And http response body path $.[0].age should be 50

  # -----------------------------------------------------------------------
  # Cleanup
  # -----------------------------------------------------------------------

  Scenario: Cleanup edge case users
    When I DELETE /users/dup-1
    Then http response code should be 200
    When I DELETE /users/edge-3
    Then http response code should be 200
    When I DELETE /users/edge-4
    Then http response code should be 200
    When I DELETE /users/edge-5
    Then http response code should be 200
    When I GET /users
    Then http response body is typed as array using path $ with length 0
