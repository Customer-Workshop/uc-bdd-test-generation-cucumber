@user @edge-case @cleanup-users
Feature: Users api - pagination and sorting
  GET /users accepts page, size and sort query parameters.
  The payload stays a json array, pagination metadata is returned as http headers.

  Background:
    Given http baseUri is /api/
    And I set http headers to:
      | Accept       | application/json |
      | Content-Type | application/json |
    And I set http body to {"id":"9201","firstName":"Ann","lastName":"Alpha","age":"40"}
    When I POST /users
    Then http response code should be 201
    And I set http body to {"id":"9202","firstName":"Bob","lastName":"Bravo","age":"35"}
    When I POST /users
    Then http response code should be 201
    And I set http body to {"id":"9203","firstName":"Cara","lastName":"Charlie","age":"30"}
    When I POST /users
    Then http response code should be 201
    And I set http body to {"id":"9204","firstName":"Dan","lastName":"Delta","age":"25"}
    When I POST /users
    Then http response code should be 201
    And I set http body to {"id":"9205","firstName":"Eve","lastName":"Echo","age":"20"}
    When I POST /users
    Then http response code should be 201

  Scenario Outline: Should return page <page> of size <size> sorted by <sort>
    When I GET /users?page=<page>&size=<size>&sort=<sort>
    Then http response code should be 200
    And http response body should be valid json
    And http response header X-Total-Count should be 5
    And http response header X-Total-Pages should be <totalPages>
    And http response header X-Page should be <page>
    And http response header X-Page-Size should be <size>
    And http response body is typed as array using path $ with length <length>
    And http response body path $.[0].lastName should be <firstLastName>

    Examples:
      | page | size | sort           | totalPages | length | firstLastName |
      | 0    | 2    | lastName,asc   | 3          | 2      | Alpha         |
      | 1    | 2    | lastName,asc   | 3          | 2      | Charlie       |
      | 2    | 2    | lastName,asc   | 3          | 1      | Echo          |
      | 0    | 2    | lastName,desc  | 3          | 2      | Echo          |
      | 0    | 3    | age,asc        | 2          | 3      | Echo          |
      | 0    | 3    | age,desc       | 2          | 3      | Alpha         |
      | 0    | 5    | id,desc        | 1          | 5      | Echo          |
      | 0    | 10   | firstName,asc  | 1          | 5      | Alpha         |

  Scenario: Should default the sort direction to ascending
    When I GET /users?page=0&size=1&sort=lastName
    Then http response code should be 200
    And http response body is typed as array using path $ with length 1
    And http response body path $.[0].lastName should be Alpha

  Scenario: Should return an empty page after the last one
    When I GET /users?page=5&size=2&sort=lastName,asc
    Then http response code should be 200
    And http response header X-Total-Count should be 5
    And http response body is typed as array using path $ with length 0

  Scenario: Should paginate the users matching a name filter
    When I GET /users?name=a&page=0&size=2&sort=lastName,asc
    Then http response code should be 200
    And http response header X-Total-Count should be 4
    And http response body is typed as array using path $ with length 2
    And http response body path $.[0].lastName should be Alpha
    And http response body path $.[1].lastName should be Bravo

  Scenario: Should return every user when no pagination parameter is given
    When I GET /users
    Then http response code should be 200
    And http response body is typed as array using path $ with length 5

  Scenario Outline: Should reject invalid pagination parameters (<description>)
    When I GET /users?<query>
    Then http response code should be 400
    And http response body path $.field should be <field>
    And http response body path $.error should exists

    Examples:
      | description             | query                       | field |
      | negative page           | page=-1&size=2              | page  |
      | zero size               | page=0&size=0               | size  |
      | negative size           | page=0&size=-5              | size  |
      | unknown sort field      | page=0&size=2&sort=unknown  | sort  |
      | unknown sort direction  | page=0&size=2&sort=age,up   | sort  |
