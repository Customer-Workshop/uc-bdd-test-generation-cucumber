@orders
Feature: Orders API

  Background:
    Given http baseUri is /api/
    And I set http headers to:
      | Accept       | application/json |
      | Content-Type | application/json |

  Scenario: Create, update, patch and delete an order
    And I set http body to {"id":"o-1","customerId":"c-1","items":["book"],"amount":12.50,"status":"PENDING"}
    When I POST /orders
    Then http response code should be 201
    And I set http body to {"id":"o-1","customerId":"c-1","items":["book","pen"],"amount":15.00,"status":"PAID"}
    When I PUT /orders/o-1
    Then http response code should be 200
    And http response body path $.status should be PAID
    And I set http body to {"status":"SHIPPED"}
    When I PATCH /orders/o-1
    Then http response code should be 200
    And http response body path $.status should be SHIPPED
    When I GET /orders/o-1
    Then http response code should be 200
    And I DELETE /orders/o-1
    Then http response code should be 200
    When I GET /orders/o-1
    Then http response code should be 404

  Scenario Outline: Reject invalid orders
    And I set http body to <body>
    When I POST /orders
    Then http response code should be 400

    Examples:
      | body                                                                 |
      | {"customerId":"c-1","items":["book"],"amount":12.5,"status":"PENDING"} |
      | {"id":"o-2","items":["book"],"amount":12.5,"status":"PENDING"}      |
      | {"id":"o-3","customerId":"c-1","items":[],"amount":12.5,"status":"PENDING"} |
      | {"id":"o-4","customerId":"c-1","items":["book"],"amount":0,"status":"PENDING"} |
      | {"id":"o-5","customerId":"c-1","items":["book"],"amount":12.5}      |

  Scenario: Reject duplicate and unknown orders
    And I set http body to {"id":"o-6","customerId":"c-1","items":["book"],"amount":12.5,"status":"PENDING"}
    When I POST /orders
    Then http response code should be 201
    And I POST /orders
    Then http response code should be 409
    When I GET /orders/unknown
    Then http response code should be 404

  Scenario: Reject an illegal status transition
    And I set http body to {"id":"o-7","customerId":"c-1","items":["book"],"amount":12.5,"status":"PENDING"}
    When I POST /orders
    Then http response code should be 201
    And I set http body to {"status":"DELIVERED"}
    When I PATCH /orders/o-7
    Then http response code should be 200
    And I set http body to {"status":"CANCELLED"}
    When I PATCH /orders/o-7
    Then http response code should be 409

  Scenario: Filter and page orders
    And I set http body to {"id":"o-8","customerId":"c-2","items":["book"],"amount":10,"status":"PAID"}
    When I POST /orders
    And I set http body to {"id":"o-9","customerId":"c-1","items":["pen"],"amount":20,"status":"PENDING"}
    And I POST /orders
    And I set http body to {"id":"o-10","customerId":"c-1","items":["paper"],"amount":30,"status":"PAID"}
    And I POST /orders
    And I set http query parameter customerId to c-1
    And I set http query parameter status to PAID
    And I set http query parameter page to 0
    And I set http query parameter size to 1
    And I set http query parameter sort to amount,desc
    When I GET /orders
    Then http response code should be 200
    And http response body is typed as array using path $ with length 1
    And http response body path $.[0].id should be o-10
    And http response header X-Total-Count should be 1
