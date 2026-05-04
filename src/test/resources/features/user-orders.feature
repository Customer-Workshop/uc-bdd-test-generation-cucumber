Feature: Cross-resource relationship tests - Users and Orders

  Background:
    Given http baseUri is /api/
    And I set http headers to:
      | Accept        | application/json  |
      | Content-Type  | application/json  |

  Scenario: Create a user for order testing
    When I authenticate with login/password tstark/marvel
    And I set http body to {"id":"200","firstName":"Diana","lastName":"Prince","age":"30"}
    And I POST /users
    Then http response code should be 201
    And http response body path $.id should be 200
    And http response body path $.firstName should be Diana
    And http response body path $.lastName should be Prince

  Scenario: Create a second user for order testing
    When I set http body to {"id":"201","firstName":"Barry","lastName":"Allen","age":"28"}
    And I POST /users
    Then http response code should be 201
    And http response body path $.id should be 201
    And http response body path $.firstName should be Barry

  Scenario: Create first order for user Diana
    When I set http body to {"id":"order-1","userId":"200","product":"Shield","quantity":1,"price":999.99,"status":"pending"}
    And I POST /orders
    Then http response code should be 201
    And http response body should be valid json
    And http response body path $.id should be order-1
    And http response body path $.userId should be 200
    And http response body path $.product should be Shield
    And http response body path $.quantity should be 1
    And http response body path $.status should be pending

  Scenario: Create second order for user Diana
    When I set http body to {"id":"order-2","userId":"200","product":"Lasso","quantity":2,"price":499.50,"status":"shipped"}
    And I POST /orders
    Then http response code should be 201
    And http response body path $.id should be order-2
    And http response body path $.userId should be 200
    And http response body path $.product should be Lasso
    And http response body path $.quantity should be 2
    And http response body path $.status should be shipped

  Scenario: Create order for user Barry
    When I set http body to {"id":"order-3","userId":"201","product":"Speed Boots","quantity":1,"price":750.00,"status":"pending"}
    And I POST /orders
    Then http response code should be 201
    And http response body path $.id should be order-3
    And http response body path $.userId should be 201
    And http response body path $.product should be Speed Boots

  Scenario: Verify orders for user Diana are returned when querying by userId
    And I set http query parameter userId to 200
    When I GET /orders
    Then http response code should be 200
    And http response body should be valid json
    And http response body is typed as array using path $ with length 2
    And http response body path $.[0].id should be order-1
    And http response body path $.[0].product should be Shield
    And http response body path $.[1].id should be order-2
    And http response body path $.[1].product should be Lasso

  Scenario: Verify orders for user Barry are returned when querying by userId
    And I set http query parameter userId to 201
    When I GET /orders
    Then http response code should be 200
    And http response body should be valid json
    And http response body is typed as array using path $ with length 1
    And http response body path $.[0].id should be order-3
    And http response body path $.[0].product should be Speed Boots
    And http response body path $.[0].userId should be 201

  Scenario: Verify all orders are returned without filter
    When I GET /orders
    Then http response code should be 200
    And http response body should be valid json
    And http response body is typed as array using path $ with length 3

  Scenario: Verify order can be retrieved by ID
    When I GET /orders/order-1
    Then http response code should be 200
    And http response body should be valid json
    And http response body path $.id should be order-1
    And http response body path $.userId should be 200
    And http response body path $.product should be Shield

  Scenario: Creating order for non-existent user fails
    When I set http body to {"id":"order-99","userId":"999","product":"Invisible Jet","quantity":1,"price":5000.00,"status":"pending"}
    And I POST /orders
    Then http response code should be 400

  Scenario: Delete an order and verify it is gone
    When I DELETE /orders/order-1
    Then http response code should be 200
    And I GET /orders/order-1
    Then http response code should be 404

  Scenario: Verify Diana now has one fewer order
    And I set http query parameter userId to 200
    When I GET /orders
    Then http response code should be 200
    And http response body is typed as array using path $ with length 1
    And http response body path $.[0].id should be order-2

  Scenario: Cleanup - delete remaining orders and users
    When I DELETE /orders/order-2
    Then http response code should be 200
    And I DELETE /orders/order-3
    Then http response code should be 200
    And I DELETE /users/200
    Then http response code should be 200
    And I DELETE /users/201
    Then http response code should be 200
    When I GET /orders
    Then http response code should be 200
    And http response body is typed as array using path $ with length 0
