@user @user-validation
Feature: Users api validation and error handling tests

  Background:
    Given http baseUri is /api/
    And I set http headers to:
      | Accept        | application/json  |
      | Content-Type  | application/json  |

  Scenario Outline: Should reject a user creation with a missing required field
    Given I set http body to <body>
    When I POST /users
    Then http response code should be 400
    And http response body should be valid json
    And http response body path $.status should be 400
    And http response body path $.message should be Validation failed
    And http response body is typed as array using path $.errors with length 1
    And http response body path $.errors.[0].field should be <field>

    Examples:
      | field     | body                                                            |
      | id        | {"firstName":"Tony","lastName":"Stark","age":42}                |
      | id        | {"id":"  ","firstName":"Tony","lastName":"Stark","age":42}      |
      | firstName | {"id":"v1","lastName":"Stark","age":42}                         |
      | firstName | {"id":"v1","firstName":"","lastName":"Stark","age":42}          |
      | lastName  | {"id":"v1","firstName":"Tony","age":42}                         |
      | lastName  | {"id":"v1","firstName":"Tony","lastName":"","age":42}           |

  Scenario Outline: Should reject a user creation with an invalid field value
    Given I set http body to <body>
    When I POST /users
    Then http response code should be 400
    And http response body path $.status should be 400
    And http response body path $.errors.[0].field should be <field>

    Examples: Invalid emails
      | field | body                                                                                        |
      | email | {"id":"v2","firstName":"Tony","lastName":"Stark","age":42,"email":"tstark"}                 |
      | email | {"id":"v2","firstName":"Tony","lastName":"Stark","age":42,"email":"tstark@"}                |
      | email | {"id":"v2","firstName":"Tony","lastName":"Stark","age":42,"email":"@marvel.com"}            |
      | email | {"id":"v2","firstName":"Tony","lastName":"Stark","age":42,"email":"tstark @marvel.com"}     |

    Examples: Names longer than 50 characters
      | field     | body                                                                                                                              |
      | firstName | {"id":"v2","firstName":"Toooooooooooooooooooooooooooooooooooooooooooooooooo","lastName":"Stark","age":42}                      |
      | lastName  | {"id":"v2","firstName":"Tony","lastName":"Stttttttttttttttttttttttttttttttttttttttttttttttttt","age":42}                      |

    Examples: Age out of bounds
      | field | body                                                             |
      | age   | {"id":"v2","firstName":"Tony","lastName":"Stark","age":-1}       |
      | age   | {"id":"v2","firstName":"Tony","lastName":"Stark","age":151}      |

  Scenario Outline: Should accept a user creation on the validation boundaries
    Given I set http body to <body>
    When I POST /users
    Then http response code should be 201
    And http response body path $.id should be <id>
    And http response body path $.age should be <age>

    Examples:
      | id  | age | body                                                                                                                                    |
      | b1  | 0   | {"id":"b1","firstName":"Tony","lastName":"Stark","age":0}                                                                               |
      | b2  | 150 | {"id":"b2","firstName":"Tony","lastName":"Stark","age":150}                                                                             |
      | b3  | 42  | {"id":"b3","firstName":"Tooooooooooooooooooooooooooooooooooooooooooooooooo","lastName":"Stark","age":42,"email":"tstark@marvel.com"} |

  Scenario: Should report every invalid field of a user creation at once
    Given I set http body to {"id":"","firstName":"","lastName":"","age":200,"email":"nope"}
    When I POST /users
    Then http response code should be 400
    And http response body is typed as array using path $.errors with length 5
    And http response body path $.errors.[0].field should be age
    And http response body path $.errors.[1].field should be email
    And http response body path $.errors.[2].field should be firstName
    And http response body path $.errors.[3].field should be id
    And http response body path $.errors.[4].field should be lastName

  Scenario: Should reject a user creation with a duplicated id
    Given I set http body to {"id":"dup","firstName":"Tony","lastName":"Stark","age":42}
    When I POST /users
    Then http response code should be 201
    Given I set http body to {"id":"dup","firstName":"Bruce","lastName":"Wayne","age":50}
    When I POST /users
    Then http response code should be 409
    And http response body should be valid json
    And http response body path $.status should be 409
    And http response body path $.message should be User already exists with id: dup
    When I GET /users
    Then http response body is typed as array using path $ with length 1
    And http response body path $.[0].firstName should be Tony

  Scenario: Should reject a body that cannot be mapped to a user
    Given I set http body to {"id":"v3","firstName":"Tony","lastName":"Stark","age":"forty two"}
    When I POST /users
    Then http response code should be 400
    And http response body path $.message should be Malformed request body

  Scenario: Should reject an update with an invalid body
    Given I set http body to {"id":"v4","firstName":"Tony","lastName":"Stark","age":42}
    When I POST /users
    Then http response code should be 201
    Given I set http body to {"id":"v4","firstName":"Tony","lastName":"","age":42}
    And I PUT /users/v4
    Then http response code should be 400
    And http response body path $.errors.[0].field should be lastName

  Scenario: Should reject a patch with a blank last name
    Given I set http body to {"id":"v5","firstName":"Tony","lastName":"Stark","age":42}
    When I POST /users
    Then http response code should be 201
    Given I set http body to {"lastName":"   "}
    And I PATCH /users/v5
    Then http response code should be 400
    And http response body path $.errors.[0].field should be lastName

  Scenario: Should fail the user lookup when the third party details call fails
    Given I mock third party api call GET /public/characters/v6 with return code 500, content type: application/json and body: {"error": "marvel api is down"}
    And I set http body to {"id":"v6","firstName":"Tony","lastName":"Stark","age":42}
    When I POST /users
    Then http response code should be 201
    When I GET /users/v6
    Then http response code should be 400
    And http response body path $ should not have content

  Scenario: Should not update an unknown user
    Given I set http body to {"id":"missing","firstName":"Tony","lastName":"Stark","age":42}
    When I PUT /users/missing
    Then http response code should be 404
    And I PATCH /users/missing
    Then http response code should be 404
