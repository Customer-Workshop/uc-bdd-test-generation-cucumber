package fr.redfroggy.bdd.restapi.glue;

import fr.redfroggy.bdd.restapi.authentication.BddRestTemplateAuthentication;
import fr.redfroggy.bdd.restapi.user.UserController;
import fr.redfroggy.bdd.restapi.order.OrderController;
import io.cucumber.java.After;
import io.cucumber.spring.CucumberContextConfiguration;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.client.TestRestTemplate;

/**
 * This file is mandatory for cucumber tests because it needs a Cucumber context to be able to work.
 * In this file you can add your own steps implementation.
 */
@CucumberContextConfiguration
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.DEFINED_PORT, properties = {
        "marvel.api.host=http://localhost:18089",
        "redfroggy.cucumber.restapi.wiremock.port=18089"
})
public class DefaultRestApiStepDefinitionTest implements BddRestTemplateAuthentication {

    final TestRestTemplate template;

    public DefaultRestApiStepDefinitionTest(TestRestTemplate template) {
        this.template = template;
    }

    @Override
    public TestRestTemplate authenticate(String login, String password) {
        return this.template.withBasicAuth(login, password);
    }

    @After("@import")
    public void afterImport() {
        UserController.users.clear();
    }

    @After("@users-validation or @users-conflict or @users-pagination")
    public void afterUsersEdgeCases() {
        UserController.users.clear();
    }

    @After("@orders")
    public void afterOrders() {
        OrderController.orders.clear();
    }

}
