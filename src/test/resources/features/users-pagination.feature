@user @user-pagination
Feature: Users api pagination and sorting tests

  Background:
    Given http baseUri is /api/
    And I set http headers to:
      | Accept        | application/json  |
      | Content-Type  | application/json  |
    And I set http body to {"id":"p2","firstName":"Bruce","lastName":"Wayne","age":50}
    And I POST /users
    And http response code should be 201
    And I set http body to {"id":"p1","firstName":"Tony","lastName":"Stark","age":42}
    And I POST /users
    And http response code should be 201
    And I set http body to {"id":"p3","firstName":"Steve","lastName":"Rogers","age":100}
    And I POST /users
    And http response code should be 201

  Scenario: Should return every user with the total count when no page is requested
    When I GET /users
    Then http response code should be 200
    And http response header X-Total-Count should be 3
    And http response body is typed as array using path $ with length 3
    And http response body path $.[0].id should be p2

  Scenario Outline: Should sort users on <sort> <order>
    Given I set http query parameter sort to <sort>
    And I set http query parameter order to <order>
    When I GET /users
    Then http response code should be 200
    And http response body is typed as array using path $ with length 3
    And http response body path $.[0].id should be <first>
    And http response body path $.[2].id should be <last>

    Examples:
      | sort      | order | first | last |
      | id        | asc   | p1    | p3   |
      | id        | desc  | p3    | p1   |
      | lastName  | asc   | p3    | p2   |
      | lastName  | desc  | p2    | p3   |
      | firstName | asc   | p2    | p1   |
      | age       | asc   | p1    | p3   |
      | age       | desc  | p3    | p1   |

  Scenario Outline: Should return page <page> of size <size> sorted by id
    Given I set http query parameter sort to id
    And I set http query parameter page to <page>
    And I set http query parameter size to <size>
    When I GET /users
    Then http response code should be 200
    And http response header X-Total-Count should be 3
    And http response body is typed as array using path $ with length <length>

    Examples: Pages within range
      | page | size | length |
      | 0    | 1    | 1      |
      | 0    | 2    | 2      |
      | 1    | 2    | 1      |
      | 0    | 3    | 3      |
      | 0    | 100  | 3      |

    Examples: Pages out of range
      | page     | size | length |
      | 2        | 2    | 0      |
      | 10       | 3    | 0      |
      | 30000000 | 100  | 0      |

  Scenario: Should keep the requested page when filtering by name
    Given I set http query parameter name to a
    And I set http query parameter sort to id
    And I set http query parameter page to 0
    And I set http query parameter size to 1
    When I GET /users
    Then http response code should be 200
    And http response header X-Total-Count should be 2
    And http response body is typed as array using path $ with length 1
    And http response body path $.[0].id should be p1

  Scenario Outline: Should reject invalid pagination and sorting parameters
    Given I set http query parameter <parameter> to <value>
    When I GET /users
    Then http response code should be 400
    And http response body path $.status should be 400
    And http response body path $.message should be <message>

    Examples:
      | parameter | value   | message                          |
      | page      | -1      | page cannot be negative          |
      | size      | 0       | size has to be between 1 and 100 |
      | size      | -5      | size has to be between 1 and 100 |
      | size      | 101     | size has to be between 1 and 100 |
      | sort      | unknown | Unknown sort field: unknown      |
      | order     | asc     | order requires a sort field      |

  Scenario: Should reject an unknown sort order
    Given I set http query parameter sort to id
    And I set http query parameter order to sideways
    When I GET /users
    Then http response code should be 400
    And http response body path $.message should be Unknown sort order: sideways
