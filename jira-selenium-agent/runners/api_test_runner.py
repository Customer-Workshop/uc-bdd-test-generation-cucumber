"""API Testing Agent - REST API test execution engine.

Executes BDD-style API tests against target application REST endpoints.
Validates CRUD operations, response codes, payload schemas, and field values.

Usage:
    python runners/api_test_runner.py
"""

import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import requests

logger = logging.getLogger(__name__)


@dataclass
class APIStepResult:
    """Result of a single API test step."""
    step: str
    method: str
    endpoint: str
    status_code: int
    expected_status: int
    passed: bool
    response_body: Any = None
    error: str = ""
    duration_ms: float = 0.0


@dataclass
class APIScenarioResult:
    """Result of an API test scenario."""
    scenario_name: str
    jira_id: str
    test_case_id: str
    steps: list[APIStepResult] = field(default_factory=list)
    passed: bool = True
    duration_seconds: float = 0.0
    tags: list[str] = field(default_factory=list)


@dataclass
class APITestReport:
    """Complete API test execution report."""
    run_id: str
    app_url: str
    scenarios: list[APIScenarioResult] = field(default_factory=list)
    total_scenarios: int = 0
    passed_scenarios: int = 0
    failed_scenarios: int = 0
    total_steps: int = 0
    passed_steps: int = 0
    duration_seconds: float = 0.0


