Feature: Orders API tests

  Background:
    Given http baseUri is /api/
    And I set http headers to:
      | Accept        | application/json  |
      | Content-Type  | application/json  |

  # ── Create order ─────────────────────────────────────────────────

  Scenario Outline: Create orders with valid data
    When I set http body to {"id":"<id>","userId":"<userId>","product":"<product>","quantity":<quantity>,"price":<price>}
    And I POST /orders
    Then http response code should be 201
    And http response body path $.id should be <id>
    And http response body path $.userId should be <userId>
    And http response body path $.product should be <product>
    And http response body path $.quantity should be <quantity>
    And http response body path $.price should be <price>
    And http response body path $.status should be PENDING

    Examples:
      | id    | userId | product       | quantity | price  |
      | ord-1 | usr-1  | Laptop        | 1        | 999.99 |
      | ord-2 | usr-1  | Mouse         | 3        | 25.50  |
      | ord-3 | usr-2  | Keyboard      | 2        | 75.00  |
      | ord-4 | usr-2  | Monitor       | 1        | 450.00 |

  # ── Create order validation ─────────────────────────────────────

  Scenario Outline: Creating an order with missing required fields returns 400
    When I set http body to <body>
    And I POST /orders
    Then http response code should be 400

    Examples:
      | body                                                                     |
      | {"userId":"usr-1","product":"Widget","quantity":1,"price":10.0}           |
      | {"id":"v-1","product":"Widget","quantity":1,"price":10.0}                |
      | {"id":"v-2","userId":"usr-1","quantity":1,"price":10.0}                  |
      | {"id":"v-3","userId":"usr-1","product":"Widget","price":10.0}            |
      | {"id":"v-4","userId":"usr-1","product":"Widget","quantity":1}             |

  # ── Duplicate order ID ──────────────────────────────────────────

  Scenario: Creating an order with a duplicate ID returns 409
    When I set http body to {"id":"ord-1","userId":"usr-9","product":"Duplicate","quantity":1,"price":5.0}
    And I POST /orders
    Then http response code should be 409
    And http response body path $.error should be Order with id ord-1 already exists

  # ── Get order by ID ─────────────────────────────────────────────

  Scenario: Get an existing order by ID
    When I GET /orders/ord-1
    Then http response code should be 200
    And http response body path $.id should be ord-1
    And http response body path $.product should be Laptop

  Scenario: Get a non-existent order returns 404
    When I GET /orders/does-not-exist
    Then http response code should be 404

  # ── List and filter orders ──────────────────────────────────────

  Scenario: List all orders
    When I GET /orders
    Then http response code should be 200
    And http response body is typed as array using path $ with length 4

  Scenario: Filter orders by userId
    And I set http query parameter userId to usr-1
    When I GET /orders
    Then http response code should be 200
    And http response body is typed as array using path $ with length 2
    And http response body path $.[0].userId should be usr-1

  Scenario: Filter orders by status
    And I set http query parameter status to PENDING
    When I GET /orders
    Then http response code should be 200
    And http response body is typed as array using path $ with length 4

  # ── Pagination and sorting ──────────────────────────────────────

  Scenario: Paginated order listing
    And I set http query parameter page to 0
    And I set http query parameter size to 2
    When I GET /orders
    Then http response code should be 200
    And http response body is typed as array using path $ with length 2

  Scenario: Sort orders by price descending
    And I set http query parameter sort to price,desc
    When I GET /orders
    Then http response code should be 200
    And http response body path $.[0].product should be Laptop
    And http response body path $.[1].product should be Monitor

  # ── Update order ────────────────────────────────────────────────

  Scenario: Update an existing order
    When I set http body to {"id":"ord-2","userId":"usr-1","product":"Wireless Mouse","quantity":5,"price":30.00,"status":"SHIPPED"}
    And I PUT /orders/ord-2
    Then http response code should be 200
    And http response body path $.product should be Wireless Mouse
    And http response body path $.quantity should be 5
    And http response body path $.status should be SHIPPED

  Scenario: Update a non-existent order returns 404
    When I set http body to {"id":"nope","userId":"usr-1","product":"Ghost","quantity":1,"price":1.0}
    And I PUT /orders/nope
    Then http response code should be 404

  # ── Delete order ────────────────────────────────────────────────

  Scenario: Delete a non-existent order returns 404
    When I DELETE /orders/does-not-exist
    Then http response code should be 404

  Scenario: Delete all test orders
    When I DELETE /orders/ord-1
    Then http response code should be 200
    When I DELETE /orders/ord-2
    Then http response code should be 200
    When I DELETE /orders/ord-3
    Then http response code should be 200
    When I DELETE /orders/ord-4
    Then http response code should be 200
    When I GET /orders
    Then http response code should be 200
    And http response body is typed as array using path $ with length 0
