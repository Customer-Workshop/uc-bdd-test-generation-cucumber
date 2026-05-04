Feature: Users API edge case tests

  Background:
    Given http baseUri is /api/
    And I set Accept-Language http header to en-US
    And I set http headers to:
      | Accept        | application/json  |
      | Content-Type  | application/json  |

  # --- Validation: missing required fields ---

  Scenario: Create user with missing id should return 400
    When I set http body to {"firstName":"Clark","lastName":"Kent","age":"30"}
    And I POST /users
    Then http response code should be 400
    And http response body path $.message should be id is required

  Scenario: Create user with empty id should return 400
    When I set http body to {"id":"","firstName":"Clark","lastName":"Kent","age":"30"}
    And I POST /users
    Then http response code should be 400
    And http response body path $.message should be id is required

  Scenario: Create user with missing firstName should return 400
    When I set http body to {"id":"100","lastName":"Kent","age":"30"}
    And I POST /users
    Then http response code should be 400
    And http response body path $.message should be firstName is required

  Scenario: Create user with missing lastName should return 400
    When I set http body to {"id":"101","firstName":"Clark","age":"30"}
    And I POST /users
    Then http response code should be 400
    And http response body path $.message should be lastName is required

  # --- Validation: age boundaries ---

  Scenario: Create user with negative age should return 400
    When I set http body to {"id":"102","firstName":"Clark","lastName":"Kent","age":"-1"}
    And I POST /users
    Then http response code should be 400
    And http response body should contain age range invalid

  Scenario: Create user with age over 150 should return 400
    When I set http body to {"id":"103","firstName":"Clark","lastName":"Kent","age":"200"}
    And I POST /users
    Then http response code should be 400
    And http response body should contain age range invalid

  # --- Duplicate ID ---

  Scenario: Create user with duplicate id should return 409
    When I set http body to {"id":"200","firstName":"Diana","lastName":"Prince","age":"30"}
    And I POST /users
    Then http response code should be 201
    And http response body path $.id should be 200
    When I set http body to {"id":"200","firstName":"Steve","lastName":"Trevor","age":"35"}
    And I POST /users
    Then http response code should be 409
    And http response body path $.error should be Conflict
    And http response body path $.message should be User with id 200 already exists

  # --- Pagination ---

  Scenario: Paginate users list
    When I set http body to {"id":"301","firstName":"Alice","lastName":"Anderson","age":"25"}
    And I POST /users
    Then http response code should be 201
    When I set http body to {"id":"302","firstName":"Bob","lastName":"Brown","age":"35"}
    And I POST /users
    Then http response code should be 201
    When I set http body to {"id":"303","firstName":"Charlie","lastName":"Clark","age":"45"}
    And I POST /users
    Then http response code should be 201
    When I GET /users?page=0&size=2
    Then http response code should be 200
    And http response body is typed as array using path $ with length 2
    When I GET /users?page=1&size=2
    Then http response code should be 200
    And http response body is typed as array for path $

  Scenario: Paginate with page beyond available data returns empty
    When I GET /users?page=100&size=10
    Then http response code should be 200
    And http response body is typed as array using path $ with length 0

  Scenario: Invalid pagination parameters return 400
    When I GET /users?page=-1&size=10
    Then http response code should be 400
    And http response body should contain invalid pagination

  # --- Sorting ---

  Scenario: Sort users by firstName ascending
    When I GET /users?sort=firstName&direction=asc
    Then http response code should be 200
    And http response body should be valid json
    And http response body is typed as array for path $

  Scenario: Sort users by age descending
    When I GET /users?sort=age&direction=desc
    Then http response code should be 200
    And http response body should be valid json
    And http response body is typed as array for path $

  # --- Cleanup ---

  Scenario: Clean up edge case test users
    When I DELETE /users/200
    Then http response code should be 200
    When I DELETE /users/301
    Then http response code should be 200
    When I DELETE /users/302
    Then http response code should be 200
    When I DELETE /users/303
    Then http response code should be 200
