"""OpenAPI/Swagger specification parser.

Parses OpenAPI 3.x and Swagger 2.x specs to extract endpoint information
including paths, methods, parameters, request bodies, and response schemas.
"""

import json
from pathlib import Path
from typing import Any

import yaml


class EndpointInfo:
    """Represents a parsed REST API endpoint."""

    def __init__(
        self,
        path: str,
        method: str,
        operation_id: str,
        summary: str,
        description: str,
        parameters: list[dict[str, Any]],
        request_body: dict[str, Any] | None,
        responses: dict[str, dict[str, Any]],
        tags: list[str],
        security: list[dict[str, list[str]]],
    ):
        self.path = path
        self.method = method.upper()
        self.operation_id = operation_id
        self.summary = summary
        self.description = description
        self.parameters = parameters
        self.request_body = request_body
        self.responses = responses
        self.tags = tags
        self.security = security

    def has_path_params(self) -> bool:
        return any(p.get("in") == "path" for p in self.parameters)

    def has_query_params(self) -> bool:
        return any(p.get("in") == "query" for p in self.parameters)

    def has_request_body(self) -> bool:
        return self.request_body is not None

    def requires_auth(self) -> bool:
        return len(self.security) > 0

    def get_success_codes(self) -> list[str]:
        return [code for code in self.responses if code.startswith("2")]

    def get_error_codes(self) -> list[str]:
        return [code for code in self.responses if code.startswith(("4", "5"))]

    def __repr__(self) -> str:
        return f"EndpointInfo({self.method} {self.path})"


class OpenAPIParser:
    """Parses OpenAPI 3.x and Swagger 2.x specifications."""

    def __init__(self, spec_path: str | None = None, spec_content: str | None = None):
        if spec_path:
            self.spec = self._load_spec(spec_path)
        elif spec_content:
            self.spec = self._parse_content(spec_content)
        else:
            raise ValueError("Either spec_path or spec_content must be provided")

        self.version = self._detect_version()
        self.base_path = self._get_base_path()
        self.global_security = self.spec.get("security", [])

    def _load_spec(self, path: str) -> dict[str, Any]:
        file_path = Path(path)
        content = file_path.read_text(encoding="utf-8")
        return self._parse_content(content, file_path.suffix)

    def _parse_content(
        self, content: str, suffix: str = ".json"
    ) -> dict[str, Any]:
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return yaml.safe_load(content)

    def _detect_version(self) -> str:
        if "openapi" in self.spec:
            return self.spec["openapi"]
        if "swagger" in self.spec:
            return self.spec["swagger"]
        raise ValueError("Cannot detect API specification version")

    def _get_base_path(self) -> str:
        if self.version.startswith("3"):
            servers = self.spec.get("servers", [])
            if servers:
                url = servers[0].get("url", "")
                if url.startswith("http"):
                    from urllib.parse import urlparse
                    return urlparse(url).path.rstrip("/")
                return url.rstrip("/")
            return ""
        return self.spec.get("basePath", "").rstrip("/")

    def get_title(self) -> str:
        return self.spec.get("info", {}).get("title", "API")

    def get_endpoints(self) -> list[EndpointInfo]:
        endpoints = []
        paths = self.spec.get("paths", {})

        for path, path_item in paths.items():
            path_params = path_item.get("parameters", [])

            for method in ("get", "post", "put", "patch", "delete", "head", "options"):
                if method not in path_item:
                    continue

                operation = path_item[method]
                params = self._resolve_parameters(
                    path_params + operation.get("parameters", [])
                )
                request_body = self._resolve_request_body(operation, method)
                security = operation.get("security", self.global_security)

                endpoint = EndpointInfo(
                    path=path,
                    method=method,
                    operation_id=operation.get("operationId", f"{method}_{path}"),
                    summary=operation.get("summary", ""),
                    description=operation.get("description", ""),
                    parameters=params,
                    request_body=request_body,
                    responses=operation.get("responses", {}),
                    tags=operation.get("tags", []),
                    security=security,
                )
                endpoints.append(endpoint)

        return endpoints

    def _resolve_parameters(
        self, params: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        resolved = []
        for param in params:
            if "$ref" in param:
                param = self._resolve_ref(param["$ref"])
            resolved.append(param)
        return resolved

    def _resolve_request_body(
        self, operation: dict[str, Any], method: str
    ) -> dict[str, Any] | None:
        if self.version.startswith("3"):
            body = operation.get("requestBody")
            if body and "$ref" in body:
                body = self._resolve_ref(body["$ref"])
            return body

        body_params = [
            p for p in operation.get("parameters", []) if p.get("in") == "body"
        ]
        if body_params:
            return {
                "content": {
                    "application/json": {"schema": body_params[0].get("schema", {})}
                }
            }
        return None

    def _resolve_ref(self, ref: str) -> dict[str, Any]:
        parts = ref.lstrip("#/").split("/")
        current = self.spec
        for part in parts:
            current = current.get(part, {})
        return current

    def resolve_schema(self, schema: dict[str, Any]) -> dict[str, Any]:
        if "$ref" in schema:
            schema = self._resolve_ref(schema["$ref"])
        if schema.get("type") == "object" and "properties" in schema:
            resolved_props = {}
            for prop_name, prop_schema in schema["properties"].items():
                resolved_props[prop_name] = self.resolve_schema(prop_schema)
            schema = {**schema, "properties": resolved_props}
        if schema.get("type") == "array" and "items" in schema:
            schema = {**schema, "items": self.resolve_schema(schema["items"])}
        return schema

    def get_request_body_schema(
        self, endpoint: EndpointInfo
    ) -> dict[str, Any] | None:
        if not endpoint.request_body:
            return None
        content = endpoint.request_body.get("content", {})
        json_content = content.get("application/json", {})
        schema = json_content.get("schema", {})
        return self.resolve_schema(schema) if schema else None

    def get_response_schema(
        self, endpoint: EndpointInfo, status_code: str
    ) -> dict[str, Any] | None:
        response = endpoint.responses.get(status_code, {})
        if self.version.startswith("3"):
            content = response.get("content", {})
            json_content = content.get("application/json", {})
            schema = json_content.get("schema", {})
        else:
            schema = response.get("schema", {})
        return self.resolve_schema(schema) if schema else None
