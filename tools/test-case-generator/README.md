# Test Case Generator Agent

An automation agent that reads **OpenAPI/Swagger** specifications and generates **Gherkin BDD test cases** (`.feature` files) compatible with the Spring Cucumber REST API framework.

## Features

- Parses OpenAPI 3.x and Swagger 2.x specifications (JSON and YAML)
- Generates comprehensive test scenarios including:
  - **Happy path** tests for each endpoint
  - **Authentication** tests (401 Unauthorized)
  - **Not found** tests (404 for path parameters)
  - **Invalid request body** tests (malformed JSON)
  - **Empty request body** tests
  - **Missing query parameter** tests
  - **Boundary value** tests (extreme values for POST/PUT)
- Groups tests by API tag into separate feature files
- Output is fully compatible with the Spring Cucumber REST API BDD framework

## Installation

```bash
cd tools/test-case-generator
pip install -r requirements.txt
```

## Usage

### Basic Usage

```bash
python -m generator sample_specs/petstore.json -o generated-tests
```

### Dry Run (preview without writing files)

```bash
python -m generator sample_specs/petstore.json --dry-run
```

### Filter by Tag

```bash
python -m generator sample_specs/petstore.json --tag-filter pets
```

### Verbose Output

```bash
python -m generator sample_specs/petstore.json -v -o generated-tests
```

## Options

| Option | Description |
|---|---|
| `SPEC_PATH` | Path to the OpenAPI/Swagger spec file (JSON or YAML) |
| `-o, --output` | Output directory for generated `.feature` files (default: `generated-tests`) |
| `--dry-run` | Print generated features to stdout without writing files |
| `--tag-filter` | Only generate tests for endpoints with this tag |
| `-v, --verbose` | Enable verbose output |

## Architecture

```
generator/
├── parser.py         # OpenAPI/Swagger spec parser
├── strategy.py       # Test strategy engine (scenario generation)
├── gherkin_writer.py # Gherkin .feature file renderer
└── cli.py            # CLI entry point
```

### Parser (`parser.py`)
Reads and normalizes OpenAPI 3.x and Swagger 2.x specs. Extracts endpoint metadata including paths, methods, parameters, request bodies, response schemas, and security requirements. Resolves `$ref` references.

### Strategy Engine (`strategy.py`)
Applies test generation strategies to each endpoint based on its characteristics (HTTP method, parameters, auth requirements, schemas). Produces structured `TestScenario` and `TestFeature` objects.

### Gherkin Writer (`gherkin_writer.py`)
Renders `TestFeature` objects into properly formatted `.feature` files using the step definition syntax from the Spring Cucumber REST API framework.

## Example Output

Given a Petstore API spec, the generator produces feature files like:

```gherkin
@pets @auto-generated
Feature: Petstore API - Pets API tests
  Auto-generated BDD tests for pets endpoints

  Background:
    Given http baseUri is /api
    And I set http headers to:
      | Accept       | application/json |
      | Content-Type | application/json |

  @get @happy-path
  Scenario: Happy path - List all pets
    When I authenticate with login/password testuser/testpass
    And I GET /pets
    Then http response code should be 200
    And http response body should be valid json

  @get @security
  Scenario: Unauthorized access - List all pets
    When I GET /pets
    Then http response code should be 401
```
