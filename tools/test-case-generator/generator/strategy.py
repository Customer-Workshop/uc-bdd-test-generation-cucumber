"""Test strategy engine.

Generates test scenarios for each endpoint based on HTTP method,
parameters, request body schema, and response codes. Produces
structured test case data ready for Gherkin rendering.
"""

import json
from typing import Any

from .parser import EndpointInfo, OpenAPIParser

SAMPLE_VALUES: dict[str, Any] = {
    "string": "test-value",
    "integer": 42,
    "number": 3.14,
    "boolean": True,
    "array": [],
    "object": {},
}

INVALID_VALUES: dict[str, list[Any]] = {
    "string": ["", None, 12345],
    "integer": [None, "not-a-number", 999999999],
    "number": [None, "not-a-number"],
    "boolean": [None, "not-a-boolean"],
}


class TestScenario:
    """A single test scenario with steps."""

    def __init__(
        self,
        name: str,
        description: str,
        steps: list[dict[str, str]],
        tags: list[str],
    ):
        self.name = name
        self.description = description
        self.steps = steps
        self.tags = tags


class TestFeature:
    """A collection of test scenarios for a feature."""

    def __init__(
        self,
        name: str,
        description: str,
        background_steps: list[dict[str, str]],
        scenarios: list[TestScenario],
        tags: list[str],
    ):
        self.name = name
        self.description = description
        self.background_steps = background_steps
        self.scenarios = scenarios
        self.tags = tags


