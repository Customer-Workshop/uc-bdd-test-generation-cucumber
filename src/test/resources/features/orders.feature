@order @orderCleanup
Feature: Orders api tests

  Background:
    Given http baseUri is /api/
    And I set http headers to:
      | Accept        | application/json |
      | Content-Type  | application/json |

  Scenario Outline: Should create the order <id> and compute its total
    Given I set http body to {"id":"<id>","customerId":"<customerId>","currency":"<currency>","items":[{"sku":"<sku>","quantity":<quantity>,"unitPrice":<unitPrice>}]}
    When I POST /orders
    Then http response code should be 201
    And http response header Content-Type should be application/json
    And http response body should be valid json
    And http response body path $.id should be <id>
    And http response body path $.customerId should be <customerId>
    And http response body path $.currency should be <currency>
    And http response body path $.status should be CREATED
    And http response body path $.total should be <total>
    And http response body path $.items.[0].sku should be <sku>
    And I store the value of http body path $.id as createdOrder in scenario scope
    And http value of scenario variable createdOrder should be <id>

    Examples:
      | id      | customerId | currency | sku      | quantity | unitPrice | total |
      | ORD-1   | CUST-1     | EUR      | SKU-CAPE | 2        | 10.50     | 21.00 |
      | ORD-2   | CUST-2     | USD      | SKU-MASK | 1        | 99.99     | 99.99 |
      | ORD-3   | CUST-1     | GBP      | SKU-BOOT | 3        | 0         | 0     |

  Scenario: Should create an order with several items
    Given I set http body to {"id":"ORD-10","customerId":"CUST-1","currency":"EUR","items":[{"sku":"SKU-CAPE","quantity":2,"unitPrice":10.50},{"sku":"SKU-MASK","quantity":1,"unitPrice":5.25}]}
    When I POST /orders
    Then http response code should be 201
    And http response body path $.total should be 26.25
    When I GET /orders/ORD-10
    Then http response code should be 200
    And http response body path $.id should be ORD-10
    And http response body path $.items.[1].sku should be SKU-MASK

  Scenario: Should not find an unknown order
    When I GET /orders/ORD-UNKNOWN
    Then http response code should be 404
    And http response body path $ should not have content

  Scenario Outline: Should move an order from <from> to <to>
    Given I set http body to {"id":"ORD-20","customerId":"CUST-1","currency":"EUR","status":"<from>","items":[{"sku":"SKU-CAPE","quantity":1,"unitPrice":10}]}
    And I POST /orders
    And http response body path $.status should be <from>
    And I set http body to {"status":"<to>"}
    When I PATCH /orders/ORD-20/status
    Then http response code should be 200
    And http response body path $.status should be <to>
    When I GET /orders/ORD-20
    Then http response body path $.status should be <to>

    Examples:
      | from    | to        |
      | CREATED | PAID      |
      | CREATED | CANCELLED |
      | PAID    | SHIPPED   |
      | PAID    | CANCELLED |
      | SHIPPED | DELIVERED |

  Scenario: Should follow the whole order lifecycle
    Given I set http body to {"id":"ORD-30","customerId":"CUST-1","currency":"EUR","items":[{"sku":"SKU-CAPE","quantity":1,"unitPrice":10}]}
    And I POST /orders
    Then http response code should be 201
    And http response body path $.status should be CREATED
    Given I set http body to {"status":"PAID"}
    When I PATCH /orders/ORD-30/status
    Then http response body path $.status should be PAID
    Given I set http body to {"status":"SHIPPED"}
    When I PATCH /orders/ORD-30/status
    Then http response body path $.status should be SHIPPED
    Given I set http body to {"status":"DELIVERED"}
    When I PATCH /orders/ORD-30/status
    Then http response code should be 200
    And http response body path $.status should be DELIVERED

  Scenario: Should update a created order
    Given I set http body to {"id":"ORD-40","customerId":"CUST-1","currency":"EUR","items":[{"sku":"SKU-CAPE","quantity":1,"unitPrice":10}]}
    And I POST /orders
    Then http response code should be 201
    Given I set http body to {"id":"ORD-40","customerId":"CUST-9","currency":"USD","items":[{"sku":"SKU-MASK","quantity":4,"unitPrice":2.50}]}
    When I PUT /orders/ORD-40
    Then http response code should be 200
    And http response body path $.customerId should be CUST-9
    And http response body path $.currency should be USD
    And http response body path $.total should be 10.00
    And http response body path $.status should be CREATED

  Scenario: Should not update an unknown order
    Given I set http body to {"id":"ORD-404","customerId":"CUST-1","currency":"EUR","items":[{"sku":"SKU-CAPE","quantity":1,"unitPrice":10}]}
    When I PUT /orders/ORD-404
    Then http response code should be 404

  Scenario: Should delete an order
    Given I set http body to {"id":"ORD-50","customerId":"CUST-1","currency":"EUR","items":[{"sku":"SKU-CAPE","quantity":1,"unitPrice":10}]}
    And I POST /orders
    Then http response code should be 201
    When I DELETE /orders/ORD-50
    Then http response code should be 200
    When I GET /orders/ORD-50
    Then http response code should be 404
    When I GET /orders
    Then http response body is typed as array using path $ with length 0

  Scenario: Should not delete an unknown order
    When I DELETE /orders/ORD-UNKNOWN
    Then http response code should be 404
