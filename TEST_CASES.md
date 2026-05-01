# Petstore API — Comprehensive Test Case Document

This document provides a full catalog of test cases covering the Petstore REST API endpoints.
Each case includes an ID, title, preconditions, detailed steps, expected results, priority, and traceability to the API endpoint under test.

---

## 1. Conventions

| Priority | Meaning |
|----------|---------|
| **P1 — Critical** | Must-pass for every release; blocks deployment if failing |
| **P2 — High** | Core happy-path and important negative cases |
| **P3 — Medium** | Boundary, edge-case, and pagination scenarios |
| **P4 — Low** | Exploratory, performance, and cosmetic checks |

---

## 2. Functional Test Cases

### 2.1 Create Pet — `POST /api/pets`

| TC ID | Title | Preconditions | Steps | Expected Result | Priority |
|-------|-------|--------------|-------|-----------------|----------|
| TC-001 | Create a pet with all fields | None | 1. POST `/api/pets` with body `{"id":"1","name":"Max","species":"Dog","breed":"Labrador","age":5,"status":"available","tags":["friendly"]}` | 201 Created; body contains all fields as sent | P1 |
| TC-002 | Create a pet with minimal required fields | None | 1. POST `/api/pets` with body `{"id":"2","name":"Whiskers","species":"Cat","age":2}` | 201 Created; `status` defaults to `available` | P1 |
| TC-003 | Create a pet from JSON fixture file | Fixture `golden-retriever.pet.json` exists | 1. POST `/api/pets` with fixture body | 201 Created; fields match fixture | P2 |
| TC-004 | Reject creation without a name | None | 1. POST `/api/pets` with body missing `name` | 400 Bad Request | P1 |
| TC-005 | Reject creation without a species | None | 1. POST `/api/pets` with body missing `species` | 400 Bad Request | P1 |
| TC-006 | Reject creation with empty name | None | 1. POST with `"name":""` | 400 Bad Request | P2 |
| TC-007 | Reject creation with blank species | None | 1. POST with `"species":"  "` | 400 Bad Request | P2 |
| TC-008 | Reject duplicate pet ID | Pet with id `200` exists | 1. POST `/api/pets` with same `id` | 409 Conflict | P1 |

### 2.2 Read Pet — `GET /api/pets/{id}`

| TC ID | Title | Preconditions | Steps | Expected Result | Priority |
|-------|-------|--------------|-------|-----------------|----------|
| TC-009 | Get pet by ID | Pet `1` exists | 1. GET `/api/pets/1` | 200 OK; body matches stored pet | P1 |
| TC-010 | Get non-existent pet | No pet `99999` | 1. GET `/api/pets/99999` | 404 Not Found | P1 |
| TC-011 | Get with alphanumeric ID | No pet `abc-123` | 1. GET `/api/pets/abc-123-xyz` | 404 Not Found | P3 |
| TC-012 | Multiple GETs return same result | Pet `22` exists | 1. GET `/api/pets/22` three times | All responses identical (idempotency) | P2 |

### 2.3 List Pets — `GET /api/pets`

| TC ID | Title | Preconditions | Steps | Expected Result | Priority |
|-------|-------|--------------|-------|-----------------|----------|
| TC-013 | List all pets | 3 pets exist | 1. GET `/api/pets` | 200 OK; array length 3 | P1 |
| TC-014 | List pets when empty | No pets | 1. GET `/api/pets` | 200 OK; empty array | P2 |
| TC-015 | Filter by status | Pets with varying statuses | 1. GET `/api/pets?status=available` | Only `available` pets returned | P1 |
| TC-016 | Filter by species | Pets with varying species | 1. GET `/api/pets?species=Cat` | Only cats returned | P2 |
| TC-017 | Filter with non-matching status | Pets exist | 1. GET `/api/pets?status=nonexistent` | 200 OK; empty array | P2 |
| TC-018 | Pagination — first page | 7 pets exist | 1. GET `/api/pets?page=0&size=2` | Exactly 2 results | P2 |
| TC-019 | Pagination — beyond data | 1 pet exists | 1. GET `/api/pets?page=100&size=10` | 200 OK; empty array | P3 |
| TC-020 | Pagination — page size 1 | Pets exist | 1. GET `/api/pets?page=0&size=1` | Exactly 1 result | P3 |
| TC-021 | Pagination headers present | Pets exist | 1. GET `/api/pets` | `X-Total-Count`, `X-Page`, `X-Page-Size` headers present | P2 |

### 2.4 Update Pet — `PUT /api/pets/{id}`

| TC ID | Title | Preconditions | Steps | Expected Result | Priority |
|-------|-------|--------------|-------|-----------------|----------|
| TC-022 | Full update of existing pet | Pet `1` exists | 1. PUT `/api/pets/1` with updated body | 200 OK; fields updated; GET confirms | P1 |
| TC-023 | Update non-existent pet | No pet `99999` | 1. PUT `/api/pets/99999` | 404 Not Found | P1 |
| TC-024 | Last-write-wins on sequential updates | Pet `501` exists | 1. PUT status=sold, 2. PUT status=pending | Final GET shows `pending` | P2 |

### 2.5 Partial Update — `PATCH /api/pets/{id}`

