@order @edge-case @cleanup-orders
Feature: Orders api - pagination, sorting and filtering
  GET /orders accepts customerId, status, page, size and sort query parameters.

  Background:
    Given http baseUri is /api/
    And I set http headers to:
      | Accept       | application/json |
      | Content-Type | application/json |
    And I set http body to {"id":"4001","customerId":"1","product":"Arrow","quantity":10,"unitPrice":2.0}
    When I POST /orders
    Then http response code should be 201
    And I set http body to {"id":"4002","customerId":"1","product":"Batarang","quantity":4,"unitPrice":15.0}
    When I POST /orders
    Then http response code should be 201
    And I set http body to {"id":"4003","customerId":"2","product":"Cape","quantity":1,"unitPrice":80.0}
    When I POST /orders
    Then http response code should be 201
    And I set http body to {"id":"4004","customerId":"2","product":"Dagger","quantity":3,"unitPrice":30.0}
    When I POST /orders
    Then http response code should be 201
    And I set http body to {"id":"4005","customerId":"3","product":"Shield","quantity":1,"unitPrice":250.0,"status":"PAID"}
    When I POST /orders
    Then http response code should be 201

  Scenario Outline: Should return page <page> of size <size> sorted by <sort>
    When I GET /orders?page=<page>&size=<size>&sort=<sort>
    Then http response code should be 200
    And http response header X-Total-Count should be 5
    And http response header X-Total-Pages should be <totalPages>
    And http response header X-Page should be <page>
    And http response header X-Page-Size should be <size>
    And http response body is typed as array using path $ with length <length>
    And http response body path $.[0].id should be <firstId>

    Examples:
      | page | size | sort         | totalPages | length | firstId |
      | 0    | 2    | id,asc       | 3          | 2      | 4001    |
      | 1    | 2    | id,asc       | 3          | 2      | 4003    |
      | 2    | 2    | id,asc       | 3          | 1      | 4005    |
      | 0    | 2    | id,desc      | 3          | 2      | 4005    |
      | 0    | 3    | total,asc    | 2          | 3      | 4001    |
      | 0    | 3    | total,desc   | 2          | 3      | 4005    |
      | 0    | 5    | product,asc  | 1          | 5      | 4001    |
      | 0    | 5    | quantity,desc| 1          | 5      | 4001    |

  Scenario Outline: Should filter the orders by <filter>
    When I GET /orders?<filter>&sort=id,asc
    Then http response code should be 200
    And http response body is typed as array using path $ with length <length>
    And http response body path $.[0].id should be <firstId>

    Examples:
      | filter          | length | firstId |
      | customerId=1    | 2      | 4001    |
      | customerId=2    | 2      | 4003    |
      | status=PENDING  | 4      | 4001    |
      | status=PAID     | 1      | 4005    |

  Scenario: Should combine filtering and pagination
    When I GET /orders?status=PENDING&page=1&size=3&sort=id,asc
    Then http response code should be 200
    And http response header X-Total-Count should be 4
    And http response header X-Total-Pages should be 2
    And http response body is typed as array using path $ with length 1
    And http response body path $.[0].id should be 4004

  Scenario: Should return an empty page for an unknown customer
    When I GET /orders?customerId=999&page=0&size=2
    Then http response code should be 200
    And http response header X-Total-Count should be 0
    And http response body is typed as array using path $ with length 0

  Scenario Outline: Should reject invalid pagination parameters (<description>)
    When I GET /orders?<query>
    Then http response code should be 400
    And http response body path $.field should be <field>
    And http response body path $.error should exists

    Examples:
      | description            | query                        | field |
      | negative page          | page=-2&size=2               | page  |
      | zero size              | page=0&size=0                | size  |
      | unknown sort field     | page=0&size=2&sort=unknown   | sort  |
      | unknown sort direction | page=0&size=2&sort=id,sideways | sort |