class TestStrategyEngine:
    """Generates test scenarios from parsed API endpoints."""

    def __init__(self, parser: OpenAPIParser):
        self.parser = parser

    def generate_features(self) -> list[TestFeature]:
        endpoints = self.parser.get_endpoints()
        grouped = self._group_by_tag(endpoints)

        features = []
        for tag, endpoints_in_tag in grouped.items():
            feature = self._build_feature(tag, endpoints_in_tag)
            features.append(feature)

        return features

    def _group_by_tag(
        self, endpoints: list[EndpointInfo]
    ) -> dict[str, list[EndpointInfo]]:
        grouped: dict[str, list[EndpointInfo]] = {}
        for endpoint in endpoints:
            tag = endpoint.tags[0] if endpoint.tags else "default"
            tag = tag.lower().replace(" ", "-")
            grouped.setdefault(tag, []).append(endpoint)
        return grouped

    def _build_feature(
        self, tag: str, endpoints: list[EndpointInfo]
    ) -> TestFeature:
        api_title = self.parser.get_title()
        base_path = self.parser.base_path or "/api"

        background_steps = [
            {"keyword": "Given", "text": f"http baseUri is {base_path}"},
            {
                "keyword": "And",
                "text": 'I set http headers to:\n      | Accept       | application/json |\n      | Content-Type | application/json |',
            },
        ]

        scenarios = []
        for endpoint in endpoints:
            scenarios.extend(self._generate_scenarios(endpoint))

        return TestFeature(
            name=f"{api_title} - {tag.replace('-', ' ').title()} API tests",
            description=f"Auto-generated BDD tests for {tag} endpoints",
            background_steps=background_steps,
            scenarios=scenarios,
            tags=[f"@{tag}", "@auto-generated"],
        )

    def _generate_scenarios(
        self, endpoint: EndpointInfo
    ) -> list[TestScenario]:
        scenarios = []

        scenarios.append(self._happy_path_scenario(endpoint))

        if endpoint.requires_auth():
            scenarios.append(self._unauthorized_scenario(endpoint))

        if endpoint.has_path_params():
            scenarios.append(self._not_found_scenario(endpoint))

        if endpoint.has_request_body():
            scenarios.append(self._invalid_body_scenario(endpoint))
            scenarios.append(self._empty_body_scenario(endpoint))

        if endpoint.has_query_params():
            scenarios.append(self._missing_query_params_scenario(endpoint))

        if endpoint.method in ("POST", "PUT"):
            schema = self.parser.get_request_body_schema(endpoint)
            if schema:
                scenarios.append(self._boundary_values_scenario(endpoint, schema))

        return scenarios

    def _happy_path_scenario(self, endpoint: EndpointInfo) -> TestScenario:
        steps = []
        path = self._build_path_with_samples(endpoint)
        success_codes = endpoint.get_success_codes()
        expected_code = success_codes[0] if success_codes else "200"

        if endpoint.requires_auth():
            steps.append(
                {"keyword": "When", "text": "I authenticate with login/password testuser/testpass"}
            )

        if endpoint.has_request_body():
            body = self._generate_sample_body(endpoint)
            steps.append(
                {"keyword": "And" if steps else "When", "text": f"I set http body to {body}"}
            )

        keyword = "And" if steps else "When"
        steps.append({"keyword": keyword, "text": f"I {endpoint.method} {path}"})
        steps.append(
            {"keyword": "Then", "text": f"http response code should be {expected_code}"}
        )
        steps.append(
            {"keyword": "And", "text": "http response body should be valid json"}
        )

        response_schema = self.parser.get_response_schema(endpoint, expected_code)
        if response_schema and response_schema.get("properties"):
            for prop in list(response_schema["properties"].keys())[:5]:
                steps.append(
                    {"keyword": "And", "text": f"http response body path $.{prop} should exist"}
                )

        summary = endpoint.summary or f"{endpoint.method} {endpoint.path}"
        return TestScenario(
            name=f"Happy path - {summary}",
            description=f"Verify {endpoint.method} {endpoint.path} returns {expected_code}",
            steps=steps,
            tags=[f"@{endpoint.method.lower()}", "@happy-path"],
        )

    def _unauthorized_scenario(self, endpoint: EndpointInfo) -> TestScenario:
        path = self._build_path_with_samples(endpoint)
        steps = [
            {"keyword": "When", "text": f"I {endpoint.method} {path}"},
            {"keyword": "Then", "text": "http response code should be 401"},
        ]
        summary = endpoint.summary or f"{endpoint.method} {endpoint.path}"
        return TestScenario(
            name=f"Unauthorized access - {summary}",
            description=f"Verify {endpoint.method} {endpoint.path} returns 401 without auth",
            steps=steps,
            tags=[f"@{endpoint.method.lower()}", "@security"],
        )

    def _not_found_scenario(self, endpoint: EndpointInfo) -> TestScenario:
        path = endpoint.path
        for param in endpoint.parameters:
            if param.get("in") == "path":
                path = path.replace(f"{{{param['name']}}}", "999999")

        steps = []
        if endpoint.requires_auth():
            steps.append(
                {"keyword": "When", "text": "I authenticate with login/password testuser/testpass"}
            )

        keyword = "And" if steps else "When"
        steps.append({"keyword": keyword, "text": f"I {endpoint.method} {path}"})
        steps.append({"keyword": "Then", "text": "http response code should be 404"})

        summary = endpoint.summary or f"{endpoint.method} {endpoint.path}"
        return TestScenario(
            name=f"Not found - {summary}",
            description=f"Verify {endpoint.method} {endpoint.path} returns 404 for non-existent resource",
            steps=steps,
            tags=[f"@{endpoint.method.lower()}", "@negative"],
        )

    def _invalid_body_scenario(self, endpoint: EndpointInfo) -> TestScenario:
        steps = []
        if endpoint.requires_auth():
            steps.append(
                {"keyword": "When", "text": "I authenticate with login/password testuser/testpass"}
            )

        steps.append(
            {"keyword": "And" if steps else "When", "text": 'I set http body to {"invalid": "data"}'}
        )

        path = self._build_path_with_samples(endpoint)
        steps.append({"keyword": "And", "text": f"I {endpoint.method} {path}"})
        steps.append(
            {"keyword": "Then", "text": "http response code should not be 200"}
        )

        summary = endpoint.summary or f"{endpoint.method} {endpoint.path}"
        return TestScenario(
            name=f"Invalid request body - {summary}",
            description=f"Verify {endpoint.method} {endpoint.path} rejects invalid body",
            steps=steps,
            tags=[f"@{endpoint.method.lower()}", "@negative", "@validation"],
        )

    def _empty_body_scenario(self, endpoint: EndpointInfo) -> TestScenario:
        steps = []
        if endpoint.requires_auth():
            steps.append(
                {"keyword": "When", "text": "I authenticate with login/password testuser/testpass"}
            )

        steps.append(
            {"keyword": "And" if steps else "When", "text": "I set http body to {}"}
        )

        path = self._build_path_with_samples(endpoint)
        steps.append({"keyword": "And", "text": f"I {endpoint.method} {path}"})
        steps.append(
            {"keyword": "Then", "text": "http response code should not be 200"}
        )

        summary = endpoint.summary or f"{endpoint.method} {endpoint.path}"
        return TestScenario(
            name=f"Empty request body - {summary}",
            description=f"Verify {endpoint.method} {endpoint.path} rejects empty body",
            steps=steps,
            tags=[f"@{endpoint.method.lower()}", "@negative", "@validation"],
        )

    def _missing_query_params_scenario(
        self, endpoint: EndpointInfo
    ) -> TestScenario:
        path = self._build_path_with_samples(endpoint)
        steps = []
        if endpoint.requires_auth():
            steps.append(
                {"keyword": "When", "text": "I authenticate with login/password testuser/testpass"}
            )

        keyword = "And" if steps else "When"
        steps.append({"keyword": keyword, "text": f"I {endpoint.method} {path}"})
        steps.append(
            {"keyword": "Then", "text": "http response code should be 400"}
        )

        summary = endpoint.summary or f"{endpoint.method} {endpoint.path}"
        return TestScenario(
            name=f"Missing query parameters - {summary}",
            description=f"Verify {endpoint.method} {endpoint.path} returns 400 without required query params",
            steps=steps,
            tags=[f"@{endpoint.method.lower()}", "@negative"],
        )

    def _boundary_values_scenario(
        self, endpoint: EndpointInfo, schema: dict[str, Any]
    ) -> TestScenario:
        steps = []
        if endpoint.requires_auth():
            steps.append(
                {"keyword": "When", "text": "I authenticate with login/password testuser/testpass"}
            )

        body = self._generate_boundary_body(schema)
        steps.append(
            {"keyword": "And" if steps else "When", "text": f"I set http body to {body}"}
        )

        path = self._build_path_with_samples(endpoint)
        steps.append({"keyword": "And", "text": f"I {endpoint.method} {path}"})

        success_codes = endpoint.get_success_codes()
        expected_code = success_codes[0] if success_codes else "200"
        steps.append(
            {"keyword": "Then", "text": f"http response code should not be {expected_code}"}
        )

        summary = endpoint.summary or f"{endpoint.method} {endpoint.path}"
        return TestScenario(
            name=f"Boundary values - {summary}",
            description=f"Verify {endpoint.method} {endpoint.path} handles boundary input values",
            steps=steps,
            tags=[f"@{endpoint.method.lower()}", "@boundary"],
        )

    def _build_path_with_samples(self, endpoint: EndpointInfo) -> str:
        path = endpoint.path
        for param in endpoint.parameters:
            if param.get("in") == "path":
                sample = self._sample_value_for_param(param)
                path = path.replace(f"{{{param['name']}}}", str(sample))
        return path

    def _generate_sample_body(self, endpoint: EndpointInfo) -> str:
        schema = self.parser.get_request_body_schema(endpoint)
        if not schema:
            return "{}"
        body = self._generate_sample_from_schema(schema)
        return json.dumps(body, separators=(",", ":"))

    def _generate_sample_from_schema(
        self, schema: dict[str, Any]
    ) -> Any:
        schema_type = schema.get("type", "object")
        if schema_type == "object":
            obj = {}
            for prop_name, prop_schema in schema.get("properties", {}).items():
                obj[prop_name] = self._generate_sample_from_schema(prop_schema)
            return obj
        if schema_type == "array":
            items = schema.get("items", {})
            return [self._generate_sample_from_schema(items)]
        if "enum" in schema:
            return schema["enum"][0]
        if "example" in schema:
            return schema["example"]
        return SAMPLE_VALUES.get(schema_type, "test")

    def _generate_boundary_body(self, schema: dict[str, Any]) -> str:
        body = {}
        for prop_name, prop_schema in schema.get("properties", {}).items():
            prop_type = prop_schema.get("type", "string")
            if prop_type == "string":
                body[prop_name] = "x" * 10000
            elif prop_type == "integer":
                body[prop_name] = -999999999
            elif prop_type == "number":
                body[prop_name] = -999999.999
            elif prop_type == "boolean":
                body[prop_name] = True
            elif prop_type == "array":
                body[prop_name] = []
            else:
                body[prop_name] = None
        return json.dumps(body, separators=(",", ":"))

    def _sample_value_for_param(self, param: dict[str, Any]) -> Any:
        if "example" in param:
            return param["example"]
        schema = param.get("schema", {})
        param_type = schema.get("type", param.get("type", "string"))
        if "enum" in schema:
            return schema["enum"][0]
        return SAMPLE_VALUES.get(param_type, "test-value")
