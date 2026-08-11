@order @cleanup-orders
Feature: Orders api tests
  CRUD operations of the orders api.

  Background:
    Given http baseUri is /api/
    And I set Accept-Language http header to en-US
    And I set http headers to:
      | Accept       | application/json |
      | Content-Type | application/json |

  Scenario Outline: Should create the order <id> for customer <customerId>
    And I set http body to {"id":"<id>","customerId":"<customerId>","product":"<product>","quantity":<quantity>,"unitPrice":<unitPrice>}
    When I POST /orders
    Then http response code should be 201
    And http response header Content-Type should be application/json
    And http response body should be valid json
    And http response body path $.id should be <id>
    And http response body path $.customerId should be <customerId>
    And http response body path $.product should be <product>
    And http response body path $.quantity should be <quantity>
    And http response body path $.total should be <total>
    And http response body path $.status should be PENDING
    When I GET /orders/<id>
    Then http response code should be 200
    And http response body path $.product should be <product>

    Examples:
      | id   | customerId | product   | quantity | unitPrice | total  |
      | 1001 | 1          | Shield    | 1        | 250.0     | 250.0  |
      | 1002 | 1          | Arrow     | 12       | 3.5       | 42.0   |
      | 1003 | 2          | Hammer    | 2        | 199.99    | 399.98 |
      | 1004 | 3          | Batarang  | 10       | 0.0       | 0.0    |

  Scenario: Should create an order with an explicit status
    And I set http body to {"id":"1010","customerId":"7","product":"Cape","quantity":1,"unitPrice":80.0,"status":"PAID"}
    When I POST /orders
    Then http response code should be 201
    And http response body path $.status should be PAID

  Scenario: Should list the orders of a given customer
    And I set http body to {"id":"1020","customerId":"42","product":"Shield","quantity":1,"unitPrice":250.0}
    When I POST /orders
    Then http response code should be 201
    And I set http body to {"id":"1021","customerId":"42","product":"Arrow","quantity":2,"unitPrice":5.0}
    When I POST /orders
    Then http response code should be 201
    And I set http body to {"id":"1022","customerId":"43","product":"Hammer","quantity":1,"unitPrice":100.0}
    When I POST /orders
    Then http response code should be 201
    When I GET /orders?customerId=42&sort=id,asc
    Then http response code should be 200
    And http response body is typed as array using path $ with length 2
    And http response body path $.[0].id should be 1020
    And http response body path $.[1].id should be 1021
    When I GET /orders
    Then http response code should be 200
    And http response body is typed as array using path $ with length 3

  Scenario: Should update an existing order
    And I set http body to {"id":"1030","customerId":"9","product":"Shield","quantity":1,"unitPrice":250.0}
    When I POST /orders
    Then http response code should be 201
    And I store the value of http body path $.id as orderId in scenario scope
    And I set http body to {"id":"1030","customerId":"9","product":"Vibranium Shield","quantity":3,"unitPrice":300.0}
    When I PUT /orders/`$orderId`
    Then http response code should be 200
    And http response body path $.product should be Vibranium Shield
    And http response body path $.quantity should be 3
    And http response body path $.total should be 900.0
    When I GET /orders/1030
    Then http response code should be 200
    And http response body path $.product should be Vibranium Shield

  Scenario: Should delete an existing order
    And I set http body to {"id":"1040","customerId":"9","product":"Shield","quantity":1,"unitPrice":250.0}
    When I POST /orders
    Then http response code should be 201
    When I DELETE /orders/1040
    Then http response code should be 200
    When I GET /orders/1040
    Then http response code should be 404
    When I GET /orders
    Then http response code should be 200
    And http response body is typed as array using path $ with length 0

  Scenario Outline: Should return 404 for the unknown order <id>
    When I <method> /orders/<id>
    Then http response code should be 404

    Examples:
      | method | id     |
      | GET    | 999999 |
      | DELETE | 999999 |

  Scenario: Should return 404 when updating an unknown order
    And I set http body to {"id":"999999","customerId":"9","product":"Shield","quantity":1,"unitPrice":250.0}
    When I PUT /orders/999999
    Then http response code should be 404