| TC ID | Title | Preconditions | Steps | Expected Result | Priority |
|-------|-------|--------------|-------|-----------------|----------|
| TC-025 | Patch pet name | Pet `1` exists | 1. PATCH `/api/pets/1` `{"name":"Maxwell"}` | 200 OK; name updated, species unchanged | P1 |
| TC-026 | Patch pet status | Pet `1` exists | 1. PATCH `/api/pets/1` `{"status":"pending"}` | 200 OK; status updated | P2 |
| TC-027 | Patch non-existent pet | No pet `99999` | 1. PATCH `/api/pets/99999` | 404 Not Found | P1 |

### 2.6 Delete Pet — `DELETE /api/pets/{id}`

| TC ID | Title | Preconditions | Steps | Expected Result | Priority |
|-------|-------|--------------|-------|-----------------|----------|
| TC-028 | Delete existing pet | Pet `2` exists | 1. DELETE `/api/pets/2` 2. GET `/api/pets/2` | 200 OK; subsequent GET returns 404 | P1 |
| TC-029 | Delete non-existent pet | No pet `99999` | 1. DELETE `/api/pets/99999` | 404 Not Found | P1 |
| TC-030 | Delete already-deleted pet | Pet `500` deleted | 1. DELETE `/api/pets/500` twice | Second DELETE returns 404 | P2 |

### 2.7 Integration / Lifecycle

| TC ID | Title | Preconditions | Steps | Expected Result | Priority |
|-------|-------|--------------|-------|-----------------|----------|
| TC-031 | Full CRUD lifecycle | None | 1. Create, 2. Read, 3. Update, 4. Patch, 5. Delete, 6. Verify 404 | Each step succeeds | P1 |
| TC-032 | Re-create pet after deletion | Pet `503` deleted | 1. Create, 2. Delete, 3. Re-create with same ID | Re-creation returns 201 | P2 |

---

## 3. Boundary Test Cases

| TC ID | Title | Preconditions | Steps | Expected Result | Priority |
|-------|-------|--------------|-------|-----------------|----------|
| TC-033 | Age zero (newborn) | None | POST with `age: 0` | 201 Created; age=0 | P3 |
| TC-034 | Large age value | None | POST with `age: 150` | 201 Created; age=150 | P3 |
| TC-035 | Single-character name | None | POST with `name: "X"` | 201 Created | P3 |
| TC-036 | Very long name (100+ chars) | None | POST with 100+ char name | 201 Created | P3 |
| TC-037 | Special characters in name | None | POST `name: "Mr. Whiskers III"` | 201 Created | P3 |
| TC-038 | Empty tags list | None | POST with `tags: []` | 201 Created; tags is empty array | P3 |
| TC-039 | Many tags (10) | None | POST with 10 tags | 201 Created; tags length 10 | P3 |

---

## 4. Security Test Cases

| TC ID | Title | Preconditions | Steps | Expected Result | Priority |
|-------|-------|--------------|-------|-----------------|----------|
| TC-040 | SQL injection in pet name | None | POST `name: "'; DROP TABLE pets;--"` | 201 or 400; no data corruption | P2 |
| TC-041 | XSS in pet name | None | POST `name: "<script>alert(1)</script>"` | Stored literally or rejected; no script execution | P2 |
| TC-042 | Script in query parameter | None | GET `/api/pets?status=<script>` | 200 OK; empty results; no injection | P3 |
| TC-043 | Response does not leak server internals | None | GET `/api/pets/99999` | 404 with no stack trace or internal paths | P2 |

---

## 5. Performance / Load Test Cases (Manual / Tool-Assisted)

| TC ID | Title | Preconditions | Steps | Expected Result | Priority |
|-------|-------|--------------|-------|-----------------|----------|
| TC-044 | Response time for single GET | Pet exists | 1. GET `/api/pets/1` | Response < 200ms | P4 |
| TC-045 | Response time for list with 100 pets | 100 pets in store | 1. GET `/api/pets` | Response < 500ms | P4 |
| TC-046 | Concurrent creation of 50 pets | None | 1. 50 parallel POSTs with unique IDs | All return 201; no data loss | P4 |

---

## 6. Traceability Matrix

| API Endpoint | Method | Test Case IDs |
|-------------|--------|---------------|
| `/api/pets` | POST | TC-001, TC-002, TC-003, TC-004, TC-005, TC-006, TC-007, TC-008, TC-033–TC-039, TC-040, TC-041 |
| `/api/pets/{id}` | GET | TC-009, TC-010, TC-011, TC-012, TC-043 |
| `/api/pets` | GET | TC-013, TC-014, TC-015, TC-016, TC-017, TC-018, TC-019, TC-020, TC-021, TC-042, TC-044, TC-045 |
| `/api/pets/{id}` | PUT | TC-022, TC-023, TC-024 |
| `/api/pets/{id}` | PATCH | TC-025, TC-026, TC-027 |
| `/api/pets/{id}` | DELETE | TC-028, TC-029, TC-030 |
| Multi-endpoint | CRUD Lifecycle | TC-031, TC-032, TC-046 |

---

## 7. Test Data Requirements

| Data Set | Description | Location |
|----------|-------------|----------|
| `golden-retriever.pet.json` | Fixture for "Create from file" tests | `src/test/resources/fixtures/` |
| In-memory `PetController.pets` | Static list cleared via `@After` hooks | Test lifecycle managed |
| Scenario Outline Examples | Inline data tables in feature files | `src/test/resources/features/petstore-data-driven.feature` |
