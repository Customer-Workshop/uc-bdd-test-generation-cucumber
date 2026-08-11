@user @userCleanup
Feature: Users api input validation

  Background:
    Given http baseUri is /api/
    And I set http headers to:
      | Accept        | application/json |
      | Content-Type  | application/json |

  Scenario Outline: Should reject the invalid email <email>
    Given I set http body to {"id":"300","firstName":"Tony","lastName":"Stark","age":"42","email":"<email>"}
    When I POST /users
    Then http response code should be 400
    And http response body path $.field should be email
    And http response body path $.message should be email is invalid
    When I GET /users
    Then http response body is typed as array using path $ with length 0

    Examples:
      | email                |
      | not-an-email         |
      | missing-at-sign.com  |
      | tony@stark           |
      | tony@@stark.com      |
      | @stark.com           |
      | tony@.com            |

  Scenario Outline: Should accept the valid email <email>
    Given I set http body to {"id":"301","firstName":"Tony","lastName":"Stark","age":"42","email":"<email>"}
    When I POST /users
    Then http response code should be 201
    And http response body path $.email should be <email>

    Examples:
      | email                             |
      | tony@stark.com                    |
      | bruce.wayne@wayne-enterprises.com |
      | peter+parker@daily.bugle.co.uk    |

  Scenario Outline: Should reject a <field> longer than 50 characters
    Given I set http body to <payload>
    When I POST /users
    Then http response code should be 400
    And http response body path $.field should be <field>
    And http response body path $.message should be <field> must not exceed 50 characters

    Examples:
      | field     | payload                                                                                                                            |
      | firstName | {"id":"302","firstName":"Anthonyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy","lastName":"Stark","age":"42"}                |
      | lastName  | {"id":"302","firstName":"Tony","lastName":"Starkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkk","age":"42"}                   |

  Scenario Outline: Should reject the out of range age <age>
    Given I set http body to {"id":"303","firstName":"Tony","lastName":"Stark","age":"<age>"}
    When I POST /users
    Then http response code should be 400
    And http response body path $.field should be age
    And http response body path $.message should be age is out of the 1-149 range

    Examples:
      | age  |
      | 0    |
      | -1   |
      | 150  |
      | 1000 |

  Scenario Outline: Should reject an update of an existing user with an invalid <field>
    Given I set http body to {"id":"304","firstName":"Tony","lastName":"Stark","age":"42"}
    When I POST /users
    Then http response code should be 201
    Given I set http body to <payload>
    When I PUT /users/304
    Then http response code should be 400
    And http response body path $.field should be <field>
    When I mock third party api call GET /public/characters/304 with return code 200, content type: application/json and body: {"comicName": "IronMan", "city": "New York", "mainColor": ["red"]}
    And I GET /users/304
    Then http response code should be 200
    And http response body path $.firstName should be Tony
    And http response body path $.lastName should be Stark

    Examples:
      | field     | payload                                                                        |
      | firstName | {"id":"304","firstName":"","lastName":"Stark","age":"42"}                      |
      | lastName  | {"id":"304","firstName":"Tony","age":"42"}                                     |
      | age       | {"id":"304","firstName":"Tony","lastName":"Stark","age":"999"}                 |
      | email     | {"id":"304","firstName":"Tony","lastName":"Stark","age":"42","email":"nope"}   |