class APITestRunner:
    """Executes REST API tests against the target application."""

    def __init__(self, base_url: str = "http://localhost:5555"):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.test_data = self._load_test_data()

    def _load_test_data(self) -> dict:
        """Load test data from JSON file."""
        data_path = Path(__file__).parent.parent / "test-data" / "car_parts_test_data.json"
        if data_path.exists():
            with open(data_path, encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _api_call(self, method: str, endpoint: str, data: dict = None,
                  expected_status: int = 200) -> APIStepResult:
        """Execute a single API call and return result."""
        url = f"{self.base_url}{endpoint}"
        start = time.time()
        try:
            resp = self.session.request(method, url, json=data, timeout=10)
            duration_ms = (time.time() - start) * 1000
            passed = resp.status_code == expected_status
            try:
                body = resp.json()
            except (ValueError, requests.exceptions.JSONDecodeError):
                body = resp.text
            return APIStepResult(
                step=f"{method} {endpoint}",
                method=method,
                endpoint=endpoint,
                status_code=resp.status_code,
                expected_status=expected_status,
                passed=passed,
                response_body=body,
                duration_ms=duration_ms,
            )
        except requests.RequestException as e:
            return APIStepResult(
                step=f"{method} {endpoint}",
                method=method,
                endpoint=endpoint,
                status_code=0,
                expected_status=expected_status,
                passed=False,
                error=str(e),
                duration_ms=(time.time() - start) * 1000,
            )

    def run(self) -> APITestReport:
        """Execute all API test scenarios."""
        logger.info("=" * 70)
        logger.info("CAR PARTS REST API - E2E TEST EXECUTION")
        logger.info("=" * 70)
        logger.info("Base URL: %s", self.base_url)
        logger.info("")

        start_time = time.time()
        run_id = f"api-{int(time.time())}"
        report = APITestReport(run_id=run_id, app_url=self.base_url)

        scenarios = [
            self._test_api_health_check,
            self._test_list_car_parts,
            self._test_get_car_part_by_id,
            self._test_create_car_part,
            self._test_update_car_part,
            self._test_delete_car_part,
            self._test_get_dropdown_fields,
            self._test_get_sub_categories,
            self._test_get_nonexistent_part,
            self._test_create_invalid_part,
        ]

        for scenario_fn in scenarios:
            result = scenario_fn()
            report.scenarios.append(result)
            status = "PASS" if result.passed else "FAIL"
            logger.info(
                "[%s] %s - %s (%d steps, %.1fs)",
                status, result.jira_id, result.scenario_name,
                len(result.steps), result.duration_seconds
            )

        report.total_scenarios = len(report.scenarios)
        report.passed_scenarios = sum(1 for s in report.scenarios if s.passed)
        report.failed_scenarios = report.total_scenarios - report.passed_scenarios
        report.total_steps = sum(len(s.steps) for s in report.scenarios)
        report.passed_steps = sum(
            sum(1 for st in s.steps if st.passed) for s in report.scenarios
        )
        report.duration_seconds = time.time() - start_time

        logger.info("")
        logger.info("=" * 70)
        logger.info("API TEST RESULTS: %d/%d scenarios passed, %d steps (%.1fs)",
                     report.passed_scenarios, report.total_scenarios,
                     report.total_steps, report.duration_seconds)
        logger.info("=" * 70)

        self._save_report(report)
        return report

    def _test_api_health_check(self) -> APIScenarioResult:
        """CAR-1011: Verify API is reachable."""
        scenario = APIScenarioResult(
            scenario_name="API Health Check",
            jira_id="CAR-1011",
            test_case_id="TC-011",
            tags=["@CAR-1011", "@api", "@health", "@priority_high"],
        )
        start = time.time()

        step = self._api_call("GET", "/api/car-parts", expected_status=200)
        step.step = "Verify GET /api/car-parts returns 200"
        scenario.steps.append(step)
        if not step.passed:
            scenario.passed = False

        step2 = self._api_call("GET", "/api/dropdown-fields", expected_status=200)
        step2.step = "Verify GET /api/dropdown-fields returns 200"
        scenario.steps.append(step2)
        if not step2.passed:
            scenario.passed = False

        scenario.duration_seconds = time.time() - start
        return scenario

    def _test_list_car_parts(self) -> APIScenarioResult:
        """CAR-1012: List all car parts via API."""
        scenario = APIScenarioResult(
            scenario_name="List All Car Parts via API",
            jira_id="CAR-1012",
            test_case_id="TC-012",
            tags=["@CAR-1012", "@api", "@read", "@priority_high"],
        )
        start = time.time()

        step = self._api_call("GET", "/api/car-parts", expected_status=200)
        step.step = "GET /api/car-parts returns list of parts"
        scenario.steps.append(step)
        if not step.passed:
            scenario.passed = False
        elif not isinstance(step.response_body, list):
            step.passed = False
            step.error = "Response is not a list"
            scenario.passed = False
        else:
            count_step = APIStepResult(
                step=f"Verify response contains {len(step.response_body)} car parts",
                method="ASSERT",
                endpoint="/api/car-parts",
                status_code=200,
                expected_status=200,
                passed=len(step.response_body) >= 1,
                response_body={"count": len(step.response_body)},
            )
            scenario.steps.append(count_step)
            if not count_step.passed:
                scenario.passed = False

            field_step = APIStepResult(
                step="Verify each part has required fields (id, part_name, part_number, part_category)",
                method="ASSERT",
                endpoint="/api/car-parts",
                status_code=200,
                expected_status=200,
                passed=all(
                    all(k in p for k in ["id", "part_name", "part_number", "part_category"])
                    for p in step.response_body
                ),
            )
            scenario.steps.append(field_step)
            if not field_step.passed:
                scenario.passed = False

        scenario.duration_seconds = time.time() - start
        return scenario

    def _test_get_car_part_by_id(self) -> APIScenarioResult:
        """CAR-1013: Get a single car part by ID."""
        scenario = APIScenarioResult(
            scenario_name="Get Car Part by ID via API",
            jira_id="CAR-1013",
            test_case_id="TC-013",
            tags=["@CAR-1013", "@api", "@read", "@priority_high"],
        )
        start = time.time()

        step = self._api_call("GET", "/api/car-parts/CP-001", expected_status=200)
        step.step = "GET /api/car-parts/CP-001 returns part details"
        scenario.steps.append(step)
        if not step.passed:
            scenario.passed = False
        else:
            name_check = APIStepResult(
                step='Verify part_name is "Turbocharger Assembly"',
                method="ASSERT",
                endpoint="/api/car-parts/CP-001",
                status_code=200,
                expected_status=200,
                passed=step.response_body.get("part_name") == "Turbocharger Assembly",
                response_body={"part_name": step.response_body.get("part_name")},
            )
            scenario.steps.append(name_check)
            if not name_check.passed:
                scenario.passed = False

            cat_check = APIStepResult(
                step='Verify part_category is "Engine Components"',
                method="ASSERT",
                endpoint="/api/car-parts/CP-001",
                status_code=200,
                expected_status=200,
                passed=step.response_body.get("part_category") == "Engine Components",
                response_body={"part_category": step.response_body.get("part_category")},
            )
            scenario.steps.append(cat_check)
            if not cat_check.passed:
                scenario.passed = False

        scenario.duration_seconds = time.time() - start
        return scenario

    def _test_create_car_part(self) -> APIScenarioResult:
        """CAR-1014: Create a new car part via API."""
        scenario = APIScenarioResult(
            scenario_name="Create Car Part via API",
            jira_id="CAR-1014",
            test_case_id="TC-014",
            tags=["@CAR-1014", "@api", "@create", "@priority_high"],
        )
        start = time.time()

        new_part = {
            "part_name": "API Test - Alternator",
            "part_number": "ALT-API-2024-099",
            "part_category": "Electrical & Lighting",
            "part_sub_category": "Alternator",
            "manufacturer": "Denso",
            "condition": "New",
            "vehicle_make": "Toyota",
            "year_range": "2022-2024",
            "unit_price": 320.00,
            "stock_quantity": 50,
            "availability": "In Stock",
            "warehouse_location": "Main Warehouse - A1",
            "quality_grade": "OEM",
            "shipping_class": "Standard",
            "warranty_type": "Manufacturer Warranty",
            "currency": "USD",
            "description": "API test - high output alternator",
        }

        step = self._api_call("POST", "/api/car-parts", data=new_part, expected_status=201)
        step.step = "POST /api/car-parts creates new part with 201"
        scenario.steps.append(step)
        if not step.passed:
            scenario.passed = False
        else:
            id_check = APIStepResult(
                step="Verify response contains generated ID",
                method="ASSERT",
                endpoint="/api/car-parts",
                status_code=201,
                expected_status=201,
                passed="id" in step.response_body,
                response_body={"id": step.response_body.get("id")},
            )
            scenario.steps.append(id_check)

            created_id = step.response_body.get("id", "")
            if created_id:
                verify = self._api_call("GET", f"/api/car-parts/{created_id}", expected_status=200)
                verify.step = f"GET /api/car-parts/{created_id} confirms part exists"
                scenario.steps.append(verify)
                if not verify.passed:
                    scenario.passed = False

        scenario.duration_seconds = time.time() - start
        return scenario

    def _test_update_car_part(self) -> APIScenarioResult:
        """CAR-1015: Update an existing car part via API."""
        scenario = APIScenarioResult(
            scenario_name="Update Car Part via API",
            jira_id="CAR-1015",
            test_case_id="TC-015",
            tags=["@CAR-1015", "@api", "@update", "@priority_high"],
        )
        start = time.time()

        update_data = {
            "condition": "Refurbished",
            "unit_price": 999.99,
            "availability": "Low Stock",
        }

        step = self._api_call("PUT", "/api/car-parts/CP-002", data=update_data, expected_status=200)
        step.step = "PUT /api/car-parts/CP-002 updates fields"
        scenario.steps.append(step)
        if not step.passed:
            scenario.passed = False
        else:
            cond_check = APIStepResult(
                step='Verify condition updated to "Refurbished"',
                method="ASSERT",
                endpoint="/api/car-parts/CP-002",
                status_code=200,
                expected_status=200,
                passed=step.response_body.get("condition") == "Refurbished",
                response_body={"condition": step.response_body.get("condition")},
            )
            scenario.steps.append(cond_check)
            if not cond_check.passed:
                scenario.passed = False

            price_check = APIStepResult(
                step="Verify unit_price updated to 999.99",
                method="ASSERT",
                endpoint="/api/car-parts/CP-002",
                status_code=200,
                expected_status=200,
                passed=step.response_body.get("unit_price") == 999.99,
                response_body={"unit_price": step.response_body.get("unit_price")},
            )
            scenario.steps.append(price_check)
            if not price_check.passed:
                scenario.passed = False

        scenario.duration_seconds = time.time() - start
        return scenario

    def _test_delete_car_part(self) -> APIScenarioResult:
        """CAR-1016: Delete a car part via API."""
        scenario = APIScenarioResult(
            scenario_name="Delete Car Part via API",
            jira_id="CAR-1016",
            test_case_id="TC-016",
            tags=["@CAR-1016", "@api", "@delete", "@priority_medium"],
        )
        start = time.time()

        # Create a part to delete
        temp_part = {"part_name": "API Delete Test", "part_number": "DEL-001",
                     "part_category": "Engine Components"}
        create_step = self._api_call("POST", "/api/car-parts", data=temp_part, expected_status=201)
        create_step.step = "Create temporary part for deletion"
        scenario.steps.append(create_step)

        if create_step.passed and isinstance(create_step.response_body, dict):
            part_id = create_step.response_body.get("id", "")
            if part_id:
                del_step = self._api_call("DELETE", f"/api/car-parts/{part_id}", expected_status=200)
                del_step.step = f"DELETE /api/car-parts/{part_id} returns 200"
                scenario.steps.append(del_step)
                if not del_step.passed:
                    scenario.passed = False

                verify = self._api_call("GET", f"/api/car-parts/{part_id}", expected_status=404)
                verify.step = f"GET /api/car-parts/{part_id} returns 404 after deletion"
                scenario.steps.append(verify)
                if not verify.passed:
                    scenario.passed = False
        else:
            scenario.passed = False

        scenario.duration_seconds = time.time() - start
        return scenario

    def _test_get_dropdown_fields(self) -> APIScenarioResult:
        """CAR-1017: Verify dropdown fields metadata API."""
        scenario = APIScenarioResult(
            scenario_name="Get Dropdown Fields Metadata via API",
            jira_id="CAR-1017",
            test_case_id="TC-017",
            tags=["@CAR-1017", "@api", "@read", "@priority_medium"],
        )
        start = time.time()

        step = self._api_call("GET", "/api/dropdown-fields", expected_status=200)
        step.step = "GET /api/dropdown-fields returns field definitions"
        scenario.steps.append(step)
        if not step.passed:
            scenario.passed = False
        else:
            expected_fields = [
                "part_category", "condition", "manufacturer",
                "vehicle_make", "availability", "quality_grade",
            ]
            for fld in expected_fields:
                fld_check = APIStepResult(
                    step=f'Verify dropdown field "{fld}" exists with values',
                    method="ASSERT",
                    endpoint="/api/dropdown-fields",
                    status_code=200,
                    expected_status=200,
                    passed=(fld in step.response_body and len(step.response_body[fld]) > 0),
                    response_body={fld: len(step.response_body.get(fld, []))},
                )
                scenario.steps.append(fld_check)
                if not fld_check.passed:
                    scenario.passed = False

        scenario.duration_seconds = time.time() - start
        return scenario

    def _test_get_sub_categories(self) -> APIScenarioResult:
        """CAR-1018: Verify dependent picklist sub-categories API."""
        scenario = APIScenarioResult(
            scenario_name="Get Dependent Sub-Categories via API",
            jira_id="CAR-1018",
            test_case_id="TC-018",
            tags=["@CAR-1018", "@api", "@read", "@priority_medium"],
        )
        start = time.time()

        categories_to_test = ["Engine Components", "Braking System", "Electrical & Lighting"]
        for cat in categories_to_test:
            step = self._api_call("GET", f"/api/sub-categories/{cat}", expected_status=200)
            step.step = f'GET /api/sub-categories/{cat} returns sub-categories'
            scenario.steps.append(step)
            if not step.passed:
                scenario.passed = False
            elif not isinstance(step.response_body, list) or len(step.response_body) == 0:
                step.passed = False
                step.error = f"Expected non-empty list for {cat}"
                scenario.passed = False

        scenario.duration_seconds = time.time() - start
        return scenario

    def _test_get_nonexistent_part(self) -> APIScenarioResult:
        """CAR-1019: Verify 404 for nonexistent car part."""
        scenario = APIScenarioResult(
            scenario_name="Get Nonexistent Car Part Returns 404",
            jira_id="CAR-1019",
            test_case_id="TC-019",
            tags=["@CAR-1019", "@api", "@validation", "@priority_medium"],
        )
        start = time.time()

        step = self._api_call("GET", "/api/car-parts/NONEXISTENT-999", expected_status=404)
        step.step = "GET /api/car-parts/NONEXISTENT-999 returns 404"
        scenario.steps.append(step)
        if not step.passed:
            scenario.passed = False

        del_step = self._api_call("DELETE", "/api/car-parts/NONEXISTENT-999", expected_status=404)
        del_step.step = "DELETE /api/car-parts/NONEXISTENT-999 returns 404"
        scenario.steps.append(del_step)
        if not del_step.passed:
            scenario.passed = False

        scenario.duration_seconds = time.time() - start
        return scenario

    def _test_create_invalid_part(self) -> APIScenarioResult:
        """CAR-1020: Verify validation on create with empty body."""
        scenario = APIScenarioResult(
            scenario_name="Create Car Part with Invalid Data Returns 400",
            jira_id="CAR-1020",
            test_case_id="TC-020",
            tags=["@CAR-1020", "@api", "@validation", "@priority_high"],
        )
        start = time.time()

        step = self._api_call("POST", "/api/car-parts", data=None, expected_status=400)
        step.step = "POST /api/car-parts with no body returns 400"
        scenario.steps.append(step)
        if not step.passed:
            scenario.passed = False

        scenario.duration_seconds = time.time() - start
        return scenario

    def _save_report(self, report: APITestReport):
        """Save API test report to reports directory."""
        reports_dir = Path(__file__).parent.parent / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)

        report_data = {
            "run_id": report.run_id,
            "type": "api",
            "app_url": report.app_url,
            "total_scenarios": report.total_scenarios,
            "passed_scenarios": report.passed_scenarios,
            "failed_scenarios": report.failed_scenarios,
            "total_steps": report.total_steps,
            "passed_steps": report.passed_steps,
            "duration_seconds": round(report.duration_seconds, 2),
            "scenarios": [
                {
                    "scenario_name": s.scenario_name,
                    "jira_id": s.jira_id,
                    "test_case_id": s.test_case_id,
                    "passed": s.passed,
                    "tags": s.tags,
                    "duration_seconds": round(s.duration_seconds, 3),
                    "steps": [
                        {
                            "step": st.step,
                            "method": st.method,
                            "endpoint": st.endpoint,
                            "status_code": st.status_code,
                            "expected_status": st.expected_status,
                            "passed": st.passed,
                            "error": st.error,
                            "duration_ms": round(st.duration_ms, 1),
                        }
                        for st in s.steps
                    ],
                }
                for s in report.scenarios
            ],
        }

        report_path = reports_dir / f"api-report-{report.run_id}.json"
        report_path.write_text(json.dumps(report_data, indent=2), encoding="utf-8")
        logger.info("API test report saved: %s", report_path)

        # Also save as latest
        latest_path = reports_dir / "latest_api_report.json"
        latest_path.write_text(json.dumps(report_data, indent=2), encoding="utf-8")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    runner = APITestRunner()
    report = runner.run()
    print(f"\nAPI Tests: {report.passed_scenarios}/{report.total_scenarios} scenarios passed")
    print(f"Steps: {report.passed_steps}/{report.total_steps}")
