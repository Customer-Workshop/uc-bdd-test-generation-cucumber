@user-edge-cases
Feature: Users API edge case tests

  Background:
    Given http baseUri is /api/
    And I set http headers to:
      | Accept        | application/json  |
      | Content-Type  | application/json  |

  # --- Missing required fields ---

  @user-edge-cases
  Scenario Outline: Creating a user with missing required fields should return 400
    When I set http body to <body>
    And I POST /users
    Then http response code should be 400
    And http response body should be valid json
    And http response body path $.errors should exists

    Examples:
      | body                                                                    |
      | {"id":"100","firstName":"","lastName":"Doe","age":"30"}                  |
      | {"id":"101","lastName":"Doe","age":"30"}                                |
      | {"id":"102","firstName":"Jane","lastName":"","age":"25"}                 |
      | {"id":"103","firstName":"Jane","age":"25"}                              |
      | {"firstName":"NoId","lastName":"User","age":"20"}                        |

  # --- Duplicate ID ---

  @user-edge-cases
  Scenario: Creating a user with duplicate ID should return 409
    When I set http body to {"id":"200","firstName":"Original","lastName":"User","age":"30"}
    And I POST /users
    Then http response code should be 201
    And http response body path $.id should be 200
    And http response body path $.firstName should be Original
    When I set http body to {"id":"200","firstName":"Duplicate","lastName":"User","age":"25"}
    And I POST /users
    Then http response code should be 409
    And http response body should be valid json
    And http response body path $.error should exists

  # --- Input validation: invalid email ---

  @user-edge-cases
  Scenario Outline: Creating a user with invalid email should return 400
    When I set http body to <body>
    And I POST /users
    Then http response code should be 400
    And http response body should be valid json
    And http response body path $.errors should exists

    Examples:
      | body                                                                                   |
      | {"id":"300","firstName":"John","lastName":"Doe","age":"30","email":"not-an-email"}      |
      | {"id":"301","firstName":"John","lastName":"Doe","age":"30","email":"missing@domain"}    |
      | {"id":"302","firstName":"John","lastName":"Doe","age":"30","email":"@nodomain.com"}     |
      | {"id":"303","firstName":"John","lastName":"Doe","age":"30","email":"spaces in@mail.com"}|

  @user-edge-cases
  Scenario: Creating a user with valid email should succeed
    When I set http body to {"id":"310","firstName":"Valid","lastName":"Email","age":"28","email":"valid@example.com"}
    And I POST /users
    Then http response code should be 201
    And http response body path $.email should be valid@example.com

  # --- Input validation: name too long ---

  @user-edge-cases
  Scenario Outline: Creating a user with too-long name should return 400
    When I set http body to <body>
    And I POST /users
    Then http response code should be 400
    And http response body should be valid json
    And http response body path $.errors should exists

    Examples:
      | body                                                                                                                                                                                       |
      | {"id":"400","firstName":"AaaaaaaaaaBbbbbbbbbbCcccccccccDdddddddddEeeeeeeeeeAaaaaaaaaaBbbbbbbbbbCcccccccccDdddddddddEeeeeeeeeeX","lastName":"Short","age":"30"}                               |
      | {"id":"401","firstName":"Short","lastName":"AaaaaaaaaaBbbbbbbbbbCcccccccccDdddddddddEeeeeeeeeeAaaaaaaaaaBbbbbbbbbbCcccccccccDdddddddddEeeeeeeeeeX","age":"30"}                                |

  # --- Pagination ---

  @user-edge-cases
  Scenario: Paginating users list
    When I set http body to {"id":"500","firstName":"Alice","lastName":"Anderson","age":"25"}
    And I POST /users
    Then http response code should be 201
    When I set http body to {"id":"501","firstName":"Bob","lastName":"Brown","age":"30"}
    And I POST /users
    Then http response code should be 201
    When I set http body to {"id":"502","firstName":"Charlie","lastName":"Clark","age":"35"}
    And I POST /users
    Then http response code should be 201
    When I set http query parameter page to 0
    And I set http query parameter size to 2
    And I GET /users
    Then http response code should be 200
    And http response body should be valid json
    And http response body path $.page should be 0
    And http response body path $.size should be 2
    And http response body path $.totalElements should be 3
    And http response body path $.totalPages should be 2
    And http response body is typed as array using path $.content with length 2
    When I set http query parameter page to 1
    And I set http query parameter size to 2
    And I GET /users
    Then http response code should be 200
    And http response body path $.page should be 1
    And http response body is typed as array using path $.content with length 1

  @user-edge-cases
  Scenario: Requesting a page beyond available data returns empty content
    When I set http body to {"id":"510","firstName":"Solo","lastName":"User","age":"40"}
    And I POST /users
    Then http response code should be 201
    When I set http query parameter page to 5
    And I set http query parameter size to 10
    And I GET /users
    Then http response code should be 200
    And http response body path $.totalElements should be 1
    And http response body is typed as array using path $.content with length 0

  # --- Sorting ---

  @user-edge-cases
  Scenario: Sorting users by firstName ascending
    When I set http body to {"id":"600","firstName":"Charlie","lastName":"Zoo","age":"30"}
    And I POST /users
    Then http response code should be 201
    When I set http body to {"id":"601","firstName":"Alice","lastName":"Young","age":"25"}
    And I POST /users
    Then http response code should be 201
    When I set http body to {"id":"602","firstName":"Bob","lastName":"Xavier","age":"35"}
    And I POST /users
    Then http response code should be 201
    And I set http query parameter sort to firstName,asc
    When I GET /users
    Then http response code should be 200
    And http response body path $.[0].firstName should be Alice
    And http response body path $.[1].firstName should be Bob
    And http response body path $.[2].firstName should be Charlie

  @user-edge-cases
  Scenario: Sorting users by age descending
    When I set http body to {"id":"700","firstName":"Young","lastName":"One","age":"20"}
    And I POST /users
    Then http response code should be 201
    When I set http body to {"id":"701","firstName":"Old","lastName":"One","age":"60"}
    And I POST /users
    Then http response code should be 201
    When I set http body to {"id":"702","firstName":"Mid","lastName":"One","age":"40"}
    And I POST /users
    Then http response code should be 201
    And I set http query parameter sort to age,desc
    When I GET /users
    Then http response code should be 200
    And http response body path $.[0].firstName should be Old
    And http response body path $.[1].firstName should be Mid
    And http response body path $.[2].firstName should be Young

  # --- Cleanup ---

  @user-edge-cases
  Scenario: Delete all edge case test users
    When I GET /users
    Then http response code should be 200
