Feature: Orders API tests

  Background:
    Given http baseUri is /api/
    And I set http headers to:
      | Accept        | application/json  |
      | Content-Type  | application/json  |

  # -----------------------------------------------------------------------
  # Create orders using Scenario Outline with Examples
  # -----------------------------------------------------------------------
  Scenario Outline: Create valid orders
    When I set http body to {"id":"<id>","userId":"<userId>","product":"<product>","quantity":<quantity>,"price":<price>,"status":"<status>"}
    And I POST /orders
    Then http response code should be 201
    And http response body path $.id should be <id>
    And http response body path $.product should be <product>
    And http response body path $.quantity should be <quantity>
    And http response body path $.price should be <price>
    And http response body path $.status should be <status>

    Examples:
      | id    | userId | product       | quantity | price  | status    |
      | ord-1 | usr-1  | Laptop        | 1        | 999.99 | pending   |
      | ord-2 | usr-1  | Mouse         | 3        | 29.99  | confirmed |
      | ord-3 | usr-2  | Keyboard      | 2        | 79.99  | shipped   |
      | ord-4 | usr-2  | Monitor       | 1        | 449.99 | delivered |
      | ord-5 | usr-3  | Headphones    | 5        | 149.99 | pending   |

  # -----------------------------------------------------------------------
  # Retrieve orders
  # -----------------------------------------------------------------------
  Scenario: Get all orders
    When I GET /orders
    Then http response code should be 200
    And http response body is typed as array using path $ with length 5

  Scenario: Get a specific order by id
    When I GET /orders/ord-1
    Then http response code should be 200
    And http response body path $.id should be ord-1
    And http response body path $.product should be Laptop
    And http response body path $.userId should be usr-1

  Scenario: Get a non-existent order returns 404
    When I GET /orders/non-existent
    Then http response code should be 404

  # -----------------------------------------------------------------------
  # Filter orders by userId and status
  # -----------------------------------------------------------------------
  Scenario: Filter orders by userId
    And I set http query parameter userId to usr-1
    When I GET /orders
    Then http response code should be 200
    And http response body is typed as array using path $ with length 2

  Scenario: Filter orders by status
    And I set http query parameter status to pending
    When I GET /orders
    Then http response code should be 200
    And http response body is typed as array using path $ with length 2

  # -----------------------------------------------------------------------
  # Validation - missing/invalid fields using Scenario Outline
  # -----------------------------------------------------------------------
  Scenario Outline: Create order with invalid data returns 400
    When I set http body to <body>
    And I POST /orders
    Then http response code should be 400
    And http response body path $.error should be <expectedError>

    Examples:
      | body                                                                              | expectedError              |
      | {"product":"Widget","quantity":1,"price":10.0,"status":"pending"}                  | id is required             |
      | {"id":"inv-1","quantity":1,"price":10.0,"status":"pending"}                        | product is required        |
      | {"id":"inv-2","product":"Widget","quantity":0,"price":10.0}                        | quantity is required to be positive |
      | {"id":"inv-3","product":"Widget","quantity":1,"price":-5.0}                        | price cannot be negative   |

  Scenario: Create order with invalid status returns 400
    When I set http body to {"id":"inv-4","product":"Widget","quantity":1,"price":10.0,"status":"invalid"}
    And I POST /orders
    Then http response code should be 400
    And http response body should contain invalid status

  # -----------------------------------------------------------------------
  # Duplicate order ID returns 409
  # -----------------------------------------------------------------------
  Scenario: Creating an order with duplicate ID returns 409
    When I set http body to {"id":"ord-1","userId":"usr-9","product":"Duplicate","quantity":1,"price":10.0,"status":"pending"}
    And I POST /orders
    Then http response code should be 409
    And http response body should contain already exists

  # -----------------------------------------------------------------------
  # Update an order
  # -----------------------------------------------------------------------
  Scenario: Update an existing order
    When I set http body to {"product":"Gaming Laptop","quantity":1,"price":1499.99,"status":"confirmed","userId":"usr-1"}
    And I PUT /orders/ord-1
    Then http response code should be 200
    And http response body path $.product should be Gaming Laptop
    And http response body path $.price should be 1499.99
    And http response body path $.status should be confirmed

  Scenario: Update a non-existent order returns 404
    When I set http body to {"product":"Nothing","quantity":1,"price":10.0}
    And I PUT /orders/non-existent
    Then http response code should be 404

  Scenario: Update an order with invalid status returns 400
    When I set http body to {"product":"Test","quantity":1,"price":10.0,"status":"bad-status"}
    And I PUT /orders/ord-2
    Then http response code should be 400
    And http response body should contain invalid status

  # -----------------------------------------------------------------------
  # Pagination and sorting
  # -----------------------------------------------------------------------
  Scenario: Paginate orders - first page of 2
    And I set http query parameter page to 0
    And I set http query parameter size to 2
    When I GET /orders
    Then http response code should be 200
    And http response body is typed as array using path $ with length 2

  Scenario: Paginate orders - beyond range returns empty
    And I set http query parameter page to 100
    And I set http query parameter size to 10
    When I GET /orders
    Then http response code should be 200
    And http response body is typed as array using path $ with length 0

  Scenario: Sort orders by price descending
    And I set http query parameter sort to price,desc
    When I GET /orders
    Then http response code should be 200
    And http response body is typed as array for path $
    And http response body path $.[0].product should be Gaming Laptop

  Scenario: Sort orders by product ascending
    And I set http query parameter sort to product,asc
    When I GET /orders
    Then http response code should be 200
    And http response body is typed as array for path $
    And http response body path $.[0].product should be Gaming Laptop

  # -----------------------------------------------------------------------
  # Delete orders using Scenario Outline
  # -----------------------------------------------------------------------
  Scenario: Delete a non-existent order returns 404
    When I DELETE /orders/non-existent
    Then http response code should be 404

  Scenario Outline: Delete existing orders
    When I DELETE /orders/<id>
    Then http response code should be 200

    Examples:
      | id    |
      | ord-1 |
      | ord-2 |
      | ord-3 |
      | ord-4 |
      | ord-5 |

  Scenario: Verify all orders are deleted
    When I GET /orders
    Then http response code should be 200
    And http response body is typed as array using path $ with length 0
    And http response body path $ should not have content
