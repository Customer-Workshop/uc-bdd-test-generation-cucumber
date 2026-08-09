@users-pagination
Feature: User pagination

  Background:
    Given http baseUri is /api/
    And I set http headers to:
      | Accept       | application/json |
      | Content-Type | application/json |

  Scenario Outline: Page users with sorting
    And I set http body to {"id":"1","firstName":"Zoe","lastName":"Zed"}
    When I POST /users
    And I set http body to {"id":"2","firstName":"Amy","lastName":"Young"}
    And I POST /users
    And I set http body to {"id":"3","firstName":"Mike","lastName":"Xavier"}
    And I POST /users
    And I set http body to {"id":"4","firstName":"Bob","lastName":"Wilson"}
    And I POST /users
    And I set http query parameter page to <page>
    And I set http query parameter size to <size>
    And I set http query parameter sort to <sort>
    When I GET /users
    Then http response code should be 200
    And http response body is typed as array using path $ with length <length>
    And http response body path $.[0].firstName should be <firstName>
    And http response header X-Total-Count should be 4

    Examples:
      | page | size | sort           | length | firstName |
      | 0    | 2    | firstName,asc  | 2      | Amy       |
      | 1    | 2    | firstName,asc  | 2      | Mike      |
      | 0    | 1    | firstName,desc | 1      | Zoe       |

  Scenario Outline: Reject invalid pagination
    And I set http query parameter <parameter> to <value>
    When I GET /users
    Then http response code should be 400

    Examples:
      | parameter | value        |
      | page      | -1           |
      | size      | 0            |
      | size      | 101          |
      | sort      | unknown,asc  |
