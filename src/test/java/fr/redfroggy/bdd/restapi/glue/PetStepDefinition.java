package fr.redfroggy.bdd.restapi.glue;

import fr.redfroggy.bdd.restapi.pet.PetController;
import io.cucumber.java.After;

/**
 * Step definitions and lifecycle hooks for Petstore API BDD scenarios.
 * Leverages the generic REST API steps from {@link DefaultRestApiBddStepDefinition}
 * for all HTTP operations, JSON path assertions, header checks, and variable storage.
 *
 * The pets feature relies on cumulative state across scenarios (create first,
 * then read/update/delete), mirroring the pattern used by users.feature.
 * The final "Delete all pets" scenario handles cleanup within the feature,
 * and the {@code @pets-cleanup} hook provides a safety net.
 */
public class PetStepDefinition {

    @After("@pets-cleanup")
    public void afterPetCleanup() {
        PetController.pets.clear();
    }
}
