Feature: Cross-resource relationship tests for users and orders

  Background:
    Given http baseUri is /api/
    And I set http headers to:
    | Accept        | application/json  |
    | Content-Type  | application/json  |

  Scenario: Create a user for order association
    When I set http body to {"id":"200","firstName":"Diana","lastName":"Prince","age":"30","sessionIds":["99990000"]}
    And I POST /users
    Then http response code should be 201
    And http response body path $.id should be 200
    And http response body path $.firstName should be Diana
    And I store the value of http body path $.id as orderUserId in scenario scope

  Scenario: Create a first order for the user
    When I set http body to {"id":"501","userId":"200","product":"Shield","quantity":"1","price":"999.99"}
    And I POST /orders
    Then http response code should be 201
    And http response body should be valid json
    And http response body path $.id should be 501
    And http response body path $.userId should be 200
    And http response body path $.product should be Shield
    And http response body path $.quantity should be 1
    And I store the value of http body path $.id as firstOrderId in scenario scope

  Scenario: Create a second order for the same user
    When I set http body to {"id":"502","userId":"200","product":"Lasso","quantity":"2","price":"499.50"}
    And I POST /orders
    Then http response code should be 201
    And http response body should be valid json
    And http response body path $.id should be 502
    And http response body path $.userId should be 200
    And http response body path $.product should be Lasso

  Scenario: Verify all orders exist
    When I GET /orders
    Then http response code should be 200
    And http response body should be valid json
    And http response body is typed as array for path $
    And http response body is typed as array using path $ with length 2

  Scenario: Verify orders appear when querying by user
    When I GET /users/200/orders
    Then http response code should be 200
    And http response body should be valid json
    And http response body is typed as array using path $ with length 2
    And http response body path $.[0].userId should be 200
    And http response body path $.[1].userId should be 200
    And http response body should contain Shield
    And http response body should contain Lasso

  Scenario: Verify no orders for a different user
    When I GET /users/999/orders
    Then http response code should be 200
    And http response body is typed as array using path $ with length 0
    And http response body path $ should not have content

  Scenario: Retrieve a single order by id
    When I GET /orders/`$firstOrderId`
    Then http response code should be 200
    And http response body path $.id should be `$firstOrderId`
    And http response body path $.product should be Shield

  Scenario: Delete the first order and verify it is gone
    When I DELETE /orders/501
    Then http response code should be 200
    When I GET /orders/501
    Then http response code should be 404

  Scenario: Verify only one order remains for the user
    When I GET /users/200/orders
    Then http response code should be 200
    And http response body is typed as array using path $ with length 1
    And http response body path $.[0].product should be Lasso

  Scenario: Clean up - delete remaining order and user
    When I DELETE /orders/502
    Then http response code should be 200
    When I DELETE /users/200
    Then http response code should be 200
    When I GET /users/200
    Then http response code should be 404
