# Petstore API — Test Coverage Report

## 1. Executive Summary

This report summarizes the test coverage generated for the Petstore REST API.
Tests are organized into BDD (Cucumber/Gherkin) scenarios and traditional JUnit test classes,
covering positive, negative, boundary, exception, data-driven, security, and performance dimensions.

---

## 2. Scenario Count by Type

| Category | BDD Scenarios | JUnit Tests | Total |
|----------|:------------:|:-----------:|:-----:|
| **Positive (CRUD)** | 16 | 10 | 26 |
| **Negative** | 10 | 6 | 16 |
| **Boundary** | 10 | 4 | 14 |
| **Exception / Edge-Case** | 7 | 4 | 11 |
| **Data-Driven (Outline)** | 16 (via Examples) | — | 16 |
| **Security** | — | — | 4 (documented) |
| **Performance** | — | — | 3 (documented) |
| **Totals** | **59** | **30** | **90** |

> BDD scenario count includes individual rows from Scenario Outline Examples tables.

---

## 3. API Endpoint Coverage Matrix

| Endpoint | POST | GET (single) | GET (list) | PUT | PATCH | DELETE |
|----------|:----:|:------------:|:----------:|:---:|:-----:|:------:|
| **Positive** | 3 | 3 | 5 | 1 | 2 | 2 |
| **Negative** | 4 | 2 | 2 | 1 | 1 | 2 |
| **Boundary** | 5 | — | 3 | — | — | — |
| **Exception** | 2 | 2 | — | 1 | — | 2 |
| **Data-Driven** | 6 | 6 | — | — | 3 | — |
| **Coverage** | **Full** | **Full** | **Full** | **Full** | **Full** | **Full** |

All six REST operations are covered across multiple scenario types.

---

## 4. Feature Files Inventory

| File | Focus | Scenario Count |
|------|-------|:--------------:|
| `petstore-crud.feature` | Happy-path CRUD, filters, pagination headers | 16 |
| `petstore-negative.feature` | Invalid inputs, not-found, duplicates | 10 |
| `petstore-boundary.feature` | Edge values for age, name, tags, pagination | 10 |
| `petstore-data-driven.feature` | Scenario Outlines with Examples tables | 16 |
| `petstore-exception.feature` | Double-delete, lifecycle, idempotency, re-creation | 7 |

---

## 5. JUnit Test Class

| Class | Location | Test Count |
|-------|----------|:----------:|
| `PetControllerTest` | `src/test/java/.../pet/PetControllerTest.java` | 30 |

Uses `MockMvc` for direct controller testing without Cucumber overhead.

---

## 6. Test Artifacts Created

| Artifact | Path |
|----------|------|
| Pet model DTOs | `src/test/java/.../pet/PetDTO.java`, `PartialPetDTO.java` |
| Pet REST controller | `src/test/java/.../pet/PetController.java` |
| BDD step definition | `src/test/java/.../glue/PetStoreStepDefinition.java` |
| JSON fixture | `src/test/resources/fixtures/golden-retriever.pet.json` |
| Feature files (5) | `src/test/resources/features/petstore-*.feature` |
| JUnit test class | `src/test/java/.../pet/PetControllerTest.java` |
| Test case document | `TEST_CASES.md` |
| This coverage report | `TEST_COVERAGE_REPORT.md` |

---

## 7. Recommendations for Additional Test Scenarios

### 7.1 High Priority
1. **Authentication & Authorization** — Add `@authenticated` scenarios that require `Basic Auth` headers (mirroring the existing `users.feature` auth pattern). Test `401 Unauthorized` and `403 Forbidden` responses.
2. **Input Validation Constraints** — Add server-side `@Valid` annotations with `@Size`, `@Min`, `@Max` on `PetDTO` fields, then write BDD scenarios that verify 400 responses for out-of-range values.
3. **Concurrency Testing** — Use JMeter, Gatling, or k6 to run parallel create/update requests and verify thread safety of the in-memory store.

