@user @userCleanup
Feature: Users api creation error cases

  Background:
    Given http baseUri is /api/
    And I set http headers to:
      | Accept        | application/json |
      | Content-Type  | application/json |

  Scenario Outline: Should reject a user creation when <field> is missing
    Given I set http body to <payload>
    When I POST /users
    Then http response code should be 400
    And http response body should be valid json
    And http response body path $.field should be <field>
    And http response body path $.message should be <message>

    Examples:
      | field     | payload                                                             | message           |
      | id        | {"firstName":"Tony","lastName":"Stark","age":"42"}                  | id is required        |
      | id        | {"id":"","firstName":"Tony","lastName":"Stark","age":"42"}          | id is required        |
      | firstName | {"id":"100","lastName":"Stark","age":"42"}                          | firstName is required |
      | firstName | {"id":"100","firstName":"   ","lastName":"Stark","age":"42"}        | firstName is required |
      | lastName  | {"id":"100","firstName":"Tony","age":"42"}                          | lastName is required  |
      | lastName  | {"id":"100","firstName":"Tony","lastName":"","age":"42"}            | lastName is required  |

  Scenario Outline: Should reject a user creation with a duplicate id <id>
    Given I set http body to {"id":"<id>","firstName":"<firstName>","lastName":"<lastName>","age":"<age>"}
    When I POST /users
    Then http response code should be 201
    And http response body path $.id should be <id>
    Given I set http body to {"id":"<id>","firstName":"Other","lastName":"Duplicate","age":"33"}
    When I POST /users
    Then http response code should be 409
    And http response body path $.field should be id
    And http response body path $.message should be a user already exists with id <id>
    When I GET /users
    Then http response code should be 200
    And http response body is typed as array using path $ with length 1
    And http response body path $.[0].firstName should be <firstName>

    Examples:
      | id    | firstName | lastName | age |
      | 200   | Tony      | Stark    | 42  |
      | 201   | Bruce     | Wayne     | 50 |
      | 15948 | Bruce     | Banner   | 45  |
