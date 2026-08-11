@order @orderCleanup
Feature: Orders api search, pagination and sorting

  Background:
    Given http baseUri is /api/
    And I set http headers to:
      | Accept        | application/json |
      | Content-Type  | application/json |
    And I set http body to {"id":"ORD-1","customerId":"CUST-1","currency":"EUR","status":"CREATED","items":[{"sku":"SKU-1","quantity":1,"unitPrice":30}]}
    And I POST /orders
    And I set http body to {"id":"ORD-2","customerId":"CUST-2","currency":"EUR","status":"PAID","items":[{"sku":"SKU-2","quantity":1,"unitPrice":10}]}
    And I POST /orders
    And I set http body to {"id":"ORD-3","customerId":"CUST-1","currency":"EUR","status":"PAID","items":[{"sku":"SKU-3","quantity":2,"unitPrice":10}]}
    And I POST /orders
    And I set http body to {"id":"ORD-4","customerId":"CUST-3","currency":"EUR","status":"SHIPPED","items":[{"sku":"SKU-4","quantity":5,"unitPrice":10}]}
    And I POST /orders

  Scenario: Should return every order
    When I GET /orders
    Then http response code should be 200
    And http response body is typed as array using path $ with length 4

  Scenario Outline: Should filter orders having the status <status>
    Given I set http query parameter status to <status>
    When I GET /orders
    Then http response code should be 200
    And http response body is typed as array using path $ with length <length>

    Examples:
      | status    | length |
      | CREATED   | 1      |
      | PAID      | 2      |
      | SHIPPED   | 1      |
      | DELIVERED | 0      |
      | CANCELLED | 0      |

  Scenario Outline: Should filter orders of the customer <customerId>
    Given I set http query parameter customerId to <customerId>
    When I GET /orders
    Then http response code should be 200
    And http response body is typed as array using path $ with length <length>

    Examples:
      | customerId | length |
      | CUST-1     | 2      |
      | CUST-2     | 1      |
      | CUST-3     | 1      |
      | CUST-404   | 0      |

  Scenario: Should combine a customer and a status filter
    Given I set http query parameter customerId to CUST-1
    And I set http query parameter status to PAID
    When I GET /orders
    Then http response code should be 200
    And http response body is typed as array using path $ with length 1
    And http response body path $.[0].id should be ORD-3

  Scenario Outline: Should sort orders by <sort>
    Given I set http query parameter sort to <sort>
    When I GET /orders
    Then http response code should be 200
    And http response body is typed as array using path $ with length 4
    And http response body path $.[0].id should be <firstId>
    And http response body path $.[3].id should be <lastId>

    Examples:
      | sort            | firstId | lastId |
      | id,asc          | ORD-1   | ORD-4  |
      | id,desc         | ORD-4   | ORD-1  |
      | total,asc       | ORD-2   | ORD-4  |
      | total,desc      | ORD-4   | ORD-2  |
      | status,asc      | ORD-1   | ORD-4  |
      | customerId,desc | ORD-4   | ORD-3  |

  Scenario Outline: Should return the page <page> of size <size>
    Given I set http query parameter sort to id,asc
    And I set http query parameter page to <page>
    And I set http query parameter size to <size>
    When I GET /orders
    Then http response code should be 200
    And http response body is typed as array using path $ with length <length>

    Examples:
      | page | size | length |
      | 0    | 2    | 2      |
      | 1    | 2    | 2      |
      | 2    | 2    | 0      |
      | 0    | 3    | 3      |

  Scenario Outline: Should reject the invalid search parameter <param>=<value>
    Given I set http query parameter <param> to <value>
    When I GET /orders
    Then http response code should be 400
    And http response body path $.field should be <field>

    Examples:
      | param  | value        | field  |
      | status | REFUNDED     | status |
      | sort   | unknownField | sort   |
      | page   | -1           | page   |
      | size   | 0            | size   |
