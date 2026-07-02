@orders
Feature: Orders API tests

  Background:
    Given http baseUri is /api/
    And I set http headers to:
      | Accept        | application/json  |
      | Content-Type  | application/json  |

  # --- Create orders ---

  @orders
  Scenario Outline: Create valid orders with different products
    When I set http body to {"id":"<id>","userId":"<userId>","product":"<product>","quantity":<quantity>,"price":<price>,"status":"<status>","items":["<item1>","<item2>"]}
    And I POST /orders
    Then http response code should be 201
    And http response body should be valid json
    And http response body path $.id should be <id>
    And http response body path $.userId should be <userId>
    And http response body path $.product should be <product>
    And http response body path $.quantity should be <quantity>
    And http response body path $.status should be <status>

    Examples:
      | id  | userId | product       | quantity | price  | status    | item1        | item2          |
      | 1   | u100   | Laptop        | 1        | 999.99 | PENDING   | MacBook Pro  | Charger        |
      | 2   | u100   | Phone         | 2        | 499.50 | CONFIRMED | iPhone       | Case           |
      | 3   | u200   | Tablet        | 3        | 329.00 | SHIPPED   | iPad         | Apple Pencil   |

  @orders
  Scenario: Create order with default PENDING status
    When I set http body to {"id":"10","userId":"u300","product":"Monitor","quantity":1,"price":299.99}
    And I POST /orders
    Then http response code should be 201
    And http response body path $.status should be PENDING

  # --- Validation errors on create ---

  @orders
  Scenario Outline: Creating an order with missing required fields should return 400
    When I set http body to <body>
    And I POST /orders
    Then http response code should be 400
    And http response body should be valid json
    And http response body path $.errors should exists

    Examples:
      | body                                                                          |
      | {"userId":"u1","product":"Laptop","quantity":1,"price":100}                    |
      | {"id":"20","product":"Laptop","quantity":1,"price":100}                        |
      | {"id":"21","userId":"u1","quantity":1,"price":100}                             |
      | {"id":"22","userId":"u1","product":"Laptop","quantity":0,"price":100}          |
      | {"id":"23","userId":"u1","product":"Laptop","quantity":-1,"price":100}         |

  @orders
  Scenario: Creating an order with negative price should return 400
    When I set http body to {"id":"30","userId":"u1","product":"BadPrice","quantity":1,"price":-50.0}
    And I POST /orders
    Then http response code should be 400
    And http response body path $.errors should exists

  @orders
  Scenario: Creating an order with invalid status should return 400
    When I set http body to {"id":"31","userId":"u1","product":"Phone","quantity":1,"price":100,"status":"INVALID_STATUS"}
    And I POST /orders
    Then http response code should be 400

  # --- Duplicate ID ---

  @orders
  Scenario: Creating an order with duplicate ID should return 409
    When I set http body to {"id":"40","userId":"u1","product":"First Order","quantity":1,"price":100}
    And I POST /orders
    Then http response code should be 201
    When I set http body to {"id":"40","userId":"u2","product":"Duplicate Order","quantity":2,"price":200}
    And I POST /orders
    Then http response code should be 409
    And http response body path $.error should exists

  # --- Get order by ID ---

  @orders
  Scenario: Get an existing order by ID
    When I set http body to {"id":"50","userId":"u100","product":"Keyboard","quantity":1,"price":79.99,"status":"PENDING"}
    And I POST /orders
    Then http response code should be 201
    When I GET /orders/50
    Then http response code should be 200
    And http response body should be valid json
    And http response body path $.id should be 50
    And http response body path $.product should be Keyboard
    And http response body path $.price should be 79.99

  @orders
  Scenario: Get non-existent order returns 404
    When I GET /orders/99999
    Then http response code should be 404

  # --- Update order ---

  @orders
  Scenario Outline: Update order details
    When I set http body to {"id":"60","userId":"u100","product":"OriginalProduct","quantity":1,"price":100.00,"status":"PENDING"}
    And I POST /orders
    Then http response code should be 201
    When I set http body to {"product":"<newProduct>","quantity":<newQuantity>,"price":<newPrice>,"status":"<newStatus>"}
    And I PUT /orders/60
    Then http response code should be 200
    And http response body path $.product should be <newProduct>
    And http response body path $.quantity should be <newQuantity>
    And http response body path $.status should be <newStatus>

    Examples:
      | newProduct     | newQuantity | newPrice | newStatus  |
      | UpdatedProduct | 5           | 250.00   | CONFIRMED  |

  @orders
  Scenario: Update non-existent order returns 404
    When I set http body to {"product":"Ghost","quantity":1,"price":50}
    And I PUT /orders/99999
    Then http response code should be 404

  @orders
  Scenario: Update order with invalid status returns 400
    When I set http body to {"id":"61","userId":"u100","product":"TestProduct","quantity":1,"price":100.00,"status":"PENDING"}
    And I POST /orders
    Then http response code should be 201
    When I set http body to {"product":"TestProduct","quantity":1,"price":100.00,"status":"BOGUS"}
    And I PUT /orders/61
    Then http response code should be 400

  # --- Update order status via PATCH ---

  @orders
  Scenario Outline: Update order status through lifecycle
    When I set http body to {"id":"70","userId":"u100","product":"Lifecycle Item","quantity":1,"price":50.00,"status":"PENDING"}
    And I POST /orders
    Then http response code should be 201
    When I set http body to {"status":"<newStatus>"}
    And I PATCH /orders/70/status
    Then http response code should be 200
    And http response body path $.status should be <newStatus>

    Examples:
      | newStatus  |
      | CONFIRMED  |
      | SHIPPED    |
      | DELIVERED  |

  @orders
  Scenario: Patch status of non-existent order returns 404
    When I set http body to {"status":"CONFIRMED"}
    And I PATCH /orders/99999/status
    Then http response code should be 404

  @orders
  Scenario: Patch with invalid status returns 400
    When I set http body to {"id":"71","userId":"u100","product":"Status Test","quantity":1,"price":50.00}
    And I POST /orders
    Then http response code should be 201
    When I set http body to {"status":"NOT_A_STATUS"}
    And I PATCH /orders/71/status
    Then http response code should be 400

  # --- Delete order ---

  @orders
  Scenario: Delete an existing order
    When I set http body to {"id":"80","userId":"u100","product":"ToDelete","quantity":1,"price":10.00}
    And I POST /orders
    Then http response code should be 201
    When I DELETE /orders/80
    Then http response code should be 200
    When I GET /orders/80
    Then http response code should be 404

  @orders
  Scenario: Delete non-existent order returns 404
    When I DELETE /orders/99999
    Then http response code should be 404

  # --- Filter by userId and status ---

  @orders
  Scenario: Filter orders by userId
    When I set http body to {"id":"90","userId":"filterUser1","product":"ProductA","quantity":1,"price":10.00}
    And I POST /orders
    Then http response code should be 201
    When I set http body to {"id":"91","userId":"filterUser2","product":"ProductB","quantity":1,"price":20.00}
    And I POST /orders
    Then http response code should be 201
    And I set http query parameter userId to filterUser1
    When I GET /orders
    Then http response code should be 200
    And http response body is typed as array using path $ with length 1
    And http response body path $.[0].userId should be filterUser1

  @orders
  Scenario: Filter orders by status
    When I set http body to {"id":"92","userId":"u1","product":"Pending Item","quantity":1,"price":10.00,"status":"PENDING"}
    And I POST /orders
    Then http response code should be 201
    When I set http body to {"id":"93","userId":"u1","product":"Shipped Item","quantity":1,"price":20.00,"status":"SHIPPED"}
    And I POST /orders
    Then http response code should be 201
    And I set http query parameter status to SHIPPED
    When I GET /orders
    Then http response code should be 200
    And http response body is typed as array using path $ with length 1
    And http response body path $.[0].product should be Shipped Item

  # --- Sorting ---

  @orders
  Scenario Outline: Sort orders by different fields
    When I set http body to {"id":"S1","userId":"u1","product":"Banana","quantity":3,"price":5.00,"status":"PENDING"}
    And I POST /orders
    Then http response code should be 201
    When I set http body to {"id":"S2","userId":"u1","product":"Apple","quantity":1,"price":15.00,"status":"CONFIRMED"}
    And I POST /orders
    Then http response code should be 201
    When I set http body to {"id":"S3","userId":"u1","product":"Cherry","quantity":2,"price":10.00,"status":"SHIPPED"}
    And I POST /orders
    Then http response code should be 201
    And I set http query parameter sort to <sortField>,<sortDirection>
    When I GET /orders
    Then http response code should be 200
    And http response body path $.[0].product should be <firstProduct>

    Examples:
      | sortField | sortDirection | firstProduct |
      | product   | asc           | Apple        |
      | price     | desc          | Apple        |
      | quantity  | asc           | Apple        |

  # --- Pagination ---

  @orders
  Scenario: Paginate orders list
    When I set http body to {"id":"P1","userId":"u1","product":"Item1","quantity":1,"price":10.00}
    And I POST /orders
    Then http response code should be 201
    When I set http body to {"id":"P2","userId":"u1","product":"Item2","quantity":1,"price":20.00}
    And I POST /orders
    Then http response code should be 201
    When I set http body to {"id":"P3","userId":"u1","product":"Item3","quantity":1,"price":30.00}
    And I POST /orders
    Then http response code should be 201
    When I set http query parameter page to 0
    And I set http query parameter size to 2
    And I GET /orders
    Then http response code should be 200
    And http response body path $.page should be 0
    And http response body path $.size should be 2
    And http response body path $.totalElements should be 3
    And http response body path $.totalPages should be 2
    And http response body is typed as array using path $.content with length 2
    When I set http query parameter page to 1
    And I set http query parameter size to 2
    And I GET /orders
    Then http response code should be 200
    And http response body path $.page should be 1
    And http response body is typed as array using path $.content with length 1