### 7.2 Medium Priority
4. **Bulk Import (CSV/Multipart)** — Following the existing `users-import.feature` pattern, add a CSV import endpoint for pets and corresponding BDD scenarios.
5. **Sorting** — Add `?sort=name,asc` query parameter support and test ascending/descending ordering.
6. **Content Negotiation** — Test `Accept: application/xml` returns 406 Not Acceptable.
7. **HATEOAS / Links** — If the API adds hypermedia links, verify `_links` presence in responses.

### 7.3 Low Priority
8. **Performance Baselines** — Establish response-time SLAs and automate with Gatling or JMH.
9. **Contract Testing** — Generate an OpenAPI spec and use `swagger-request-validator` to ensure responses conform.
10. **Database-backed Persistence** — When migrating from in-memory to JPA, add integration tests that verify transactional rollback, unique constraints, and cascade deletes.

---

## 8. How a Functional QA Can Review, Refine, and Regenerate Tests

### 8.1 Reviewing Existing Tests
1. **Read the feature files** in `src/test/resources/features/petstore-*.feature` — they are written in business-readable Gherkin (Given/When/Then).
2. **Cross-reference** each scenario with the `TEST_CASES.md` traceability matrix to confirm endpoint coverage.
3. **Run the suite locally** with `mvn test` and review the Cucumber HTML/JSON report.

### 8.2 Refining Scenarios
- **Add new Examples rows** to existing Scenario Outlines in `petstore-data-driven.feature` to increase data variety.
- **Tag scenarios** with business-meaningful tags (e.g., `@smoke`, `@regression`, `@sprint-12`) for selective execution.
- **Modify expected values** in feature files without touching Java code — the existing step definitions are generic.

### 8.3 Regenerating / Extending Tests
1. **Copy a feature file** and change the endpoint/body to target a new resource (e.g., Orders, Customers).
2. **Create a new model DTO** following the `PetDTO` pattern.
3. **Create a new controller** following the `PetController` pattern.
4. **Reuse step definitions** — `DefaultRestApiBddStepDefinition` handles all HTTP verbs and JSON path assertions generically.
5. **Add a cleanup hook** in a new step definition class (see `PetStoreStepDefinition.java`).

### 8.4 Running Specific Subsets
```bash
# Run all petstore tests
mvn test -Dcucumber.filter.tags="@petstore"

# Run only negative scenarios
mvn test -Dcucumber.filter.tags="@petstore and @negative"

# Run only boundary scenarios
mvn test -Dcucumber.filter.tags="@petstore and @boundary"

# Run only data-driven scenarios
mvn test -Dcucumber.filter.tags="@petstore and @data-driven"

# Run JUnit tests only (skip Cucumber)
mvn test -Dtest=PetControllerTest
```

---

## 9. Framework Architecture Reference

```
src/
├── main/java/.../glue/
│   ├── AbstractBddStepDefinition.java    ← Core HTTP + assertion engine
│   └── DefaultRestApiBddStepDefinition.java  ← Cucumber @Given/@When/@Then bindings
├── test/
│   ├── java/.../
│   │   ├── glue/
│   │   │   ├── DefaultRestApiStepDefinitionTest.java  ← Spring context + auth
│   │   │   └── PetStoreStepDefinition.java            ← Petstore lifecycle hooks
│   │   ├── pet/
│   │   │   ├── PetDTO.java / PartialPetDTO.java       ← Models
│   │   │   ├── PetController.java                      ← In-memory REST controller
│   │   │   └── PetControllerTest.java                  ← JUnit/MockMvc tests
│   │   └── RestApiCucumberTest.java                    ← Cucumber runner entry point
│   └── resources/
│       ├── features/
│       │   ├── petstore-crud.feature
│       │   ├── petstore-negative.feature
│       │   ├── petstore-boundary.feature
│       │   ├── petstore-data-driven.feature
│       │   └── petstore-exception.feature
│       └── fixtures/
│           └── golden-retriever.pet.json
```
