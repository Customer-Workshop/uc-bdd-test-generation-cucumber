@users-validation
Feature: User validation

  Background:
    Given http baseUri is /api/
    And I set http headers to:
      | Accept       | application/json |
      | Content-Type | application/json |

  Scenario Outline: Reject a user missing a required field
    And I set http body to <body>
    When I POST /users
    Then http response code should be 400

    Examples:
      | body                                                        |
      | {"firstName":"Ada","lastName":"Lovelace"}                   |
      | {"id":"1","lastName":"Lovelace"}                            |
      | {"id":"1","firstName":"Ada"}                                |

  Scenario Outline: Reject invalid email
    And I set http body to {"id":"<id>","firstName":"Ada","lastName":"Lovelace","email":"<email>"}
    When I POST /users
    Then http response code should be 400

    Examples:
      | id | email             |
      | 1  | not-an-email      |
      | 2  | ada@              |

  Scenario Outline: Reject over-long names
    And I set http body to {"id":"<id>","firstName":"<firstName>","lastName":"<lastName>"}
    When I POST /users
    Then http response code should be 400

    Examples:
      | id | firstName | lastName                                                   |
      | 3  | ABCDEFGHIJKLMNOPQRSTUVWXYZABCDEFGHIJKLMNOPQRSTUVWXYZ      | Lovelace |
      | 4  | Ada       | ABCDEFGHIJKLMNOPQRSTUVWXYZABCDEFGHIJKLMNOPQRSTUVWXY        |

  Scenario Outline: Accept valid boundary users
    And I set http body to {"id":"<id>","firstName":"<firstName>","lastName":"Lovelace","email":"<email>"}
    When I POST /users
    Then http response code should be 201
    And http response body path $.id should be <id>

    Examples:
      | id | firstName                                                 | email            |
      | 5  | Ada                                                       |                  |
      | 6  | ABCDEFGHIJKLMNOPQRSTUVWXYZABCDEFGHIJKLMNOPQRSTUVWX        | ada@example.com  |
