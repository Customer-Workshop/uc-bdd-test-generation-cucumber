@order @edge-case @cleanup-orders
Feature: Orders api - input validation
  An order requires an id, a customerId, a product and a positive quantity.
  Ids are unique and the status must be a known one.

  Background:
    Given http baseUri is /api/
    And I set http headers to:
      | Accept       | application/json |
      | Content-Type | application/json |

  Scenario Outline: Should reject an order creation when <field> is invalid (<description>)
    And I set http body to <payload>
    When I POST /orders
    Then http response code should be 400
    And http response body should be valid json
    And http response body path $.field should be <field>
    And http response body path $.error should exists
    When I GET /orders
    Then http response code should be 200
    And http response body is typed as array using path $ with length 0

    Examples:
      | description         | field      | payload                                                                                  |
      | no id               | id         | {"customerId":"1","product":"Shield","quantity":1,"unitPrice":250.0}                     |
      | blank id            | id         | {"id":"  ","customerId":"1","product":"Shield","quantity":1,"unitPrice":250.0}           |
      | no customerId       | customerId | {"id":"2001","product":"Shield","quantity":1,"unitPrice":250.0}                          |
      | no product          | product    | {"id":"2001","customerId":"1","quantity":1,"unitPrice":250.0}                            |
      | zero quantity       | quantity   | {"id":"2001","customerId":"1","product":"Shield","quantity":0,"unitPrice":250.0}         |
      | negative quantity   | quantity   | {"id":"2001","customerId":"1","product":"Shield","quantity":-3,"unitPrice":250.0}        |
      | quantity above 100  | quantity   | {"id":"2001","customerId":"1","product":"Shield","quantity":101,"unitPrice":250.0}       |
      | negative unitPrice  | unitPrice  | {"id":"2001","customerId":"1","product":"Shield","quantity":1,"unitPrice":-1.0}          |
      | unknown status      | status     | {"id":"2001","customerId":"1","product":"Shield","quantity":1,"unitPrice":250.0,"status":"ARCHIVED"} |
      | empty payload       | id         | {}                                                                                       |

  Scenario Outline: Should reject a duplicate order id (<description>)
    And I set http body to {"id":"2100","customerId":"1","product":"Shield","quantity":1,"unitPrice":250.0}
    When I POST /orders
    Then http response code should be 201
    And I set http body to <payload>
    When I POST /orders
    Then http response code should be 409
    And http response body path $.field should be id
    And http response body should contain already exists
    When I GET /orders
    Then http response code should be 200
    And http response body is typed as array using path $ with length 1
    And http response body path $.[0].product should be Shield

    Examples:
      | description      | payload                                                                          |
      | same payload     | {"id":"2100","customerId":"1","product":"Shield","quantity":1,"unitPrice":250.0} |
      | other customer   | {"id":"2100","customerId":"2","product":"Hammer","quantity":5,"unitPrice":10.0}  |

  Scenario: Should reject an update making the order invalid
    And I set http body to {"id":"2200","customerId":"1","product":"Shield","quantity":1,"unitPrice":250.0}
    When I POST /orders
    Then http response code should be 201
    And I set http body to {"id":"2200","customerId":"1","product":"Shield","quantity":0,"unitPrice":250.0}
    When I PUT /orders/2200
    Then http response code should be 400
    And http response body path $.field should be quantity
    When I GET /orders/2200
    Then http response code should be 200
    And http response body path $.quantity should be 1

  Scenario: Should reject an unknown status filter
    When I GET /orders?status=ARCHIVED
    Then http response code should be 400
    And http response body path $.field should be status
