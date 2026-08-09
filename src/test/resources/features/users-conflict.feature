@users-conflict
Feature: User conflicts

  Background:
    Given http baseUri is /api/
    And I set http headers to:
      | Accept       | application/json |
      | Content-Type | application/json |

  Scenario: Reject a duplicate user id
    And I set http body to {"id":"duplicate","firstName":"Ada","lastName":"Lovelace"}
    When I POST /users
    Then http response code should be 201
    And I POST /users
    Then http response code should be 409
