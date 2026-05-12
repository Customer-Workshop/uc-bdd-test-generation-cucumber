package fr.redfroggy.bdd.restapi.glue;

import io.cucumber.java.en.Given;
import io.cucumber.java.en.Then;
import org.springframework.boot.test.web.client.TestRestTemplate;

import static org.assertj.core.api.Assertions.assertThat;

public class GoogleLoginStepDefinition {

    private final TestRestTemplate restTemplate;

    public GoogleLoginStepDefinition(TestRestTemplate restTemplate) {
        this.restTemplate = restTemplate;
    }

    @Then("^the response should contain a valid JWT token$")
    public void responseContainsValidJwtToken() {
        // Custom assertion logic to validate JWT token structure
        // e.g., check that the token has three dot-separated parts
    }

    @Given("^the Google OAuth service is available$")
    public void googleOAuthServiceIsAvailable() {
        // Optional: setup WireMock or verify connectivity to mock Google OAuth
    }
}
