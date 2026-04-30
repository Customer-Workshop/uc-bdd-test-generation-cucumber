Feature: Users API data-driven tests

  Background:
    Given http baseUri is /api/
    And I set Accept-Language http header to en-US
    And I set http headers to:
      | Accept       | application/json |
      | Content-Type | application/json |

  # --- Authentication (prerequisite) ---
  Scenario: Authenticate before data-driven tests
    When I authenticate with login/password tstark/marvel
    And I HEAD /authenticated
    Then http response code should be 200
    And I store the value of http response header Authorization as authToken in scenario scope

  # --- Parameterized user creation ---
  Scenario Outline: Create user <firstName> <lastName>
    When I authenticate with login/password tstark/marvel
    And I set http body to {"id":"<id>","firstName":"<firstName>","lastName":"<lastName>","age":"<age>", "sessionIds": [<sessionIds>]}
    And I POST /users
    Then http response code should be 201
    And http response body path $.id should be <id>
    And http response body path $.firstName should be <firstName>
    And http response body path $.lastName should be <lastName>
    And http response body path $.age should be <age>

    Examples:
      | id          | firstName | lastName | age | sessionIds                |
      | 1           | Tony      | Stark    | 42  | "43233333", "45654345"    |
      | 2           | Bruce     | Wayne    | 50  | "43233333"                |
      | 3           | Peter     | Parker   | 25  | "11111111"                |
      | 4           | Clark     | Kent     | 35  | "22222222", "33333333"    |

  # --- Parameterized user retrieval ---
  Scenario Outline: Get user by ID <id> should return <firstName> <lastName>
    When I GET /users/<id>
    Then http response code should be <expectedStatus>
    And http response body path $.firstName should be <firstName>
    And http response body path $.lastName should be <lastName>

    Examples:
      | id    | expectedStatus | firstName | lastName |
      | 1     | 200            | Tony      | Stark    |
      | 2     | 200            | Bruce     | Wayne    |

  # --- Parameterized search ---
  Scenario Outline: Search users by name "<searchTerm>" should return <expectedCount> results
    And I set http query parameter name to <searchTerm>
    When I GET /users
    And http response body should be valid json
    Then http response code should be 200
    And http response body is typed as array using path $ with length <expectedCount>

    Examples:
      | searchTerm  | expectedCount |
      | stark       | 1             |
      | wayne       | 1             |
      | bruce       | 1             |
      | nonexistent | 0             |

  # --- Parameterized user update ---
  Scenario Outline: Update user <id> field <field> to <newValue>
    When I set http body to {"<field>":"<newValue>"}
    And I PATCH /users/<id>
    Then http response code should be 200
    And http response body path $.<field> should be <newValue>
    When I GET /users/<id>
    Then http response code should be 200
    And http response body path $.<field> should be <newValue>

    Examples:
      | id | field     | newValue |
      | 1  | age       | 60       |
      | 2  | lastName  | WAYNE    |

  # --- Parameterized deletion ---
  Scenario Outline: Delete user <id> should return <expectedStatus>
    When I DELETE /users/<id>
    Then http response code should be <expectedStatus>

    Examples:
      | id    | expectedStatus |
      | 1     | 200            |
      | 2     | 200            |
      | 99999 | 404            |

  # --- Parameterized validation (negative tests) ---
  Scenario Outline: Creating user with invalid data should fail - <description>
    When I authenticate with login/password tstark/marvel
    And I set http body to <body>
    And I POST /users
    Then http response code should not be 201

    Examples:
      | description        | body                                                                    |
      | missing id         | {"firstName":"Test","lastName":"User","age":"30","sessionIds":[]}        |
      | missing firstName  | {"id":"99","lastName":"User","age":"30","sessionIds":[]}                 |
      | empty body         | {}                                                                       |
