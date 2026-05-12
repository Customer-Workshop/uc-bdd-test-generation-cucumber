Feature: Users API edge cases

  Background:
    Given http baseUri is /api/
    And I set http headers to:
      | Accept        | application/json  |
      | Content-Type  | application/json  |

  # -----------------------------------------------------------------------
  # 1. Creating a user with missing required fields (expect 400)
  # -----------------------------------------------------------------------
  Scenario Outline: Creating a user with missing required fields returns 400
    When I set http body to <body>
    And I POST /users
    Then http response code should be 400
    And http response body path $.error should be <expectedError>

    Examples:
      | body                                                         | expectedError                          |
      | {"firstName":"Tony","lastName":"Stark","age":"40"}           | id is required                         |
      | {"id":"99","lastName":"Stark","age":"40"}                    | firstName is required                  |
      | {"id":"99","firstName":"Tony","age":"40"}                    | lastName is required                   |

  # -----------------------------------------------------------------------
  # 2. Creating a user with duplicate ID (expect 409)
  # -----------------------------------------------------------------------
  Scenario: Setup user for duplicate test
    When I set http body to {"id":"dup-1","firstName":"Clark","lastName":"Kent","age":"35"}
    And I POST /users
    Then http response code should be 201
    And http response body path $.id should be dup-1

  Scenario: Creating a user with duplicate ID returns 409
    When I set http body to {"id":"dup-1","firstName":"Diana","lastName":"Prince","age":"30"}
    And I POST /users
    Then http response code should be 409
    And http response body should contain already exists

  # -----------------------------------------------------------------------
  # 3. Input validation - invalid email and too-long names
  # -----------------------------------------------------------------------
  Scenario Outline: Creating a user with invalid email returns 400
    When I set http body to {"id":"<id>","firstName":"Test","lastName":"User","age":"25","email":"<email>"}
    And I POST /users
    Then http response code should be 400
    And http response body path $.error should be invalid email format

    Examples:
      | id    | email             |
      | em-1  | not-an-email      |
      | em-2  | @missing-local    |
      | em-3  | missing@           |

  Scenario: Creating a user with valid email succeeds
    When I set http body to {"id":"em-ok","firstName":"Valid","lastName":"Email","age":"30","email":"valid@example.com"}
    And I POST /users
    Then http response code should be 201
    And http response body path $.email should be valid@example.com

  Scenario Outline: Creating a user with too-long name returns 400
    When I set http body to {"id":"<id>","firstName":"<firstName>","lastName":"<lastName>","age":"25"}
    And I POST /users
    Then http response code should be 400
    And http response body should contain exceeds maximum length

    Examples:
      | id     | firstName                                                                                                       | lastName  |
      | ln-1   | Test                                                                                                            | AAAAAAAAAABBBBBBBBBBCCCCCCCCCCDDDDDDDDDDEEEEEEEEEEAAAAAAAAAABBBBBBBBBBCCCCCCCCCCDDDDDDDDDDEEEEEEEEEEFFFFFFFFFFFF |
      | ln-2   | AAAAAAAAAABBBBBBBBBBCCCCCCCCCCDDDDDDDDDDEEEEEEEEEEAAAAAAAAAABBBBBBBBBBCCCCCCCCCCDDDDDDDDDDEEEEEEEEEEFFFFFFFFFFFF  | Test      |

  # -----------------------------------------------------------------------
  # 4. Pagination and sorting
  # -----------------------------------------------------------------------
  Scenario: Setup multiple users for pagination and sorting tests
    When I set http body to {"id":"pg-1","firstName":"Alice","lastName":"Zulu","age":"30"}
    And I POST /users
    Then http response code should be 201
    When I set http body to {"id":"pg-2","firstName":"Bob","lastName":"Yankee","age":"25"}
    And I POST /users
    Then http response code should be 201
    When I set http body to {"id":"pg-3","firstName":"Charlie","lastName":"Xray","age":"35"}
    And I POST /users
    Then http response code should be 201

  Scenario: Paginate users - first page
    And I set http query parameter page to 0
    And I set http query parameter size to 2
    When I GET /users
    Then http response code should be 200
    And http response body is typed as array using path $ with length 2

  Scenario: Paginate users - second page
    And I set http query parameter page to 1
    And I set http query parameter size to 2
    When I GET /users
    Then http response code should be 200
    And http response body should be valid json

  Scenario: Paginate users - beyond available data returns empty
    And I set http query parameter page to 100
    And I set http query parameter size to 10
    When I GET /users
    Then http response code should be 200
    And http response body is typed as array using path $ with length 0

  Scenario: Sort users by firstName ascending
    And I set http query parameter sort to firstName,asc
    When I GET /users
    Then http response code should be 200
    And http response body is typed as array for path $
    And http response body path $.[0].firstName should be Alice

  Scenario: Sort users by age descending
    And I set http query parameter sort to age,desc
    When I GET /users
    Then http response code should be 200
    And http response body is typed as array for path $
    And http response body path $.[0].age should be 35

  # -----------------------------------------------------------------------
  # Cleanup
  # -----------------------------------------------------------------------
  Scenario: Clean up edge case test users
    When I DELETE /users/dup-1
    Then http response code should be 200
    When I DELETE /users/em-ok
    Then http response code should be 200
    When I DELETE /users/pg-1
    Then http response code should be 200
    When I DELETE /users/pg-2
    Then http response code should be 200
    When I DELETE /users/pg-3
    Then http response code should be 200
