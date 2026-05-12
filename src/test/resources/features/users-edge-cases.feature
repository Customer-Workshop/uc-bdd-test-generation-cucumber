Feature: Users API edge case tests

  Background:
    Given http baseUri is /api/
    And I set Accept-Language http header to en-US
    And I set http headers to:
      | Accept        | application/json  |
      | Content-Type  | application/json  |

  # ── Missing required fields ──────────────────────────────────────

  Scenario Outline: Creating a user with missing required fields returns 400
    When I set http body to <body>
    And I POST /users
    Then http response code should be 400

    Examples:
      | body                                                                    |
      | {"firstName":"NoId","lastName":"User","age":"25"}                        |
      | {"id":"","firstName":"Empty","lastName":"Id","age":"30"}                 |
      | {"id":"99","lastName":"NoFirstName","age":"35"}                          |
      | {"id":"","firstName":"","lastName":"AllBlank","age":"20"}                |

  # ── Duplicate ID ─────────────────────────────────────────────────

  Scenario: Creating a user with a duplicate ID returns 409
    When I set http body to {"id":"dup-1","firstName":"Alice","lastName":"Smith","age":"30"}
    And I POST /users
    Then http response code should be 201
    And http response body path $.id should be dup-1
    When I set http body to {"id":"dup-1","firstName":"Bob","lastName":"Jones","age":"25"}
    And I POST /users
    Then http response code should be 409
    And http response body path $.error should be User with id dup-1 already exists
    When I DELETE /users/dup-1
    Then http response code should be 200

  # ── Pagination ───────────────────────────────────────────────────

  Scenario: Paginated listing of users
    When I set http body to {"id":"pg-1","firstName":"Alpha","lastName":"One","age":"20"}
    And I POST /users
    Then http response code should be 201
    When I set http body to {"id":"pg-2","firstName":"Beta","lastName":"Two","age":"25"}
    And I POST /users
    Then http response code should be 201
    When I set http body to {"id":"pg-3","firstName":"Gamma","lastName":"Three","age":"30"}
    And I POST /users
    Then http response code should be 201
    And I set http query parameter page to 0
    And I set http query parameter size to 2
    When I GET /users
    Then http response code should be 200
    And http response body is typed as array using path $ with length 2
    And I set http query parameter page to 1
    And I set http query parameter size to 2
    When I GET /users
    Then http response code should be 200
    And http response body is typed as array using path $ with length 1
    And I set http query parameter page to 5
    And I set http query parameter size to 2
    When I GET /users
    Then http response code should be 200
    And http response body is typed as array using path $ with length 0
    When I DELETE /users/pg-1
    And I DELETE /users/pg-2
    And I DELETE /users/pg-3

  # ── Sorting ──────────────────────────────────────────────────────

  Scenario: Sorted listing of users by firstName ascending
    When I set http body to {"id":"st-1","firstName":"Charlie","lastName":"X","age":"40"}
    And I POST /users
    Then http response code should be 201
    When I set http body to {"id":"st-2","firstName":"Alice","lastName":"Y","age":"20"}
    And I POST /users
    Then http response code should be 201
    When I set http body to {"id":"st-3","firstName":"Bob","lastName":"Z","age":"30"}
    And I POST /users
    Then http response code should be 201
    And I set http query parameter sort to firstName,asc
    When I GET /users
    Then http response code should be 200
    And http response body is typed as array using path $ with length 3
    And http response body path $.[0].firstName should be Alice
    And http response body path $.[1].firstName should be Bob
    And http response body path $.[2].firstName should be Charlie
    When I DELETE /users/st-1
    And I DELETE /users/st-2
    And I DELETE /users/st-3

  Scenario: Sorted listing of users by age descending
    When I set http body to {"id":"sa-1","firstName":"Young","lastName":"A","age":"20"}
    And I POST /users
    Then http response code should be 201
    When I set http body to {"id":"sa-2","firstName":"Old","lastName":"B","age":"60"}
    And I POST /users
    Then http response code should be 201
    When I set http body to {"id":"sa-3","firstName":"Mid","lastName":"C","age":"40"}
    And I POST /users
    Then http response code should be 201
    And I set http query parameter sort to age,desc
    When I GET /users
    Then http response code should be 200
    And http response body path $.[0].firstName should be Old
    And http response body path $.[1].firstName should be Mid
    And http response body path $.[2].firstName should be Young
    When I DELETE /users/sa-1
    And I DELETE /users/sa-2
    And I DELETE /users/sa-3

  # ── Input validation ─────────────────────────────────────────────

  Scenario Outline: Creating a user with invalid email returns 400
    When I set http body to <body>
    And I POST /users
    Then http response code should be 400

    Examples:
      | body                                                                                    |
      | {"id":"em-1","firstName":"Test","lastName":"User","age":"25","email":"not-an-email"}     |
      | {"id":"em-2","firstName":"Test","lastName":"User","age":"25","email":"missing@"}         |
      | {"id":"em-3","firstName":"Test","lastName":"User","age":"25","email":"@nodomain.com"}    |

  Scenario: Creating a user with a valid email succeeds
    When I set http body to {"id":"em-ok","firstName":"Valid","lastName":"Email","age":"25","email":"valid@example.com"}
    And I POST /users
    Then http response code should be 201
    And http response body path $.email should be valid@example.com
    When I DELETE /users/em-ok
    Then http response code should be 200

  Scenario: Creating a user with a too-long first name returns 400
    When I set http body to {"id":"ln-1","firstName":"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA","lastName":"TooLong","age":"30"}
    And I POST /users
    Then http response code should be 400
