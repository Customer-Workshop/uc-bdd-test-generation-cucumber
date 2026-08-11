@order @orderCleanup
Feature: Orders api validation and error cases

  Background:
    Given http baseUri is /api/
    And I set http headers to:
      | Accept        | application/json |
      | Content-Type  | application/json |

  Scenario Outline: Should reject an order creation because of <field>
    Given I set http body to <payload>
    When I POST /orders
    Then http response code should be 400
    And http response body should be valid json
    And http response body path $.field should be <field>
    And http response body path $.message should be <message>
    When I GET /orders
    Then http response body is typed as array using path $ with length 0

    Examples:
      | field            | payload                                                                                                        | message                                        |
      | id               | {"customerId":"CUST-1","currency":"EUR","items":[{"sku":"SKU-1","quantity":1,"unitPrice":10}]}                 | id is required                                 |
      | customerId       | {"id":"ORD-1","currency":"EUR","items":[{"sku":"SKU-1","quantity":1,"unitPrice":10}]}                          | customerId is required                         |
      | currency         | {"id":"ORD-1","customerId":"CUST-1","items":[{"sku":"SKU-1","quantity":1,"unitPrice":10}]}                     | currency is required                           |
      | currency         | {"id":"ORD-1","customerId":"CUST-1","currency":"EURO","items":[{"sku":"SKU-1","quantity":1,"unitPrice":10}]}   | currency is not a 3 letters ISO code           |
      | items            | {"id":"ORD-1","customerId":"CUST-1","currency":"EUR"}                                                          | at least one item is required                  |
      | items            | {"id":"ORD-1","customerId":"CUST-1","currency":"EUR","items":[]}                                               | at least one item is required                  |
      | items.sku        | {"id":"ORD-1","customerId":"CUST-1","currency":"EUR","items":[{"quantity":1,"unitPrice":10}]}                  | sku is required                                |
      | items.quantity   | {"id":"ORD-1","customerId":"CUST-1","currency":"EUR","items":[{"sku":"SKU-1","quantity":0,"unitPrice":10}]}    | quantity cannot be lower than 1                |
      | items.quantity   | {"id":"ORD-1","customerId":"CUST-1","currency":"EUR","items":[{"sku":"SKU-1","unitPrice":10}]}                 | quantity cannot be lower than 1                |
      | items.unitPrice  | {"id":"ORD-1","customerId":"CUST-1","currency":"EUR","items":[{"sku":"SKU-1","quantity":2,"unitPrice":-1}]}    | unitPrice cannot be negative                   |
      | items.unitPrice  | {"id":"ORD-1","customerId":"CUST-1","currency":"EUR","items":[{"sku":"SKU-1","quantity":2}]}                   | unitPrice cannot be negative                   |

  Scenario Outline: Should reject the duplicate order id <id>
    Given I set http body to {"id":"<id>","customerId":"CUST-1","currency":"EUR","items":[{"sku":"SKU-1","quantity":1,"unitPrice":10}]}
    When I POST /orders
    Then http response code should be 201
    Given I set http body to {"id":"<id>","customerId":"CUST-2","currency":"USD","items":[{"sku":"SKU-2","quantity":5,"unitPrice":1}]}
    When I POST /orders
    Then http response code should be 409
    And http response body path $.field should be id
    And http response body path $.message should be an order already exists with id <id>
    When I GET /orders
    Then http response body is typed as array using path $ with length 1
    And http response body path $.[0].customerId should be CUST-1

    Examples:
      | id      |
      | ORD-100 |
      | ORD-101 |

  Scenario Outline: Should reject the transition from <from> to <to>
    Given I set http body to {"id":"ORD-200","customerId":"CUST-1","currency":"EUR","status":"<from>","items":[{"sku":"SKU-1","quantity":1,"unitPrice":10}]}
    And I POST /orders
    And http response body path $.status should be <from>
    And I set http body to {"status":"<to>"}
    When I PATCH /orders/ORD-200/status
    Then http response code should be 409
    And http response body path $.field should be status
    And http response body path $.message should be <from> cannot be changed to <to>
    When I GET /orders/ORD-200
    Then http response body path $.status should be <from>

    Examples:
      | from      | to        |
      | CREATED   | SHIPPED   |
      | CREATED   | DELIVERED |
      | PAID      | DELIVERED |
      | SHIPPED   | CANCELLED |
      | DELIVERED | PAID      |
      | CANCELLED | PAID      |
      | CANCELLED | SHIPPED   |

  Scenario Outline: Should reject the unknown status <status>
    Given I set http body to {"id":"ORD-300","customerId":"CUST-1","currency":"EUR","items":[{"sku":"SKU-1","quantity":1,"unitPrice":10}]}
    And I POST /orders
    And I set http body to {"status":"<status>"}
    When I PATCH /orders/ORD-300/status
    Then http response code should be 400
    And http response body path $.field should be status
    And http response body path $.message should be unknown status, expected one of [CREATED, PAID, SHIPPED, DELIVERED, CANCELLED]

    Examples:
      | status    |
      | REFUNDED  |
      | PENDING   |
      | UNKNOWN   |

  Scenario: Should not change the status of an unknown order
    Given I set http body to {"status":"PAID"}
    When I PATCH /orders/ORD-UNKNOWN/status
    Then http response code should be 404

  Scenario: Should not update an order which is not CREATED anymore
    Given I set http body to {"id":"ORD-400","customerId":"CUST-1","currency":"EUR","status":"SHIPPED","items":[{"sku":"SKU-1","quantity":1,"unitPrice":10}]}
    And I POST /orders
    Then http response code should be 201
    Given I set http body to {"id":"ORD-400","customerId":"CUST-2","currency":"EUR","items":[{"sku":"SKU-1","quantity":2,"unitPrice":10}]}
    When I PUT /orders/ORD-400
    Then http response code should be 409
    And http response body path $.field should be status
    And http response body path $.message should be only a CREATED order can be updated
