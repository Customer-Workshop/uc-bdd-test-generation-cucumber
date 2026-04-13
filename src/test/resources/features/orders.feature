Feature: Orders api tests

  Background:
    Given http baseUri is /api/
    And I set http headers to:
    | Accept        | application/json  |
    | Content-Type  | application/json  |

  Scenario: Create a new order
    When I set http body to {"id":"1","product":"Laptop","quantity":2,"price":999.99,"status":"pending","customerId":"C100","tags":["electronics","sale"]}
    And I POST /orders
    Then http response code should be 201
    And http response body should be valid json
    And http response body path $.id should be 1
    And http response body path $.product should be Laptop
    And http response body path $.quantity should be 2
    And http response body path $.price should be 999.99
    And http response body path $.status should be pending
    And http response body path $.customerId should be C100
    And http response body path $.tags should be ["electronics", "sale"]
    And I store the value of http body path $.id as orderId in scenario scope

  Scenario: Create a second order
    When I set http body to {"id":"2","product":"Mouse","quantity":5,"price":29.99,"status":"shipped","customerId":"C200","tags":["accessories"]}
    And I POST /orders
    Then http response code should be 201
    And http response body path $.id should be 2
    And http response body path $.product should be Mouse
    And http response body path $.status should be shipped
    And http response body path $.customerId should be C200

  Scenario: Create a third order with default status
    When I set http body to {"id":"3","product":"Keyboard","quantity":1,"price":79.99,"customerId":"C100"}
    And I POST /orders
    Then http response code should be 201
    And http response body path $.status should be pending

  Scenario: Reject duplicate order
    When I set http body to {"id":"1","product":"Duplicate","quantity":1,"price":10.00}
    And I POST /orders
    Then http response code should be 400

  Scenario: Get all orders
    When I GET /orders
    Then http response code should be 200
    And http response body should be valid json
    And http response body is typed as array for path $
    And http response body is typed as array using path $ with length 3
    And http response body path $.[0].id should be `$orderId`
    And http response body path $.[0].product should be Laptop
    And http response body path $.[1].product should be Mouse

  Scenario: Filter orders by status
    And I set http query parameter status to pending
    When I GET /orders
    Then http response code should be 200
    And http response body is typed as array using path $ with length 2
    And http response body path $.[0].product should be Laptop
    And http response body path $.[1].product should be Keyboard

  Scenario: Filter orders by customerId
    And I set http query parameter customerId to C200
    When I GET /orders
    Then http response code should be 200
    And http response body is typed as array using path $ with length 1
    And http response body path $.[0].product should be Mouse

  Scenario: Get order by id
    When I GET /orders/1
    Then http response code should be 200
    And http response body should be valid json
    And http response body path $.id should be 1
    And http response body path $.product should be Laptop
    And http response body path $.quantity should be 2
    And http response body path $.tags should be ["electronics", "sale"]
    And http response body should contain Laptop

  Scenario: Get nonexistent order returns 404
    When I GET /orders/99999
    Then http response code should be 404
    And http response body path $ should not have content

  Scenario: Update an order
    When I set http body to {"id":"1","product":"Laptop Pro","quantity":3,"price":1299.99,"status":"processing","customerId":"C100","tags":["electronics","premium"]}
    And I PUT /orders/1
    Then http response code should be 200
    And http response body path $.product should be Laptop Pro
    And http response body path $.quantity should be 3
    And http response body path $.price should be 1299.99
    And http response body path $.status should be processing
    When I GET /orders/1
    Then http response code should be 200
    And http response body path $.product should be Laptop Pro
    And http response body path $.quantity should be 3

  Scenario: Update nonexistent order returns 404
    When I set http body to {"id":"999","product":"Nothing","quantity":0,"price":0}
    And I PUT /orders/999
    Then http response code should be 404

  Scenario: Patch order status
    When I set http body to {"status":"delivered"}
    And I PATCH /orders/2
    Then http response code should be 200
    And http response body path $.status should be delivered
    And http response body path $.product should be Mouse
    When I GET /orders/2
    Then http response code should be 200
    And http response body path $.status should be delivered

  Scenario: Patch nonexistent order returns 404
    When I set http body to {"status":"cancelled"}
    And I PATCH /orders/99999
    Then http response code should be 404

  Scenario: Delete nonexistent order returns 404
    When I DELETE /orders/99999
    Then http response code should be 404

  Scenario: Delete orders and verify cleanup
    When I DELETE /orders/1
    Then http response code should be 200
    And I DELETE /orders/2
    Then http response code should be 200
    And I DELETE /orders/3
    Then http response code should be 200
    And I GET /orders
    And http response body is typed as array using path $ with length 0
    And http response body path $ should not have content
