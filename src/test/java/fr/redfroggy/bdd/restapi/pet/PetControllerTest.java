package fr.redfroggy.bdd.restapi.pet;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.After;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.junit4.SpringRunner;
import org.springframework.test.web.servlet.MockMvc;

import java.util.Arrays;
import java.util.Collections;

import static org.hamcrest.Matchers.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

/**
 * Non-BDD JUnit test class for PetController.
 * Covers functional, integration, boundary, negative, and idempotency scenarios.
 */
@RunWith(SpringRunner.class)
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT, properties = {
        "marvel.api.host=http://localhost:8888"
})
@AutoConfigureMockMvc
public class PetControllerTest {

    @Autowired
    private MockMvc mockMvc;

    private final ObjectMapper objectMapper = new ObjectMapper();

    @Before
    public void setUp() {
        PetController.pets.clear();
    }

    @After
    public void tearDown() {
        PetController.pets.clear();
    }

    // -----------------------------------------------------------------------
    // Helper
    // -----------------------------------------------------------------------

    private PetDTO buildPet(String id, String name, String species, String breed, int age, String status) {
        PetDTO pet = new PetDTO();
        pet.setId(id);
        pet.setName(name);
        pet.setSpecies(species);
        pet.setBreed(breed);
        pet.setAge(age);
        pet.setStatus(status);
        return pet;
    }

