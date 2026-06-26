@pets
Feature: Petstore API tests

  Background:
    Given http baseUri is /api/
    And I set http headers to:
      | Accept        | application/json  |
      | Content-Type  | application/json  |

  # ---------- CREATE ----------

  Scenario: Create a pet successfully
    When I set http body to {"id":"1","name":"Buddy","species":"Dog","status":"available","tags":["friendly","trained"]}
    And I POST /pets
    Then http response code should be 201
    And http response body should be valid json
    And http response body path $.id should be 1
    And http response body path $.name should be Buddy
    And http response body path $.species should be Dog
    And http response body path $.status should be available
    And http response body path $.tags should be ["friendly","trained"]
    And I store the value of http body path $.id as petId in scenario scope

  Scenario: Create a second pet
    When I set http body to {"id":"2","name":"Whiskers","species":"Cat","status":"adopted","tags":["indoor"]}
    And I POST /pets
    Then http response code should be 201
    And http response body path $.id should be 2
    And http response body path $.name should be Whiskers
    And http response body path $.species should be Cat
    And http response body path $.status should be adopted

  Scenario: Create a third pet for pagination
    When I set http body to {"id":"3","name":"Goldie","species":"Fish","status":"available","tags":["aquatic"]}
    And I POST /pets
    Then http response code should be 201
    And http response body path $.id should be 3
    And http response body path $.name should be Goldie

  # ---------- VALIDATION ERRORS ----------

  Scenario: Create pet fails when name is missing
    When I set http body to {"id":"10","species":"Dog","status":"available"}
    And I POST /pets
    Then http response code should be 400
    And http response body should be valid json
    And http response body path $.error should be Validation failed
    And http response body path $.message should be Name is required

  Scenario: Create pet fails when species is missing
    When I set http body to {"id":"11","name":"Rex","status":"available"}
    And I POST /pets
    Then http response code should be 400
    And http response body should be valid json
    And http response body path $.error should be Validation failed
    And http response body path $.message should be Species is required

  Scenario: Create pet fails when both name and species are missing
    When I set http body to {"id":"12","status":"available"}
    And I POST /pets
    Then http response code should be 400
    And http response body path $.error should be Validation failed

  # ---------- READ ----------

  Scenario: Get pet by id
    When I GET /pets/1
    Then http response code should be 200
    And http response body should be valid json
    And http response body path $.id should be 1
    And http response body path $.name should be Buddy
    And http response body path $.species should be Dog
    And http response body path $.status should be available
    And http response body path $.tags should be ["friendly","trained"]

  Scenario: Get pet not found
    When I GET /pets/99999
    Then http response code should be 404
    And http response body path $ should not have content

  # ---------- LIST ----------

  Scenario: List all pets
    When I GET /pets
    Then http response code should be 200
    And http response body should be valid json
    And http response body is typed as array for path $
    And http response body is typed as array using path $ with length 3
    And http response body path $.[0].id should be 1
    And http response body path $.[0].name should be Buddy
    And http response body path $.[1].id should be 2
    And http response body path $.[1].name should be Whiskers
    And http response body path $.[2].id should be 3
    And http response body path $.[2].name should be Goldie
    And http response body should contain Dog

  # ---------- PAGINATION ----------

  Scenario: List pets with pagination - first page
    And I set http query parameter page to 0
    And I set http query parameter size to 2
    When I GET /pets
    Then http response code should be 200
    And http response body should be valid json
    And http response body path $.page should be 0
    And http response body path $.size should be 2
    And http response body path $.totalElements should be 3
    And http response body path $.totalPages should be 2
    And http response body is typed as array using path $.content with length 2
    And http response body path $.content.[0].name should be Buddy
    And http response body path $.content.[1].name should be Whiskers

  Scenario: List pets with pagination - second page
    And I set http query parameter page to 1
    And I set http query parameter size to 2
    When I GET /pets
    Then http response code should be 200
    And http response body should be valid json
    And http response body path $.page should be 1
    And http response body path $.size should be 2
    And http response body path $.totalElements should be 3
    And http response body path $.totalPages should be 2
    And http response body is typed as array using path $.content with length 1
    And http response body path $.content.[0].name should be Goldie

  Scenario: List pets with pagination - page beyond range
    And I set http query parameter page to 5
    And I set http query parameter size to 2
    When I GET /pets
    Then http response code should be 200
    And http response body path $.page should be 5
    And http response body path $.totalElements should be 3
    And http response body is typed as array using path $.content with length 0

  # ---------- UPDATE ----------

  Scenario: Update a pet successfully
    When I set http body to {"id":"1","name":"Buddy Jr","species":"Dog","status":"adopted","tags":["friendly"]}
    And I PUT /pets/1
    Then http response code should be 200
    And http response body should be valid json
    And http response body path $.name should be Buddy Jr
    And http response body path $.status should be adopted
    When I GET /pets/1
    Then http response code should be 200
    And http response body path $.name should be Buddy Jr
    And http response body path $.status should be adopted

  Scenario: Update pet not found
    When I set http body to {"id":"99999","name":"Ghost","species":"Unknown","status":"available"}
    And I PUT /pets/99999
    Then http response code should be 404
    And http response body path $ should not have content

  Scenario: Update pet fails validation when name is missing
    When I set http body to {"id":"1","species":"Dog","status":"available"}
    And I PUT /pets/1
    Then http response code should be 400
    And http response body path $.error should be Validation failed
    And http response body path $.message should be Name is required

  # ---------- DELETE ----------

  Scenario: Delete pet not found
    When I DELETE /pets/99999
    Then http response code should be 404
    And http response body path $ should not have content

  @pets-cleanup
  Scenario: Delete all pets
    When I DELETE /pets/1
    Then http response code should be 200
    And I DELETE /pets/2
    Then http response code should be 200
    And I DELETE /pets/3
    Then http response code should be 200
    And I GET /pets
    And http response body is typed as array using path $ with length 0
    And http response body path $ should not have content
