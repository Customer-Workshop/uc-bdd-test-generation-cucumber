package fr.redfroggy.bdd.restapi.glue;

import fr.redfroggy.bdd.restapi.pet.PetController;
import io.cucumber.java.After;

/**
 * Step definitions specific to Petstore scenarios.
 * Leverages the existing DefaultRestApiBddStepDefinition for all HTTP verb
 * and assertion steps; this class provides only lifecycle hooks.
 */
public class PetStoreStepDefinition {

    @After("@petstore-cleanup")
    public void afterPetstoreCleanup() {
        PetController.pets.clear();
    }
}
