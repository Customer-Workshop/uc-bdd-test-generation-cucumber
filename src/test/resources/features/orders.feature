Feature: Orders API tests

  Background:
    Given http baseUri is /api/
    And I set http headers to:
      | Accept        | application/json  |
      | Content-Type  | application/json  |

  # -----------------------------------------------------------------------
  # Create orders — happy path
  # -----------------------------------------------------------------------

  Scenario: Create a new order
    And I set http body to {"id":"ord-1","userId":"user-1","product":"Laptop","quantity":1,"price":999.99,"status":"PENDING","tags":["electronics","sale"]}
    And I POST /orders
    Then http response code should be 201
    And http response body should be valid json
    And http response body path $.id should be ord-1
    And http response body path $.userId should be user-1
    And http response body path $.product should be Laptop
    And http response body path $.quantity should be 1
    And http response body path $.price should be 999.99
    And http response body path $.status should be PENDING
    And http response body path $.tags should be ["electronics","sale"]

  Scenario: Create a second order
    And I set http body to {"id":"ord-2","userId":"user-1","product":"Mouse","quantity":3,"price":29.99,"status":"CONFIRMED"}
    And I POST /orders
    Then http response code should be 201
    And http response body path $.id should be ord-2
    And http response body path $.product should be Mouse
    And http response body path $.status should be CONFIRMED

  Scenario: Create an order for a different user
    And I set http body to {"id":"ord-3","userId":"user-2","product":"Keyboard","quantity":2,"price":79.50,"status":"PENDING"}
    And I POST /orders
    Then http response code should be 201
    And http response body path $.userId should be user-2

  Scenario: Create order with default PENDING status
    And I set http body to {"id":"ord-4","userId":"user-1","product":"Headphones","quantity":1,"price":149.00}
    And I POST /orders
    Then http response code should be 201
    And http response body path $.status should be PENDING

  # -----------------------------------------------------------------------
  # Create orders — validation errors
  # -----------------------------------------------------------------------

  Scenario: Should return 400 when creating order with missing product
    And I set http body to {"id":"ord-bad","quantity":1,"price":10.00}
    And I POST /orders
    Then http response code should be 400
    And http response body should be valid json
    And http response body path $.error should be Bad Request
    And http response body path $.errors.product should be product is required

  Scenario: Should return 400 when creating order with zero quantity
    And I set http body to {"id":"ord-bad2","product":"Widget","quantity":0,"price":10.00}
    And I POST /orders
    Then http response code should be 400
    And http response body path $.errors.quantity should be quantity requires a positive value

  Scenario: Should return 400 when creating order with negative price
    And I set http body to {"id":"ord-bad3","product":"Widget","quantity":1,"price":-5.00}
    And I POST /orders
    Then http response code should be 400
    And http response body path $.errors.price should be price requires a positive value

  Scenario: Should return 400 when creating order with missing required fields
    And I set http body to {"status":"PENDING"}
    And I POST /orders
    Then http response code should be 400
    And http response body path $.errors.id should be id is required
    And http response body path $.errors.product should be product is required

  Scenario: Should return 400 when creating order with invalid status
    And I set http body to {"id":"ord-bad4","product":"Widget","quantity":1,"price":10.00,"status":"INVALID"}
    And I POST /orders
    Then http response code should be 400
    And http response body should be valid json

  # -----------------------------------------------------------------------
  # Duplicate order
  # -----------------------------------------------------------------------

  Scenario: Should return 409 when creating order with duplicate ID
    And I set http body to {"id":"ord-1","product":"Duplicate","quantity":1,"price":1.00}
    And I POST /orders
    Then http response code should be 409
    And http response body path $.error should be Conflict
    And http response body path $.message should be Order with id ord-1 already exists

  # -----------------------------------------------------------------------
  # Read orders
  # -----------------------------------------------------------------------

  Scenario: Get all orders
    When I GET /orders
    Then http response code should be 200
    And http response body should be valid json
    And http response body is typed as array for path $
    And http response body is typed as array using path $ with length 4

  Scenario: Get order by ID
    When I GET /orders/ord-1
    Then http response code should be 200
    And http response body path $.id should be ord-1
    And http response body path $.product should be Laptop

  Scenario: Get non-existent order returns 404
    When I GET /orders/ord-999
    Then http response code should be 404

  # -----------------------------------------------------------------------
  # Filter orders
  # -----------------------------------------------------------------------

  Scenario: Filter orders by userId
    And I set http query parameter userId to user-1
    When I GET /orders
    Then http response code should be 200
    And http response body is typed as array using path $ with length 3

  Scenario: Filter orders by status
    And I set http query parameter status to PENDING
    When I GET /orders
    Then http response code should be 200
    And http response body is typed as array for path $

  # -----------------------------------------------------------------------
  # Pagination and sorting
  # -----------------------------------------------------------------------

  Scenario: Paginate orders
    And I set http query parameter page to 0
    And I set http query parameter size to 2
    When I GET /orders
    Then http response code should be 200
    And http response body path $.page should be 0
    And http response body path $.size should be 2
    And http response body path $.totalElements should be 4
    And http response body path $.totalPages should be 2
    And http response body is typed as array using path $.content with length 2

  Scenario: Sort orders by price descending
    And I set http query parameter sort to -price
    When I GET /orders
    Then http response code should be 200
    And http response body is typed as array for path $
    And http response body path $.[0].product should be Laptop

  # -----------------------------------------------------------------------
  # Update order
  # -----------------------------------------------------------------------

  Scenario: Update an existing order
    And I set http body to {"product":"Gaming Laptop","price":1299.99}
    And I PUT /orders/ord-1
    Then http response code should be 200
    And http response body path $.product should be Gaming Laptop
    And http response body path $.price should be 1299.99
    When I GET /orders/ord-1
    Then http response code should be 200
    And http response body path $.product should be Gaming Laptop

  Scenario: Update non-existent order returns 404
    And I set http body to {"product":"Ghost"}
    And I PUT /orders/ord-999
    Then http response code should be 404

  # -----------------------------------------------------------------------
  # Patch order status
  # -----------------------------------------------------------------------

  Scenario: Update order status via PATCH
    And I set http body to {"status":"SHIPPED"}
    And I PATCH /orders/ord-1/status
    Then http response code should be 200
    And http response body path $.status should be SHIPPED

  Scenario: Should return 400 for invalid status in PATCH
    And I set http body to {"status":"WRONG"}
    And I PATCH /orders/ord-1/status
    Then http response code should be 400
    And http response body path $.error should be Bad Request

  Scenario: Patch non-existent order returns 404
    And I set http body to {"status":"SHIPPED"}
    And I PATCH /orders/ord-999/status
    Then http response code should be 404

  # -----------------------------------------------------------------------
  # Delete orders
  # -----------------------------------------------------------------------

  Scenario: Delete non-existent order returns 404
    When I DELETE /orders/ord-999
    Then http response code should be 404

  Scenario: Delete all orders
    When I DELETE /orders/ord-1
    Then http response code should be 200
    When I DELETE /orders/ord-2
    Then http response code should be 200
    When I DELETE /orders/ord-3
    Then http response code should be 200
    When I DELETE /orders/ord-4
    Then http response code should be 200
    When I GET /orders
    And http response body is typed as array using path $ with length 0
