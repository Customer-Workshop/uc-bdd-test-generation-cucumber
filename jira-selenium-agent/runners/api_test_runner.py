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
            # Multi-Relationship scenarios
            self._test_parent_child_traversal,
            self._test_child_parent_traversal,
            self._test_lookup_relationship,
            self._test_master_detail_relationship,
            self._test_custom_object_api_names,
            self._test_cross_object_query,
            self._test_relationship_data_isolation,
            self._test_multi_relationship_hub,
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

    # ── Multi-Relationship Test Scenarios ─────────────────────────────────

    def _test_parent_child_traversal(self) -> APIScenarioResult:
        """CAR-1021: Verify parent-to-child relationship traversal via __r."""
        scenario = APIScenarioResult(
            scenario_name="Parent-to-Child Relationship Traversal",
            jira_id="CAR-1021",
            test_case_id="TC-021",
            tags=["@CAR-1021", "@api", "@relationship", "@parent_child", "@priority_high"],
        )
        start = time.time()

        step = self._api_call("GET", "/api/car-parts/CP-001/related", expected_status=200)
        step.step = "GET /api/car-parts/CP-001/related returns expanded relationships"
        scenario.steps.append(step)
        if not step.passed:
            scenario.passed = False
        else:
            body = step.response_body
            orders_check = APIStepResult(
                step='Verify "Orders__r" child relationship exists with records',
                method="ASSERT", endpoint="/api/car-parts/CP-001/related",
                status_code=200, expected_status=200,
                passed="Orders__r" in body and body["Orders__r"]["totalSize"] > 0,
                response_body={"Orders__r_totalSize": body.get("Orders__r", {}).get("totalSize", 0)},
            )
            scenario.steps.append(orders_check)
            if not orders_check.passed:
                scenario.passed = False

            claims_check = APIStepResult(
                step='Verify "Warranty_Claims__r" child relationship exists',
                method="ASSERT", endpoint="/api/car-parts/CP-001/related",
                status_code=200, expected_status=200,
                passed="Warranty_Claims__r" in body and body["Warranty_Claims__r"]["totalSize"] > 0,
                response_body={"Warranty_Claims__r_totalSize": body.get("Warranty_Claims__r", {}).get("totalSize", 0)},
            )
            scenario.steps.append(claims_check)
            if not claims_check.passed:
                scenario.passed = False

            # Verify child records reference back to parent
            if body.get("Orders__r", {}).get("records"):
                fk_check = APIStepResult(
                    step='Verify Orders__r records have Car_Part__c = "CP-001"',
                    method="ASSERT", endpoint="/api/car-parts/CP-001/related",
                    status_code=200, expected_status=200,
                    passed=all(o.get("Car_Part__c") == "CP-001" for o in body["Orders__r"]["records"]),
                )
                scenario.steps.append(fk_check)
                if not fk_check.passed:
                    scenario.passed = False

        scenario.duration_seconds = time.time() - start
        return scenario

    def _test_child_parent_traversal(self) -> APIScenarioResult:
        """CAR-1022: Verify child-to-parent relationship traversal via __r."""
        scenario = APIScenarioResult(
            scenario_name="Child-to-Parent Relationship Traversal",
            jira_id="CAR-1022",
            test_case_id="TC-022",
            tags=["@CAR-1022", "@api", "@relationship", "@child_parent", "@priority_high"],
        )
        start = time.time()

        step = self._api_call("GET", "/api/orders/ORD-001", expected_status=200)
        step.step = "GET /api/orders/ORD-001 returns order with parent traversals"
        scenario.steps.append(step)
        if not step.passed:
            scenario.passed = False
        else:
            body = step.response_body
            part_check = APIStepResult(
                step='Verify Car_Part__r parent reference contains part_name "Turbocharger Assembly"',
                method="ASSERT", endpoint="/api/orders/ORD-001",
                status_code=200, expected_status=200,
                passed="Car_Part__r" in body and body["Car_Part__r"].get("part_name") == "Turbocharger Assembly",
                response_body={"Car_Part__r.part_name": body.get("Car_Part__r", {}).get("part_name")},
            )
            scenario.steps.append(part_check)
            if not part_check.passed:
                scenario.passed = False

            wh_check = APIStepResult(
                step='Verify Ship_From_Warehouse__r parent reference contains "Main Warehouse - A1"',
                method="ASSERT", endpoint="/api/orders/ORD-001",
                status_code=200, expected_status=200,
                passed="Ship_From_Warehouse__r" in body and body["Ship_From_Warehouse__r"].get("Name") == "Main Warehouse - A1",
                response_body={"Ship_From_Warehouse__r.Name": body.get("Ship_From_Warehouse__r", {}).get("Name")},
            )
            scenario.steps.append(wh_check)
            if not wh_check.passed:
                scenario.passed = False

        # Warranty claims with two parent traversals
        wc_step = self._api_call("GET", "/api/warranty-claims", expected_status=200)
        wc_step.step = "Verify warranty claims have Car_Part__r and Order__r parent refs"
        scenario.steps.append(wc_step)
        if wc_step.passed and isinstance(wc_step.response_body, list) and len(wc_step.response_body) > 0:
            multi_parent = APIStepResult(
                step="Verify each warranty claim has both Car_Part__r and Order__r",
                method="ASSERT", endpoint="/api/warranty-claims",
                status_code=200, expected_status=200,
                passed=all("Car_Part__r" in wc and "Order__r" in wc for wc in wc_step.response_body),
            )
            scenario.steps.append(multi_parent)
            if not multi_parent.passed:
                scenario.passed = False

        scenario.duration_seconds = time.time() - start
        return scenario

    def _test_lookup_relationship(self) -> APIScenarioResult:
        """CAR-1023: Verify Lookup relationship fields have distinct __c and __r API names."""
        scenario = APIScenarioResult(
            scenario_name="Lookup Relationship Field Handling",
            jira_id="CAR-1023",
            test_case_id="TC-023",
            tags=["@CAR-1023", "@api", "@relationship", "@lookup", "@priority_high"],
        )
        start = time.time()

        step = self._api_call("GET", "/api/car-parts/CP-001/related", expected_status=200)
        step.step = "GET /api/car-parts/CP-001/related for lookup field verification"
        scenario.steps.append(step)
        if not step.passed:
            scenario.passed = False
        else:
            body = step.response_body
            # Manufacturer__c (ID) vs Manufacturer__r (object)
            mfr_id_check = APIStepResult(
                step='Verify Manufacturer__c (ID field) = "MFR-001"',
                method="ASSERT", endpoint="/api/car-parts/CP-001/related",
                status_code=200, expected_status=200,
                passed=body.get("Manufacturer__c") == "MFR-001",
                response_body={"Manufacturer__c": body.get("Manufacturer__c")},
            )
            scenario.steps.append(mfr_id_check)
            if not mfr_id_check.passed:
                scenario.passed = False

            mfr_obj_check = APIStepResult(
                step='Verify Manufacturer__r (relationship) resolves to Name "BorgWarner"',
                method="ASSERT", endpoint="/api/car-parts/CP-001/related",
                status_code=200, expected_status=200,
                passed=body.get("Manufacturer__r", {}).get("Name") == "BorgWarner",
                response_body={"Manufacturer__r.Name": body.get("Manufacturer__r", {}).get("Name")},
            )
            scenario.steps.append(mfr_obj_check)
            if not mfr_obj_check.passed:
                scenario.passed = False

            # Warehouse__c vs Warehouse__r
            wh_id_check = APIStepResult(
                step='Verify Warehouse__c (ID field) = "WH-001"',
                method="ASSERT", endpoint="/api/car-parts/CP-001/related",
                status_code=200, expected_status=200,
                passed=body.get("Warehouse__c") == "WH-001",
                response_body={"Warehouse__c": body.get("Warehouse__c")},
            )
            scenario.steps.append(wh_id_check)
            if not wh_id_check.passed:
                scenario.passed = False

        # Manufacturer -> Supplier lookup
        mfr_step = self._api_call("GET", "/api/manufacturers/MFR-001", expected_status=200)
        mfr_step.step = "Verify Manufacturer has Primary_Supplier__r lookup"
        scenario.steps.append(mfr_step)
        if mfr_step.passed:
            sup_check = APIStepResult(
                step='Verify Primary_Supplier__r.Name = "Global Steel Corp"',
                method="ASSERT", endpoint="/api/manufacturers/MFR-001",
                status_code=200, expected_status=200,
                passed=mfr_step.response_body.get("Primary_Supplier__r", {}).get("Name") == "Global Steel Corp",
            )
            scenario.steps.append(sup_check)
            if not sup_check.passed:
                scenario.passed = False

        scenario.duration_seconds = time.time() - start
        return scenario

    def _test_master_detail_relationship(self) -> APIScenarioResult:
        """CAR-1024: Verify Master-Detail relationship handling."""
        scenario = APIScenarioResult(
            scenario_name="Master-Detail Relationship Handling",
            jira_id="CAR-1024",
            test_case_id="TC-024",
            tags=["@CAR-1024", "@api", "@relationship", "@master_detail", "@priority_high"],
        )
        start = time.time()

        # Order -> Car_Part__c is Master-Detail
        step = self._api_call("GET", "/api/orders/ORD-001", expected_status=200)
        step.step = "GET /api/orders/ORD-001 for Master-Detail verification"
        scenario.steps.append(step)
        if not step.passed:
            scenario.passed = False
        else:
            body = step.response_body
            md_check = APIStepResult(
                step='Verify Order has Master-Detail Car_Part__c = "CP-001"',
                method="ASSERT", endpoint="/api/orders/ORD-001",
                status_code=200, expected_status=200,
                passed=body.get("Car_Part__c") == "CP-001",
            )
            scenario.steps.append(md_check)
            if not md_check.passed:
                scenario.passed = False

            parent_check = APIStepResult(
                step="Verify Car_Part__r contains full parent record with part_name",
                method="ASSERT", endpoint="/api/orders/ORD-001",
                status_code=200, expected_status=200,
                passed="Car_Part__r" in body and "part_name" in body.get("Car_Part__r", {}),
            )
            scenario.steps.append(parent_check)
            if not parent_check.passed:
                scenario.passed = False

        # Schema confirms Master-Detail type
        schema_step = self._api_call("GET", "/api/relationship-schema", expected_status=200)
        schema_step.step = "Verify schema defines Orders__r as Master-Detail on Car_Part__c"
        scenario.steps.append(schema_step)
        if schema_step.passed:
            cp_children = schema_step.response_body.get("objects", {}).get("Car_Part__c", {}).get("child_relationships", [])
            md_found = any(c.get("relationship_name") == "Orders__r" and c.get("type") == "Master-Detail" for c in cp_children)
            schema_check = APIStepResult(
                step="Verify Car_Part__c child_relationships includes Orders__r (Master-Detail)",
                method="ASSERT", endpoint="/api/relationship-schema",
                status_code=200, expected_status=200,
                passed=md_found,
            )
            scenario.steps.append(schema_check)
            if not schema_check.passed:
                scenario.passed = False

        scenario.duration_seconds = time.time() - start
        return scenario

    def _test_custom_object_api_names(self) -> APIScenarioResult:
        """CAR-1025: Verify all custom objects use __c suffix."""
        scenario = APIScenarioResult(
            scenario_name="Custom Object __c Suffix and API Identity",
            jira_id="CAR-1025",
            test_case_id="TC-025",
            tags=["@CAR-1025", "@api", "@relationship", "@custom_object", "@priority_medium"],
        )
        start = time.time()

        step = self._api_call("GET", "/api/relationship-schema", expected_status=200)
        step.step = "GET /api/relationship-schema returns all custom objects"
        scenario.steps.append(step)
        if not step.passed:
            scenario.passed = False
        else:
            objects = step.response_body.get("objects", {})
            expected = ["Car_Part__c", "Manufacturer__c", "Warehouse__c", "Supplier__c", "Order__c", "Warranty_Claim__c"]

            suffix_check = APIStepResult(
                step="Verify all object API names end with __c",
                method="ASSERT", endpoint="/api/relationship-schema",
                status_code=200, expected_status=200,
                passed=all(name.endswith("__c") for name in objects.keys()),
                response_body={"objects": list(objects.keys())},
            )
            scenario.steps.append(suffix_check)
            if not suffix_check.passed:
                scenario.passed = False

            presence_check = APIStepResult(
                step=f"Verify schema contains all 6 custom objects: {', '.join(expected)}",
                method="ASSERT", endpoint="/api/relationship-schema",
                status_code=200, expected_status=200,
                passed=all(e in objects for e in expected),
            )
            scenario.steps.append(presence_check)
            if not presence_check.passed:
                scenario.passed = False

            prefixes = {name: obj.get("key_prefix", "") for name, obj in objects.items()}
            unique_check = APIStepResult(
                step="Verify each object has a unique key_prefix",
                method="ASSERT", endpoint="/api/relationship-schema",
                status_code=200, expected_status=200,
                passed=len(set(prefixes.values())) == len(prefixes),
                response_body=prefixes,
            )
            scenario.steps.append(unique_check)
            if not unique_check.passed:
                scenario.passed = False

        scenario.duration_seconds = time.time() - start
        return scenario

    def _test_cross_object_query(self) -> APIScenarioResult:
        """CAR-1026: Verify SOQL-style cross-object query traversal."""
        scenario = APIScenarioResult(
            scenario_name="Cross-Object SOQL Query Traversal",
            jira_id="CAR-1026",
            test_case_id="TC-026",
            tags=["@CAR-1026", "@api", "@relationship", "@soql", "@priority_high"],
        )
        start = time.time()

        # Query Car_Part__c with Manufacturer__r
        step = self._api_call(
            "POST", "/api/soql",
            data={"query": "SELECT Name, Manufacturer__r.Name FROM Car_Part__c"},
            expected_status=200,
        )
        step.step = "SOQL: SELECT Name, Manufacturer__r.Name FROM Car_Part__c"
        scenario.steps.append(step)
        if not step.passed:
            scenario.passed = False
        else:
            body = step.response_body
            records_with_mfr = [r for r in body.get("records", []) if "Manufacturer__r" in r]
            mfr_check = APIStepResult(
                step="Verify records with Manufacturer__c have Manufacturer__r resolved",
                method="ASSERT", endpoint="/api/soql",
                status_code=200, expected_status=200,
                passed=len(records_with_mfr) > 0 and body.get("totalSize", 0) > 0,
                response_body={"totalSize": body.get("totalSize", 0), "records_with_mfr": len(records_with_mfr)},
            )
            scenario.steps.append(mfr_check)
            if not mfr_check.passed:
                scenario.passed = False

        # Query with child subquery
        step2 = self._api_call(
            "POST", "/api/soql",
            data={"query": "SELECT Name, (SELECT Name FROM Orders__r) FROM Car_Part__c"},
            expected_status=200,
        )
        step2.step = "SOQL: SELECT Name, (SELECT Name FROM Orders__r) FROM Car_Part__c"
        scenario.steps.append(step2)
        if not step2.passed:
            scenario.passed = False

        # Query Warranty_Claim__c with two parent refs
        step3 = self._api_call(
            "POST", "/api/soql",
            data={"query": "SELECT Name, Car_Part__r.Name, Order__r.Name FROM Warranty_Claim__c"},
            expected_status=200,
        )
        step3.step = "SOQL: SELECT Name, Car_Part__r.Name, Order__r.Name FROM Warranty_Claim__c"
        scenario.steps.append(step3)
        if not step3.passed:
            scenario.passed = False
        elif step3.response_body.get("records"):
            dual_parent = APIStepResult(
                step="Verify each warranty claim has both Car_Part__r and Order__r in SOQL result",
                method="ASSERT", endpoint="/api/soql",
                status_code=200, expected_status=200,
                passed=all("Car_Part__r" in r and "Order__r" in r for r in step3.response_body["records"]),
            )
            scenario.steps.append(dual_parent)
            if not dual_parent.passed:
                scenario.passed = False

        scenario.duration_seconds = time.time() - start
        return scenario

    def _test_relationship_data_isolation(self) -> APIScenarioResult:
        """CAR-1027: Verify data does not blend between relationship paths."""
        scenario = APIScenarioResult(
            scenario_name="Relationship Data Isolation Between Paths",
            jira_id="CAR-1027",
            test_case_id="TC-027",
            tags=["@CAR-1027", "@api", "@relationship", "@data_isolation", "@priority_high"],
        )
        start = time.time()

        step = self._api_call("GET", "/api/car-parts/CP-001/related", expected_status=200)
        step.step = "GET /api/car-parts/CP-001/related for data isolation check"
        scenario.steps.append(step)
        if not step.passed:
            scenario.passed = False
        else:
            body = step.response_body
            # Manufacturer__r and Warehouse__r should be different object types
            mfr_id = body.get("Manufacturer__r", {}).get("id", "")
            wh_id = body.get("Warehouse__r", {}).get("id", "")
            isolation_check = APIStepResult(
                step="Verify Manufacturer__r.id and Warehouse__r.id are different records",
                method="ASSERT", endpoint="/api/car-parts/CP-001/related",
                status_code=200, expected_status=200,
                passed=mfr_id != wh_id and mfr_id.startswith("MFR") and wh_id.startswith("WH"),
                response_body={"Manufacturer__r.id": mfr_id, "Warehouse__r.id": wh_id},
            )
            scenario.steps.append(isolation_check)
            if not isolation_check.passed:
                scenario.passed = False

        # Order has two distinct parent paths
        order_step = self._api_call("GET", "/api/orders/ORD-001", expected_status=200)
        order_step.step = "Verify Order has two isolated parent paths"
        scenario.steps.append(order_step)
        if order_step.passed:
            body = order_step.response_body
            order_isolation = APIStepResult(
                step="Verify Car_Part__r and Ship_From_Warehouse__r are independent objects",
                method="ASSERT", endpoint="/api/orders/ORD-001",
                status_code=200, expected_status=200,
                passed=(
                    "Car_Part__r" in body and "Ship_From_Warehouse__r" in body
                    and body["Car_Part__r"].get("id", "").startswith("CP")
                    and body["Ship_From_Warehouse__r"].get("id", "").startswith("WH")
                ),
            )
            scenario.steps.append(order_isolation)
            if not order_isolation.passed:
                scenario.passed = False

        scenario.duration_seconds = time.time() - start
        return scenario

    def _test_multi_relationship_hub(self) -> APIScenarioResult:
        """CAR-1028: Verify Car Part functions as a central data hub."""
        scenario = APIScenarioResult(
            scenario_name="Multi-Relationship Central Data Hub",
            jira_id="CAR-1028",
            test_case_id="TC-028",
            tags=["@CAR-1028", "@api", "@relationship", "@data_hub", "@priority_medium"],
        )
        start = time.time()

        # Car Part as hub: 2 parents + 2 child relationships
        step = self._api_call("GET", "/api/car-parts/CP-001/related", expected_status=200)
        step.step = "Verify Car Part CP-001 is connected to 4 relationship paths"
        scenario.steps.append(step)
        if not step.passed:
            scenario.passed = False
        else:
            body = step.response_body
            hub_check = APIStepResult(
                step="Verify hub has Manufacturer__r, Warehouse__r, Orders__r, Warranty_Claims__r",
                method="ASSERT", endpoint="/api/car-parts/CP-001/related",
                status_code=200, expected_status=200,
                passed=all(k in body for k in ["Manufacturer__r", "Warehouse__r", "Orders__r", "Warranty_Claims__r"]),
            )
            scenario.steps.append(hub_check)
            if not hub_check.passed:
                scenario.passed = False

        # Manufacturer as hub
        mfr_step = self._api_call("GET", "/api/manufacturers/MFR-001", expected_status=200)
        mfr_step.step = "Verify Manufacturer MFR-001 has supplier and car parts connections"
        scenario.steps.append(mfr_step)
        if mfr_step.passed:
            mfr_hub = APIStepResult(
                step="Verify manufacturer has Primary_Supplier__r and Car_Parts__r",
                method="ASSERT", endpoint="/api/manufacturers/MFR-001",
                status_code=200, expected_status=200,
                passed="Primary_Supplier__r" in mfr_step.response_body and "Car_Parts__r" in mfr_step.response_body,
            )
            scenario.steps.append(mfr_hub)
            if not mfr_hub.passed:
                scenario.passed = False

        # Warehouse as hub
        wh_step = self._api_call("GET", "/api/warehouses/WH-001", expected_status=200)
        wh_step.step = "Verify Warehouse WH-001 has car parts and orders connections"
        scenario.steps.append(wh_step)
        if wh_step.passed:
            wh_hub = APIStepResult(
                step="Verify warehouse has Car_Parts__r and Orders__r",
                method="ASSERT", endpoint="/api/warehouses/WH-001",
                status_code=200, expected_status=200,
                passed="Car_Parts__r" in wh_step.response_body and "Orders__r" in wh_step.response_body,
            )
            scenario.steps.append(wh_hub)
            if not wh_hub.passed:
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
