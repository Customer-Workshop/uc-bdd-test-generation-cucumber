@user @edge-case @cleanup-users
Feature: Users api - input validation
  Emails must be well formed, names must not exceed 50 characters and the age must be a realistic value.

  Background:
    Given http baseUri is /api/
    And I set http headers to:
      | Accept       | application/json |
      | Content-Type | application/json |

  Scenario Outline: Should reject the invalid email <email>
    And I set http body to {"id":"9300","firstName":"Steve","lastName":"Rogers","age":"44","email":"<email>"}
    When I POST /users
    Then http response code should be 400
    And http response body path $.field should be email
    And http response body should contain valid email address

    Examples:
      | email                |
      | not-an-email         |
      | missing-at.example   |
      | @example.com         |
      | steve@               |
      | steve@example        |
      | steve@@example.com   |
      | steve rogers@ex.com  |

  Scenario Outline: Should accept the valid email <email>
    And I set http body to {"id":"<id>","firstName":"Steve","lastName":"Rogers","age":"44","email":"<email>"}
    When I POST /users
    Then http response code should be 201
    And http response body path $.email should be <email>

    Examples:
      | id   | email                       |
      | 9301 | steve.rogers@example.com    |
      | 9302 | steve+avengers@example.com  |
      | 9303 | s@example.co.uk             |

  Scenario Outline: Should reject a <field> longer than 50 characters
    And I set http body to <payload>
    When I POST /users
    Then http response code should be 400
    And http response body path $.field should be <field>
    And http response body should contain must not exceed 50 characters

    Examples:
      | field     | payload                                                                                                                         |
      | firstName | {"id":"9310","firstName":"aaaaaaaaaabbbbbbbbbbccccccccccddddddddddeeeeeeeeeef","lastName":"Rogers","age":"44"}                   |
      | lastName  | {"id":"9310","firstName":"Steve","lastName":"aaaaaaaaaabbbbbbbbbbccccccccccddddddddddeeeeeeeeeef","age":"44"}                    |
      | firstName | {"id":"9310","firstName":"aaaaaaaaaabbbbbbbbbbccccccccccddddddddddeeeeeeeeeeffffffffff","lastName":"Rogers","age":"44"}          |

  Scenario Outline: Should accept a <field> of exactly 50 characters
    And I set http body to <payload>
    When I POST /users
    Then http response code should be 201
    And http response body path $.id should be <id>

    Examples:
      | id   | field     | payload                                                                                                        |
      | 9320 | firstName | {"id":"9320","firstName":"aaaaaaaaaabbbbbbbbbbccccccccccddddddddddeeeeeeeeee","lastName":"Rogers","age":"44"}   |
      | 9321 | lastName  | {"id":"9321","firstName":"Steve","lastName":"aaaaaaaaaabbbbbbbbbbccccccccccddddddddddeeeeeeeeee","age":"44"}    |

  Scenario Outline: Should reject the out of range age <age>
    And I set http body to {"id":"9330","firstName":"Steve","lastName":"Rogers","age":"<age>"}
    When I POST /users
    Then http response code should be 400
    And http response body path $.field should be age
    And http response body should contain age must be between 0 and 150

    Examples:
      | age  |
      | -1   |
      | -100 |
      | 151  |
      | 9999 |

  Scenario: Should reject an update introducing an invalid email
    And I set http body to {"id":"9340","firstName":"Steve","lastName":"Rogers","age":"44"}
    When I POST /users
    Then http response code should be 201
    And I set http body to {"id":"9340","firstName":"Steve","lastName":"Rogers","age":"44","email":"nope"}
    When I PUT /users/9340
    Then http response code should be 400
    And http response body path $.field should be email
