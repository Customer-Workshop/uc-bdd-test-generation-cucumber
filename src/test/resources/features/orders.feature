@order
Feature: Orders api tests

  Background:
    Given http baseUri is /api/
    And I set http headers to:
      | Accept        | application/json  |
      | Content-Type  | application/json  |

  Scenario: Should create an order and compute its total
    Given I set http body to {"id":"o1","customerName":"Tony Stark","customerEmail":"tstark@marvel.com","items":[{"sku":"ARC-REACTOR","quantity":2,"unitPrice":10.5},{"sku":"REPULSOR","quantity":1,"unitPrice":4.25}]}
    When I POST /orders
    Then http response code should be 201
    And http response header Content-Type should be application/json
    And http response body should be valid json
    And http response body path $.id should be o1
    And http response body path $.status should be PENDING
    And http response body path $.total should be 25.25
    And I store the value of http body path $.id as createdOrder in scenario scope
    When I GET /orders/`$createdOrder`
    Then http response code should be 200
    And http response body path $.customerName should be Tony Stark
    And http response body is typed as array using path $.items with length 2

  Scenario: Should reject an order with a duplicated id
    Given I set http body to {"id":"o2","customerName":"Tony Stark","items":[{"sku":"ARC-REACTOR","quantity":1,"unitPrice":10.5}]}
    When I POST /orders
    Then http response code should be 201
    Given I set http body to {"id":"o2","customerName":"Bruce Wayne","items":[{"sku":"BATARANG","quantity":1,"unitPrice":2}]}
    When I POST /orders
    Then http response code should be 409
    And http response body path $.status should be 409
    And http response body path $.message should be Order already exists with id: o2

  Scenario Outline: Should reject an order creation with an invalid <field>
    Given I set http body to <body>
    When I POST /orders
    Then http response code should be 400
    And http response body path $.status should be 400
    And http response body path $.message should be Validation failed
    And http response body path $.errors.[0].field should be <field>

    Examples: Missing required fields
      | field        | body                                                                                     |
      | customerName | {"id":"o3","items":[{"sku":"ARC-REACTOR","quantity":1,"unitPrice":10.5}]}                |
      | customerName | {"id":"o3","customerName":"  ","items":[{"sku":"ARC","quantity":1,"unitPrice":10.5}]}    |
      | id           | {"customerName":"Tony Stark","items":[{"sku":"ARC","quantity":1,"unitPrice":10.5}]}      |
      | items        | {"id":"o3","customerName":"Tony Stark","items":[]}                                       |

    Examples: Invalid item values
      | field              | body                                                                                             |
      | items[0].quantity  | {"id":"o3","customerName":"Tony Stark","items":[{"sku":"ARC","quantity":0,"unitPrice":10.5}]}    |
      | items[0].quantity  | {"id":"o3","customerName":"Tony Stark","items":[{"sku":"ARC","quantity":1001,"unitPrice":10.5}]} |
      | items[0].sku       | {"id":"o3","customerName":"Tony Stark","items":[{"sku":"","quantity":1,"unitPrice":10.5}]}       |
      | items[0].unitPrice | {"id":"o3","customerName":"Tony Stark","items":[{"sku":"ARC","quantity":1,"unitPrice":0}]}       |
      | items[0].unitPrice | {"id":"o3","customerName":"Tony Stark","items":[{"sku":"ARC","quantity":1}]}                     |

    Examples: Invalid customer email
      | field         | body                                                                                                                  |
      | customerEmail | {"id":"o3","customerName":"Tony","customerEmail":"nope","items":[{"sku":"ARC","quantity":1,"unitPrice":10.5}]}        |

  Scenario Outline: Should accept an order on the item boundaries
    Given I set http body to {"id":"<id>","customerName":"Tony Stark","items":[{"sku":"ARC","quantity":<quantity>,"unitPrice":<price>}]}
    When I POST /orders
    Then http response code should be 201
    And http response body path $.total should be <total>

    Examples:
      | id | quantity | price | total   |
      | b1 | 1        | 0.01  | 0.01    |
      | b2 | 1000     | 0.01  | 10.00   |
      | b3 | 3        | 12.5  | 37.5    |

  Scenario Outline: Should move an order from PENDING to <target>
    Given I set http body to {"id":"t1","customerName":"Tony Stark","items":[{"sku":"ARC","quantity":1,"unitPrice":10.5}]}
    When I POST /orders
    Then http response code should be 201
    Given I set http body to {"status":"<target>"}
    And I PATCH /orders/t1/status
    Then http response code should be 200
    And http response body path $.status should be <target>

    Examples:
      | target    |
      | SHIPPED   |
      | CANCELLED |

  Scenario Outline: Should reject the transition from <from> to <target>
    Given I set http body to {"id":"t2","customerName":"Tony Stark","items":[{"sku":"ARC","quantity":1,"unitPrice":10.5}]}
    When I POST /orders
    Then http response code should be 201
    Given I set http body to {"status":"<from>"}
    And I PATCH /orders/t2/status
    Then http response code should be 200
    Given I set http body to {"status":"<target>"}
    And I PATCH /orders/t2/status
    Then http response code should be 409
    And http response body path $.message should be Cannot move order from <from> to <target>

    Examples:
      | from      | target    |
      | SHIPPED   | CANCELLED |
      | SHIPPED   | PENDING   |
      | CANCELLED | SHIPPED   |
      | CANCELLED | PENDING   |

  Scenario: Should reject an unknown status value
    Given I set http body to {"id":"t3","customerName":"Tony Stark","items":[{"sku":"ARC","quantity":1,"unitPrice":10.5}]}
    When I POST /orders
    Then http response code should be 201
    Given I set http body to {"status":"DELIVERED"}
    And I PATCH /orders/t3/status
    Then http response code should be 400
    And http response body path $.message should be Malformed request body

  Scenario: Should update a pending order only
    Given I set http body to {"id":"u1","customerName":"Tony Stark","items":[{"sku":"ARC","quantity":1,"unitPrice":10.5}]}
    When I POST /orders
    Then http response code should be 201
    Given I set http body to {"id":"u1","customerName":"Anthony Stark","items":[{"sku":"ARC","quantity":2,"unitPrice":10.5}]}
    And I PUT /orders/u1
    Then http response code should be 200
    And http response body path $.customerName should be Anthony Stark
    And http response body path $.total should be 21.0
    Given I set http body to {"status":"SHIPPED"}
    And I PATCH /orders/u1/status
    Then http response code should be 200
    Given I set http body to {"id":"u1","customerName":"Tony Stark","items":[{"sku":"ARC","quantity":1,"unitPrice":10.5}]}
    And I PUT /orders/u1
    Then http response code should be 409
    And http response body path $.message should be Only a PENDING order can be updated, current status: SHIPPED

  Scenario Outline: Should return 404 for an unknown order on <method>
    Given I set http body to <body>
    When I <method> <path>
    Then http response code should be 404
    And http response body path $.status should be 404
    And http response body path $.message should be No order found with id: nope

    Examples:
      | method | path               | body                                                                                              |
      | GET    | /orders/nope       | {"id":"nope","customerName":"Tony Stark","items":[{"sku":"ARC","quantity":1,"unitPrice":10.5}]}   |
      | PUT    | /orders/nope       | {"id":"nope","customerName":"Tony Stark","items":[{"sku":"ARC","quantity":1,"unitPrice":10.5}]}   |
      | DELETE | /orders/nope       | {"id":"nope","customerName":"Tony Stark","items":[{"sku":"ARC","quantity":1,"unitPrice":10.5}]}   |
      | PATCH  | /orders/nope/status | {"status":"SHIPPED"}                                                                             |

  Scenario: Should delete an order
    Given I set http body to {"id":"d1","customerName":"Tony Stark","items":[{"sku":"ARC","quantity":1,"unitPrice":10.5}]}
    When I POST /orders
    Then http response code should be 201
    When I DELETE /orders/d1
    Then http response code should be 204
    And http response body path $ should not have content
    When I GET /orders/d1
    Then http response code should be 404

  Scenario: Should return an empty list when no order exists
    When I GET /orders
    Then http response code should be 200
    And http response header X-Total-Count should be 0
    And http response body is typed as array using path $ with length 0
    And http response body path $ should not have content
