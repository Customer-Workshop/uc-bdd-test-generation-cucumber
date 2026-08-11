@user @userCleanup
Feature: Users api pagination and sorting

  Background:
    Given http baseUri is /api/
    And I set http headers to:
      | Accept        | application/json |
      | Content-Type  | application/json |
    And I set http body to {"id":"1","firstName":"Tony","lastName":"Stark","age":"42"}
    And I POST /users
    And I set http body to {"id":"2","firstName":"Bruce","lastName":"Wayne","age":"50"}
    And I POST /users
    And I set http body to {"id":"3","firstName":"Bruce","lastName":"Banner","age":"45"}
    And I POST /users
    And I set http body to {"id":"4","firstName":"Peter","lastName":"Parker","age":"22"}
    And I POST /users
    And I set http body to {"id":"5","firstName":"Steve","lastName":"Rogers","age":"44"}
    And I POST /users

  Scenario: Should return every user when no pagination is requested
    When I GET /users
    Then http response code should be 200
    And http response body is typed as array using path $ with length 5

  Scenario Outline: Should return page <page> of size <size>
    Given I set http query parameter page to <page>
    And I set http query parameter size to <size>
    When I GET /users
    Then http response code should be 200
    And http response body is typed as array using path $ with length <length>
    And http response body path $.[0].id should be <firstId>

    Examples:
      | page | size | length | firstId |
      | 0    | 2    | 2      | 1       |
      | 1    | 2    | 2      | 3       |
      | 2    | 2    | 1      | 5       |
      | 0    | 5    | 5      | 1       |
      | 0    | 10   | 5      | 1       |

  Scenario Outline: Should return an empty page for the out of range page <page>
    Given I set http query parameter page to <page>
    And I set http query parameter size to 2
    When I GET /users
    Then http response code should be 200
    And http response body is typed as array using path $ with length 0
    And http response body path $ should not have content

    Examples:
      | page |
      | 3    |
      | 10   |

  Scenario Outline: Should sort users by <sort>
    Given I set http query parameter sort to <sort>
    When I GET /users
    Then http response code should be 200
    And http response body is typed as array using path $ with length 5
    And http response body path $.[0].id should be <firstId>
    And http response body path $.[4].id should be <lastId>

    Examples:
      | sort           | firstId | lastId |
      | id,asc         | 1       | 5      |
      | id,desc        | 5       | 1      |
      | age,asc        | 4       | 2      |
      | age,desc       | 2       | 4      |
      | lastName,asc   | 3       | 2      |
      | lastName,desc  | 2       | 3      |
      | firstName,asc  | 2       | 1      |
      | firstName,desc | 1       | 3      |

  Scenario: Should combine name search, sorting and pagination
    Given I set http query parameter name to bruce
    And I set http query parameter sort to lastName,asc
    And I set http query parameter page to 0
    And I set http query parameter size to 1
    When I GET /users
    Then http response code should be 200
    And http response body is typed as array using path $ with length 1
    And http response body path $.[0].id should be 3
    And http response body path $.[0].lastName should be Banner

  Scenario Outline: Should reject the invalid pagination parameter <param>=<value>
    Given I set http query parameter <param> to <value>
    When I GET /users
    Then http response code should be 400
    And http response body path $.field should be <field>
    And http response body path $.message should be <message>

    Examples:
      | param | value        | field | message                                     |
      | page  | -1           | page  | page cannot be negative                     |
      | size  | 0            | size  | size cannot be lower than 1                 |
      | size  | -5           | size  | size cannot be lower than 1                 |
      | sort  | unknownField | sort  | unknown sort property unknownField          |
      | sort  | age,sideways | sort  | unknown sort direction sideways             |
