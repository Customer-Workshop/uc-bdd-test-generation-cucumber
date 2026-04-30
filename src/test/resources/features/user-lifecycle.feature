Feature: User lifecycle end-to-end tests

  Background:
    Given http baseUri is /api/
    And I set http headers to:
    | Accept        | application/json  |
    | Content-Type  | application/json  |

  Scenario: Create a new user
    When I set http body to {"id":"100","firstName":"Clark","lastName":"Kent","age":"35","sessionIds":["88881111"]}
    And I POST /users
    Then http response code should be 201
    And http response body should be valid json
    And http response body path $.id should be 100
    And http response body path $.firstName should be Clark
    And http response body path $.lastName should be Kent
    And http response body path $.age should be 35
    And I store the value of http body path $.id as lifecycleUserId in scenario scope

  Scenario: Verify the created user appears in the users list
    When I GET /users
    Then http response code should be 200
    And http response body should be valid json
    And http response body is typed as array for path $
    And http response body should contain Clark
    And http response body should contain Kent

  Scenario: Verify the created user can be retrieved by id
    When I mock third party api call GET /public/characters/100 with return code 200, content type: application/json and body: {"comicName": "Superman", "city": "Metropolis", "mainColor": ["blue", "red"]}
    And I GET /users/100
    Then http response code should be 200
    And http response body should be valid json
    And http response body path $.id should be 100
    And http response body path $.firstName should be Clark
    And http response body path $.lastName should be Kent
    And http response body path $.age should be 35

  Scenario: Update the user details
    When I mock third party api call GET /public/characters/100 with return code 200, content type: application/json and body: {"comicName": "Superman", "city": "Metropolis", "mainColor": ["blue", "red"]}
    And I set http body to {"id":"100","firstName":"Clark","lastName":"Kent-Lane","age":"36"}
    And I PUT /users/100
    Then http response code should be 200
    And http response body should be valid json
    And http response body path $.lastName should be Kent-Lane
    And http response body path $.age should be 36

  Scenario: Verify the update is persisted
    When I mock third party api call GET /public/characters/100 with return code 200, content type: application/json and body: {"comicName": "Superman", "city": "Metropolis", "mainColor": ["blue", "red"]}
    And I GET /users/100
    Then http response code should be 200
    And http response body path $.lastName should be Kent-Lane
    And http response body path $.age should be 36

  Scenario: Delete the user
    When I DELETE /users/100
    Then http response code should be 200

  Scenario: Verify the deleted user is gone
    When I GET /users/100
    Then http response code should be 404
    And http response body path $ should not have content
