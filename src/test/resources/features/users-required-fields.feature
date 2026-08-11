@user @edge-case @cleanup-users
Feature: Users api - missing required fields
  Creating a user requires an id, a firstName and a lastName.
  Any missing or blank required field must be rejected with a 400 and the faulty field name.

  Background:
    Given http baseUri is /api/
    And I set http headers to:
      | Accept       | application/json |
      | Content-Type | application/json |

  Scenario Outline: Should reject a user created without <missingField>
    And I set http body to <payload>
    When I POST /users
    Then http response code should be 400
    And http response body should be valid json
    And http response body path $.field should be <missingField>
    And http response body path $.error should exists
    When I GET /users
    Then http response code should be 200
    And http response body is typed as array using path $ with length 0

    Examples:
      | missingField | payload                                                          |
      | id           | {"firstName":"Peter","lastName":"Parker","age":"22"}             |
      | firstName    | {"id":"9001","lastName":"Parker","age":"22"}                     |
      | lastName     | {"id":"9001","firstName":"Peter","age":"22"}                     |
      | id           | {}                                                               |
      | id           | {"id":"   ","firstName":"Peter","lastName":"Parker","age":"22"}  |
      | firstName    | {"id":"9001","firstName":"","lastName":"Parker","age":"22"}      |
      | lastName     | {"id":"9001","firstName":"Peter","lastName":"  ","age":"22"}     |

  Scenario: Should create a user once every required field is provided
    And I set http body to {"id":"9001","firstName":"Peter","lastName":"Parker","age":"22"}
    When I POST /users
    Then http response code should be 201
    And http response body path $.id should be 9001
    When I GET /users
    Then http response code should be 200
    And http response body is typed as array using path $ with length 1
