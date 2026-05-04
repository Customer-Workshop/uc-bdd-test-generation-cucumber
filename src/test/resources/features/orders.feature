Feature: Orders API tests

  Background:
    Given http baseUri is /api/
    And I set Accept-Language http header to en-US
    And I set http headers to:
      | Accept        | application/json  |
      | Content-Type  | application/json  |

  # --- Validation ---

  Scenario: Create order with missing id should return 400
    When I set http body to {"userId":"user1","items":[{"productName":"Widget","quantity":1,"price":9.99}]}
    And I POST /orders
    Then http response code should be 400
    And http response body path $.message should be id is required

  Scenario: Create order with missing userId should return 400
    When I set http body to {"id":"ord-1","items":[{"productName":"Widget","quantity":1,"price":9.99}]}
    And I POST /orders
    Then http response code should be 400
    And http response body path $.message should be userId is required

  Scenario: Create order with empty items should return 400
    When I set http body to {"id":"ord-1","userId":"user1","items":[]}
    And I POST /orders
    Then http response code should be 400
    And http response body should contain items required

  Scenario: Create order without items field should return 400
    When I set http body to {"id":"ord-1","userId":"user1"}
    And I POST /orders
    Then http response code should be 400
    And http response body should contain items required

  # --- CRUD Operations ---

  Scenario: Create a new order
    When I set http body to {"id":"ord-100","userId":"user1","items":[{"productName":"Laptop","quantity":1,"price":999.99},{"productName":"Mouse","quantity":2,"price":25.50}]}
    And I POST /orders
    Then http response code should be 201
    And http response body path $.id should be ord-100
    And http response body path $.userId should be user1
    And http response body path $.status should be PENDING
    And http response body path $.totalAmount should be 1050.99
    And http response body is typed as array using path $.items with length 2

  Scenario: Create a second order
    When I set http body to {"id":"ord-101","userId":"user2","status":"CONFIRMED","items":[{"productName":"Keyboard","quantity":1,"price":75.00}]}
    And I POST /orders
    Then http response code should be 201
    And http response body path $.id should be ord-101
    And http response body path $.userId should be user2
    And http response body path $.status should be CONFIRMED
    And http response body path $.totalAmount should be 75.0

  Scenario: Create order with duplicate id should return 409
    When I set http body to {"id":"ord-100","userId":"user3","items":[{"productName":"Tablet","quantity":1,"price":500.00}]}
    And I POST /orders
    Then http response code should be 409
    And http response body path $.error should be Conflict
    And http response body path $.message should be Order with id ord-100 already exists

  Scenario: Get an existing order by id
    When I GET /orders/ord-100
    Then http response code should be 200
    And http response body path $.id should be ord-100
    And http response body path $.userId should be user1
    And http response body path $.status should be PENDING
    And http response body path $.totalAmount should be 1050.99

  Scenario: Get non-existent order should return 404
    When I GET /orders/ord-999
    Then http response code should be 404

  Scenario: Get all orders
    When I GET /orders
    Then http response code should be 200
    And http response body is typed as array using path $ with length 2

  Scenario: Filter orders by userId
    When I GET /orders?userId=user1
    Then http response code should be 200
    And http response body is typed as array using path $ with length 1
    And http response body path $.[0].id should be ord-100

  Scenario: Filter orders by status
    When I GET /orders?status=CONFIRMED
    Then http response code should be 200
    And http response body is typed as array using path $ with length 1
    And http response body path $.[0].id should be ord-101

  Scenario: Filter with non-matching criteria returns empty list
    When I GET /orders?userId=nonexistent
    Then http response code should be 200
    And http response body is typed as array using path $ with length 0

  # --- Update Operations ---

  Scenario: Update an existing order
    When I set http body to {"userId":"user1","status":"SHIPPED","items":[{"productName":"Laptop","quantity":1,"price":999.99},{"productName":"Mouse","quantity":3,"price":25.50}]}
    And I PUT /orders/ord-100
    Then http response code should be 200
    And http response body path $.status should be SHIPPED
    And http response body path $.totalAmount should be 1076.49

  Scenario: Update non-existent order should return 404
    When I set http body to {"userId":"user1","status":"SHIPPED"}
    And I PUT /orders/ord-999
    Then http response code should be 404

  Scenario: Update order with invalid status should return 400
    When I set http body to {"status":"INVALID_STATUS"}
    And I PUT /orders/ord-100
    Then http response code should be 400
    And http response body should contain Invalid status

  # --- Patch Status ---

  Scenario: Patch order status
    When I set http body to {"status":"DELIVERED"}
    And I PATCH /orders/ord-100/status
    Then http response code should be 200
    And http response body path $.status should be DELIVERED

  Scenario: Patch order status with invalid value should return 400
    When I set http body to {"status":"UNKNOWN"}
    And I PATCH /orders/ord-100/status
    Then http response code should be 400
    And http response body should contain Invalid status

  Scenario: Patch non-existent order status should return 404
    When I set http body to {"status":"CANCELLED"}
    And I PATCH /orders/ord-999/status
    Then http response code should be 404

  # --- Delete Operations ---

  Scenario: Delete non-existent order should return 404
    When I DELETE /orders/ord-999
    Then http response code should be 404

  Scenario: Delete existing orders
    When I DELETE /orders/ord-100
    Then http response code should be 200
    When I DELETE /orders/ord-101
    Then http response code should be 200
    When I GET /orders
    Then http response code should be 200
    And http response body is typed as array using path $ with length 0