    private void createPetViaApi(PetDTO pet) throws Exception {
        mockMvc.perform(post("/api/pets")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(pet)))
                .andExpect(status().isCreated());
    }

    // -----------------------------------------------------------------------
    // TC-001: Create a pet with all fields
    // -----------------------------------------------------------------------
    @Test
    public void testCreatePetWithAllFields() throws Exception {
        PetDTO pet = buildPet("1", "Max", "Dog", "Labrador", 5, "available");
        pet.setTags(Arrays.asList("friendly", "vaccinated"));

        mockMvc.perform(post("/api/pets")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(pet)))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.id", is("1")))
                .andExpect(jsonPath("$.name", is("Max")))
                .andExpect(jsonPath("$.species", is("Dog")))
                .andExpect(jsonPath("$.breed", is("Labrador")))
                .andExpect(jsonPath("$.age", is(5)))
                .andExpect(jsonPath("$.status", is("available")))
                .andExpect(jsonPath("$.tags", hasSize(2)));
    }

    // -----------------------------------------------------------------------
    // TC-002: Create a pet with minimal required fields
    // -----------------------------------------------------------------------
    @Test
    public void testCreatePetMinimalFields() throws Exception {
        PetDTO pet = new PetDTO();
        pet.setId("2");
        pet.setName("Whiskers");
        pet.setSpecies("Cat");

        mockMvc.perform(post("/api/pets")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(pet)))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.status", is("available")));
    }

    // -----------------------------------------------------------------------
    // TC-003: Reject creation without name
    // -----------------------------------------------------------------------
    @Test
    public void testCreatePetWithoutName_ReturnsBadRequest() throws Exception {
        PetDTO pet = buildPet("3", null, "Dog", "Poodle", 3, "available");

        mockMvc.perform(post("/api/pets")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(pet)))
                .andExpect(status().isBadRequest());
    }

    // -----------------------------------------------------------------------
    // TC-004: Reject creation without species
    // -----------------------------------------------------------------------
    @Test
    public void testCreatePetWithoutSpecies_ReturnsBadRequest() throws Exception {
        PetDTO pet = buildPet("4", "Rex", null, "Shepherd", 2, "available");

        mockMvc.perform(post("/api/pets")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(pet)))
                .andExpect(status().isBadRequest());
    }

    // -----------------------------------------------------------------------
    // TC-005: Reject creation with empty name
    // -----------------------------------------------------------------------
    @Test
    public void testCreatePetWithEmptyName_ReturnsBadRequest() throws Exception {
        PetDTO pet = buildPet("5", "", "Dog", null, 1, "available");

        mockMvc.perform(post("/api/pets")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(pet)))
                .andExpect(status().isBadRequest());
    }

    // -----------------------------------------------------------------------
    // TC-006: Reject duplicate pet ID (conflict)
    // -----------------------------------------------------------------------
    @Test
    public void testCreateDuplicatePet_ReturnsConflict() throws Exception {
        PetDTO pet = buildPet("6", "Luna", "Cat", "Siamese", 2, "available");
        createPetViaApi(pet);

        mockMvc.perform(post("/api/pets")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(pet)))
                .andExpect(status().isConflict());
    }

    // -----------------------------------------------------------------------
    // TC-007: Get pet by ID
    // -----------------------------------------------------------------------
    @Test
    public void testGetPetById() throws Exception {
        PetDTO pet = buildPet("7", "Buddy", "Dog", "Golden Retriever", 3, "available");
        createPetViaApi(pet);

        mockMvc.perform(get("/api/pets/7")
                        .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.id", is("7")))
                .andExpect(jsonPath("$.name", is("Buddy")));
    }

    // -----------------------------------------------------------------------
    // TC-008: Get non-existent pet returns 404
    // -----------------------------------------------------------------------
    @Test
    public void testGetNonExistentPet_ReturnsNotFound() throws Exception {
        mockMvc.perform(get("/api/pets/99999")
                        .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isNotFound());
    }

    // -----------------------------------------------------------------------
    // TC-009: List all pets
    // -----------------------------------------------------------------------
    @Test
    public void testListAllPets() throws Exception {
        createPetViaApi(buildPet("9a", "Pet1", "Dog", null, 1, "available"));
        createPetViaApi(buildPet("9b", "Pet2", "Cat", null, 2, "available"));

        mockMvc.perform(get("/api/pets")
                        .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$", hasSize(2)));
    }

    // -----------------------------------------------------------------------
    // TC-010: List pets returns empty when none exist
    // -----------------------------------------------------------------------
    @Test
    public void testListPetsEmpty() throws Exception {
        mockMvc.perform(get("/api/pets")
                        .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$", hasSize(0)));
    }

    // -----------------------------------------------------------------------
    // TC-011: Filter pets by status
    // -----------------------------------------------------------------------
    @Test
    public void testFilterByStatus() throws Exception {
        createPetViaApi(buildPet("11a", "Available", "Dog", null, 1, "available"));
        createPetViaApi(buildPet("11b", "Sold", "Cat", null, 2, "sold"));

        mockMvc.perform(get("/api/pets")
                        .param("status", "sold")
                        .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$", hasSize(1)))
                .andExpect(jsonPath("$[0].name", is("Sold")));
    }

    // -----------------------------------------------------------------------
    // TC-012: Filter pets by species
    // -----------------------------------------------------------------------
    @Test
    public void testFilterBySpecies() throws Exception {
        createPetViaApi(buildPet("12a", "Dog1", "Dog", null, 1, "available"));
        createPetViaApi(buildPet("12b", "Cat1", "Cat", null, 2, "available"));

        mockMvc.perform(get("/api/pets")
                        .param("species", "Cat")
                        .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$", hasSize(1)))
                .andExpect(jsonPath("$[0].species", is("Cat")));
    }

    // -----------------------------------------------------------------------
    // TC-013: Pagination - page 0 size 1
    // -----------------------------------------------------------------------
    @Test
    public void testPaginationFirstPage() throws Exception {
        createPetViaApi(buildPet("13a", "P1", "Dog", null, 1, "available"));
        createPetViaApi(buildPet("13b", "P2", "Cat", null, 2, "available"));
        createPetViaApi(buildPet("13c", "P3", "Bird", null, 3, "available"));

        mockMvc.perform(get("/api/pets")
                        .param("page", "0")
                        .param("size", "1")
                        .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$", hasSize(1)));
    }

    // -----------------------------------------------------------------------
    // TC-014: Pagination - page beyond data returns empty
    // -----------------------------------------------------------------------
    @Test
    public void testPaginationBeyondData() throws Exception {
        createPetViaApi(buildPet("14a", "P1", "Dog", null, 1, "available"));

        mockMvc.perform(get("/api/pets")
                        .param("page", "100")
                        .param("size", "10")
                        .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$", hasSize(0)));
    }

    // -----------------------------------------------------------------------
    // TC-015: Full update (PUT)
    // -----------------------------------------------------------------------
    @Test
    public void testFullUpdate() throws Exception {
        createPetViaApi(buildPet("15", "Original", "Dog", "Pug", 3, "available"));

        PetDTO updated = buildPet("15", "Updated", "Dog", "Pug", 4, "sold");

        mockMvc.perform(put("/api/pets/15")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(updated)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.name", is("Updated")))
                .andExpect(jsonPath("$.age", is(4)))
                .andExpect(jsonPath("$.status", is("sold")));
    }

    // -----------------------------------------------------------------------
    // TC-016: Full update non-existent pet returns 404
    // -----------------------------------------------------------------------
    @Test
    public void testFullUpdateNonExistent_ReturnsNotFound() throws Exception {
        PetDTO pet = buildPet("16", "Ghost", "Unknown", null, 0, "available");

        mockMvc.perform(put("/api/pets/16")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(pet)))
                .andExpect(status().isNotFound());
    }

    // -----------------------------------------------------------------------
    // TC-017: Partial update (PATCH) name
    // -----------------------------------------------------------------------
    @Test
    public void testPartialUpdateName() throws Exception {
        createPetViaApi(buildPet("17", "OldName", "Cat", "Tabby", 2, "available"));

        mockMvc.perform(patch("/api/pets/17")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"name\":\"NewName\"}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.name", is("NewName")))
                .andExpect(jsonPath("$.species", is("Cat")));
    }

    // -----------------------------------------------------------------------
    // TC-018: Partial update non-existent pet returns 404
    // -----------------------------------------------------------------------
    @Test
    public void testPartialUpdateNonExistent_ReturnsNotFound() throws Exception {
        mockMvc.perform(patch("/api/pets/18")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"name\":\"Ghost\"}"))
                .andExpect(status().isNotFound());
    }

    // -----------------------------------------------------------------------
    // TC-019: Delete a pet
    // -----------------------------------------------------------------------
    @Test
    public void testDeletePet() throws Exception {
        createPetViaApi(buildPet("19", "ToDelete", "Dog", null, 1, "available"));

        mockMvc.perform(delete("/api/pets/19"))
                .andExpect(status().isOk());

        mockMvc.perform(get("/api/pets/19")
                        .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isNotFound());
    }

    // -----------------------------------------------------------------------
    // TC-020: Delete non-existent pet returns 404
    // -----------------------------------------------------------------------
    @Test
    public void testDeleteNonExistent_ReturnsNotFound() throws Exception {
        mockMvc.perform(delete("/api/pets/99999"))
                .andExpect(status().isNotFound());
    }

    // -----------------------------------------------------------------------
    // TC-021: Delete already-deleted pet returns 404
    // -----------------------------------------------------------------------
    @Test
    public void testDeleteAlreadyDeleted_ReturnsNotFound() throws Exception {
        createPetViaApi(buildPet("21", "DoubleDel", "Fish", null, 1, "available"));

        mockMvc.perform(delete("/api/pets/21"))
                .andExpect(status().isOk());

        mockMvc.perform(delete("/api/pets/21"))
                .andExpect(status().isNotFound());
    }

    // -----------------------------------------------------------------------
    // TC-022: Idempotent GET returns same result
    // -----------------------------------------------------------------------
    @Test
    public void testIdempotentGet() throws Exception {
        createPetViaApi(buildPet("22", "Stable", "Dog", null, 2, "available"));

        for (int i = 0; i < 3; i++) {
            mockMvc.perform(get("/api/pets/22")
                            .accept(MediaType.APPLICATION_JSON))
                    .andExpect(status().isOk())
                    .andExpect(jsonPath("$.name", is("Stable")));
        }
    }

    // -----------------------------------------------------------------------
    // TC-023: Full CRUD lifecycle
    // -----------------------------------------------------------------------
    @Test
    public void testFullCrudLifecycle() throws Exception {
        PetDTO pet = buildPet("23", "Lifecycle", "Cat", "Tabby", 3, "available");
        pet.setTags(Collections.singletonList("test"));

        // Create
        mockMvc.perform(post("/api/pets")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(pet)))
                .andExpect(status().isCreated());

        // Read
        mockMvc.perform(get("/api/pets/23").accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.name", is("Lifecycle")));

        // Update
        PetDTO updated = buildPet("23", "Updated", "Cat", "Tabby", 4, "sold");
        mockMvc.perform(put("/api/pets/23")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(updated)))
                .andExpect(status().isOk());

        // Patch
        mockMvc.perform(patch("/api/pets/23")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"status\":\"available\"}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status", is("available")));

        // Delete
        mockMvc.perform(delete("/api/pets/23"))
                .andExpect(status().isOk());

        // Verify deleted
        mockMvc.perform(get("/api/pets/23").accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isNotFound());
    }

    // -----------------------------------------------------------------------
    // TC-024: Re-create after deletion
    // -----------------------------------------------------------------------
    @Test
    public void testReCreateAfterDeletion() throws Exception {
        PetDTO pet = buildPet("24", "Phoenix", "Bird", null, 1, "available");
        createPetViaApi(pet);

        mockMvc.perform(delete("/api/pets/24")).andExpect(status().isOk());

        pet.setName("Phoenix Reborn");
        mockMvc.perform(post("/api/pets")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(pet)))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.name", is("Phoenix Reborn")));
    }

    // -----------------------------------------------------------------------
    // TC-025: Last-write-wins on sequential updates
    // -----------------------------------------------------------------------
    @Test
    public void testLastWriteWins() throws Exception {
        createPetViaApi(buildPet("25", "Racer", "Horse", null, 5, "available"));

        PetDTO v1 = buildPet("25", "Racer", "Horse", null, 5, "sold");
        mockMvc.perform(put("/api/pets/25")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(v1)))
                .andExpect(status().isOk());

        PetDTO v2 = buildPet("25", "Racer", "Horse", null, 5, "pending");
        mockMvc.perform(put("/api/pets/25")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(v2)))
                .andExpect(status().isOk());

        mockMvc.perform(get("/api/pets/25").accept(MediaType.APPLICATION_JSON))
                .andExpect(jsonPath("$.status", is("pending")));
    }

    // -----------------------------------------------------------------------
    // TC-026: Boundary - age zero
    // -----------------------------------------------------------------------
    @Test
    public void testBoundaryAgeZero() throws Exception {
        PetDTO pet = buildPet("26", "Newborn", "Hamster", null, 0, "available");

        mockMvc.perform(post("/api/pets")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(pet)))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.age", is(0)));
    }

    // -----------------------------------------------------------------------
    // TC-027: Boundary - single character name
    // -----------------------------------------------------------------------
    @Test
    public void testBoundarySingleCharName() throws Exception {
        PetDTO pet = buildPet("27", "X", "Fish", null, 1, "available");

        mockMvc.perform(post("/api/pets")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(pet)))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.name", is("X")));
    }

    // -----------------------------------------------------------------------
    // TC-028: Boundary - empty tags list
    // -----------------------------------------------------------------------
    @Test
    public void testBoundaryEmptyTags() throws Exception {
        PetDTO pet = buildPet("28", "NoTags", "Bird", null, 2, "available");
        pet.setTags(Collections.emptyList());

        mockMvc.perform(post("/api/pets")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(pet)))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.tags", hasSize(0)));
    }

    // -----------------------------------------------------------------------
    // TC-029: Response Content-Type header is application/json
    // -----------------------------------------------------------------------
    @Test
    public void testResponseContentType() throws Exception {
        createPetViaApi(buildPet("29", "HeaderPet", "Dog", null, 1, "available"));

        mockMvc.perform(get("/api/pets/29").accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(header().string("Content-Type", containsString("application/json")));
    }

    // -----------------------------------------------------------------------
    // TC-030: Pagination headers present
    // -----------------------------------------------------------------------
    @Test
    public void testPaginationHeaders() throws Exception {
        createPetViaApi(buildPet("30", "PagPet", "Dog", null, 1, "available"));

        mockMvc.perform(get("/api/pets").accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(header().exists("X-Total-Count"))
                .andExpect(header().exists("X-Page"))
                .andExpect(header().exists("X-Page-Size"));
    }
}
