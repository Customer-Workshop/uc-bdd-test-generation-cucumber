@user @edge-case @cleanup-users
Feature: Users api - duplicate user id
  Ids are unique: creating a user with an already used id must be rejected with a 409 conflict
  and must not overwrite the existing user.

  Background:
    Given http baseUri is /api/
    And I set http headers to:
      | Accept       | application/json |
      | Content-Type | application/json |
    And I set http body to {"id":"9100","firstName":"Natasha","lastName":"Romanoff","age":"35"}
    When I POST /users
    Then http response code should be 201

  Scenario Outline: Should reject a second user using the id 9100 (<description>)
    And I set http body to <payload>
    When I POST /users
    Then http response code should be 409
    And http response body should be valid json
    And http response body path $.field should be id
    And http response body should contain already exists

    Examples:
      | description        | payload                                                             |
      | same payload       | {"id":"9100","firstName":"Natasha","lastName":"Romanoff","age":"35"} |
      | different names    | {"id":"9100","firstName":"Clint","lastName":"Barton","age":"41"}     |
      | extra email field  | {"id":"9100","firstName":"Clint","lastName":"Barton","age":"41","email":"clint@shield.com"} |

  Scenario: Should keep the original user untouched after a duplicate creation attempt
    And I set http body to {"id":"9100","firstName":"Clint","lastName":"Barton","age":"41"}
    When I POST /users
    Then http response code should be 409
    When I GET /users
    Then http response code should be 200
    And http response body is typed as array using path $ with length 1
    And http response body path $.[0].firstName should be Natasha
    And http response body path $.[0].lastName should be Romanoff
    And http response body path $.[0].age should be 35

  Scenario: Should allow the id to be reused once the user is deleted
    When I DELETE /users/9100
    Then http response code should be 200
    And I set http body to {"id":"9100","firstName":"Clint","lastName":"Barton","age":"41"}
    When I POST /users
    Then http response code should be 201
    And http response body path $.firstName should be Clint
