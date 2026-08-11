@order @edge-case @cleanup-orders
Feature: Orders api - status transitions
  An order lifecycle is PENDING -> PAID -> SHIPPED -> DELIVERED, and can be CANCELLED while it is not shipped yet.
  Any other transition is a conflict.

  Background:
    Given http baseUri is /api/
    And I set http headers to:
      | Accept       | application/json |
      | Content-Type | application/json |
    And I set http body to {"id":"3000","customerId":"1","product":"Shield","quantity":1,"unitPrice":250.0}
    When I POST /orders
    Then http response code should be 201
    And http response body path $.status should be PENDING

  Scenario Outline: Should move a pending order to <to>
    And I set http body to {"status":"<to>"}
    When I PATCH /orders/3000/status
    Then http response code should be 200
    And http response body path $.status should be <to>
    When I GET /orders/3000
    Then http response code should be 200
    And http response body path $.status should be <to>

    Examples:
      | to        |
      | PAID      |
      | CANCELLED |

  Scenario Outline: Should move a paid order to <to>
    And I set http body to {"status":"PAID"}
    When I PATCH /orders/3000/status
    Then http response code should be 200
    And I set http body to {"status":"<to>"}
    When I PATCH /orders/3000/status
    Then http response code should be 200
    And http response body path $.status should be <to>

    Examples:
      | to        |
      | SHIPPED   |
      | CANCELLED |

  Scenario: Should walk through the whole order lifecycle
    And I set http body to {"status":"PAID"}
    When I PATCH /orders/3000/status
    Then http response code should be 200
    And I set http body to {"status":"SHIPPED"}
    When I PATCH /orders/3000/status
    Then http response code should be 200
    And I set http body to {"status":"DELIVERED"}
    When I PATCH /orders/3000/status
    Then http response code should be 200
    And http response body path $.status should be DELIVERED

  Scenario Outline: Should reject the transition from PENDING to <to>
    And I set http body to {"status":"<to>"}
    When I PATCH /orders/3000/status
    Then http response code should be 409
    And http response body path $.field should be status
    And http response body should contain cannot move order from PENDING
    When I GET /orders/3000
    Then http response code should be 200
    And http response body path $.status should be PENDING

    Examples:
      | to        |
      | PENDING   |
      | SHIPPED   |
      | DELIVERED |

  Scenario Outline: Should reject the unknown status <status>
    And I set http body to {"status":"<status>"}
    When I PATCH /orders/3000/status
    Then http response code should be 400
    And http response body path $.field should be status
    And http response body should contain unknown status

    Examples:
      | status   |
      | ARCHIVED |
      | paid!    |
      | 42       |

  Scenario: Should return 404 when patching the status of an unknown order
    And I set http body to {"status":"PAID"}
    When I PATCH /orders/999999/status
    Then http response code should be 404

  Scenario: Should refuse to delete a shipped order
    And I set http body to {"status":"PAID"}
    When I PATCH /orders/3000/status
    Then http response code should be 200
    And I set http body to {"status":"SHIPPED"}
    When I PATCH /orders/3000/status
    Then http response code should be 200
    When I DELETE /orders/3000
    Then http response code should be 409
    And http response body path $.field should be status
    And http response body should contain cannot be deleted
    When I GET /orders/3000
    Then http response code should be 200
    And http response body path $.status should be SHIPPED

  Scenario: Should delete a cancelled order
    And I set http body to {"status":"CANCELLED"}
    When I PATCH /orders/3000/status
    Then http response code should be 200
    When I DELETE /orders/3000
    Then http response code should be 200
    When I GET /orders/3000
    Then http response code should be 404
