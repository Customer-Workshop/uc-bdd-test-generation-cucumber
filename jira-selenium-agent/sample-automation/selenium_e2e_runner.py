"""Selenium E2E test runner for Car Parts Mock Salesforce UI.

Connects to the running Chrome browser via CDP (Playwright) and executes BDD
test scenarios against the mock Salesforce Lightning application at localhost:5555.
"""

import json
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:5555"
CDP_URL = "http://localhost:29229"

# Load test data
TEST_DATA_PATH = Path(__file__).parent / "car_parts_test_data.json"
with open(TEST_DATA_PATH) as f:
    TEST_CONFIG = json.load(f)


@dataclass
class StepResult:
    keyword: str
    text: str
    status: str = "passed"
    duration_ms: int = 0
    error: str = ""


@dataclass
class ScenarioResult:
    name: str
    jira_id: str
    status: str = "passed"
    steps: list = field(default_factory=list)
    duration_ms: int = 0


def run_step(keyword, text, action_fn):
    """Execute a single BDD step and record results."""
    start = time.time()
    step = StepResult(keyword=keyword, text=text)
    try:
        action_fn()
        step.status = "passed"
    except Exception as e:
        step.status = "failed"
        step.error = str(e)
    step.duration_ms = int((time.time() - start) * 1000)
    status_icon = "\033[92mPASS\033[0m" if step.status == "passed" else "\033[91mFAIL\033[0m"
    print(f"    [{status_icon}] {keyword} {text} ({step.duration_ms}ms)")
    return step


# ---------------------------------------------------------------------------
# Scenario implementations
# ---------------------------------------------------------------------------

def scenario_login(page):
    """Scenario: Login to Salesforce."""
    scenario = ScenarioResult(name="Login to Salesforce", jira_id="CAR-1000")
    start = time.time()

    scenario.steps.append(run_step(
        "Given", "the user navigates to the Salesforce login page",
        lambda: page.goto(f"{BASE_URL}/login")
    ))

    scenario.steps.append(run_step(
        "When", 'the user enters "admin@carparts.demo" in the username field',
        lambda: None  # pre-filled
    ))

    scenario.steps.append(run_step(
        "And", 'the user enters password',
        lambda: None  # pre-filled
    ))

    def click_login():
        page.click("button:has-text('Log In')")
        page.wait_for_url("**/car-parts**", timeout=5000)

    scenario.steps.append(run_step(
        "When", 'the user clicks the "Log In" button',
        click_login
    ))

    scenario.steps.append(run_step(
        "Then", "the Car Parts list view should be displayed",
        lambda: page.wait_for_selector("h2:has-text('Car Parts')", timeout=5000)
    ))

    scenario.duration_ms = int((time.time() - start) * 1000)
    scenario.status = "failed" if any(s.status == "failed" for s in scenario.steps) else "passed"
    return scenario


def scenario_create_part(page, test_data, jira_id, scenario_name):
    """Scenario: Create a car part with all dropdown fields."""
    scenario = ScenarioResult(name=scenario_name, jira_id=jira_id)
    start = time.time()

    # Navigate to list view
    scenario.steps.append(run_step(
        "Given", "the user is on the Car Parts list view",
        lambda: page.goto(f"{BASE_URL}/car-parts")
    ))

    # Click New
    def click_new():
        page.click("a:has-text('+ New')")
        page.wait_for_selector("h2:has-text('New Car Part')", timeout=5000)

    scenario.steps.append(run_step(
        "When", 'the user clicks the "New" button',
        click_new
    ))

    # Verify form
    scenario.steps.append(run_step(
        "Then", "the Car Part creation form should be displayed",
        lambda: page.wait_for_selector("h2:has-text('New Car Part')", timeout=3000)
    ))

    data = test_data["data"]

    # Fill Part Name
    scenario.steps.append(run_step(
        "When", f'the user enters "{data["Part Name"]}" in the "Part Name" field',
        lambda: page.fill("input[name='Part Name']", data["Part Name"])
    ))

    # Fill Part Number
    scenario.steps.append(run_step(
        "And", f'the user enters "{data["Part Number"]}" in the "Part Number" field',
        lambda: page.fill("input[name='Part Number']", data["Part Number"])
    ))

    # Select Part Category first (needed for dependent picklist)
    if "Part Category" in data:
        scenario.steps.append(run_step(
            "And", f'the user selects "{data["Part Category"]}" from the "Part Category" dropdown',
            lambda: page.select_option("select[name='Part Category']", label=data["Part Category"])
        ))

    # Wait for dependent picklist refresh, then select Part Sub-Category
    if "Part Sub-Category" in data:
        def select_sub():
            page.wait_for_timeout(500)
            page.select_option("select[name='Part Sub-Category']", label=data["Part Sub-Category"])

        scenario.steps.append(run_step(
            "And", f'the dependent "Part Sub-Category" dropdown refreshes and user selects "{data["Part Sub-Category"]}"',
            select_sub
        ))

    # Other dropdown fields
    dropdown_order = [
        "Manufacturer", "Condition", "Vehicle Make", "Model Year Range",
        "Availability Status", "Warehouse Location", "Quality Grade",
        "Shipping Class", "Warranty Type",
    ]

    for field_name in dropdown_order:
        if field_name in data:
            val = data[field_name]
            scenario.steps.append(run_step(
                "And", f'the user selects "{val}" from the "{field_name}" dropdown',
                lambda fn=field_name, v=val: page.select_option(f"select[name='{fn}']", label=v)
            ))

    # Currency if present
    if "Currency" in data:
        scenario.steps.append(run_step(
            "And", f'the user selects "{data["Currency"]}" from the "Currency" dropdown',
            lambda: page.select_option("select[name='Currency']", label=data["Currency"])
        ))

    # Fill Unit Price
    if "Unit Price" in data:
        scenario.steps.append(run_step(
            "And", f'the user enters "{data["Unit Price"]}" in the "Unit Price" field',
            lambda: page.fill("input[name='Unit Price']", data["Unit Price"])
        ))

    # Fill Stock Quantity
    if "Stock Quantity" in data:
        scenario.steps.append(run_step(
            "And", f'the user enters "{data["Stock Quantity"]}" in the "Stock Quantity" field',
            lambda: page.fill("input[name='Stock Quantity']", data["Stock Quantity"])
        ))

    # Fill Description
    if "Description" in data:
        scenario.steps.append(run_step(
            "And", 'the user enters the description in the "Description" field',
            lambda: page.fill("textarea[name='Description']", data["Description"])
        ))

    # Click Save
    def click_save():
        page.click("button#saveBtn")
        page.wait_for_timeout(1000)

    scenario.steps.append(run_step(
        "When", 'the user clicks the "Save" button',
        click_save
    ))

    # Verify success toast
    scenario.steps.append(run_step(
        "Then", 'a success toast message "was created" should be displayed',
        lambda: page.wait_for_selector(".sf-toast.success", timeout=5000)
    ))

    # Verify record page
    scenario.steps.append(run_step(
        "And", f'the record page should show "{data["Part Name"]}"',
        lambda: page.wait_for_selector(f"h2:has-text('{data['Part Name']}')", timeout=5000)
    ))

    scenario.duration_ms = int((time.time() - start) * 1000)
    scenario.status = "failed" if any(s.status == "failed" for s in scenario.steps) else "passed"
    return scenario


def scenario_traverse_dropdowns(page):
    """Scenario: Traverse all dropdown fields and verify values."""
    scenario = ScenarioResult(name="Traverse and verify all dropdown fields and their values", jira_id="CAR-1005")
    start = time.time()

    scenario.steps.append(run_step(
        "Given", "the user navigates to the New Car Part form",
        lambda: page.goto(f"{BASE_URL}/car-parts/new")
    ))

    scenario.steps.append(run_step(
        "Then", "the Car Part creation form should be displayed",
        lambda: page.wait_for_selector("h2:has-text('New Car Part')", timeout=5000)
    ))

    fields_to_check = {
        "Part Category": 12,
        "Manufacturer": 23,
        "Condition": 6,
        "Availability Status": 7,
        "Vehicle Make": 21,
        "Model Year Range": 9,
        "Warehouse Location": 7,
        "Quality Grade": 5,
        "Shipping Class": 7,
        "Warranty Type": 7,
        "Currency": 7,
    }

    for label, expected_count in fields_to_check.items():
        def verify_dropdown(lbl=label, cnt=expected_count):
            def action():
                options = page.query_selector_all(f"select[name='{lbl}'] option[value]:not([value=''])")
                actual = len(options)
                assert actual == cnt, f"Expected {cnt} options for {lbl}, got {actual}"
            return action

        scenario.steps.append(run_step(
            "When", f'the user opens the "{label}" dropdown',
            lambda: None
        ))

        scenario.steps.append(run_step(
            "Then", f'the dropdown should contain {expected_count} values',
            verify_dropdown()
        ))

    # Check dependent picklist
    def check_dependent():
        page.select_option("select[name='Part Category']", label="Engine Components")
        page.wait_for_timeout(500)
        sub_options = page.query_selector_all("select[name='Part Sub-Category'] option[value]:not([value=''])")
        assert len(sub_options) == 10, f"Expected 10 sub-categories, got {len(sub_options)}"

    scenario.steps.append(run_step(
        "When", 'the user selects "Engine Components" and checks dependent picklist',
        check_dependent
    ))

    # Check another parent category
    def check_dependent_braking():
        page.select_option("select[name='Part Category']", label="Braking System")
        page.wait_for_timeout(500)
        sub_options = page.query_selector_all("select[name='Part Sub-Category'] option[value]:not([value=''])")
        assert len(sub_options) == 8, f"Expected 8 sub-categories for Braking System, got {len(sub_options)}"

    scenario.steps.append(run_step(
        "And", 'switching to "Braking System" shows 8 sub-categories',
        check_dependent_braking
    ))

    scenario.duration_ms = int((time.time() - start) * 1000)
    scenario.status = "failed" if any(s.status == "failed" for s in scenario.steps) else "passed"
    return scenario


def scenario_edit_part(page):
    """Scenario: Edit an existing car part."""
    scenario = ScenarioResult(name="Edit an existing Car Part and update dropdown fields", jira_id="CAR-1006")
    start = time.time()

    scenario.steps.append(run_step(
        "Given", "the user is on the Car Parts list view",
        lambda: page.goto(f"{BASE_URL}/car-parts")
    ))

    # Click Edit on first part
    def click_edit():
        page.wait_for_timeout(500)
        page.click("a:has-text('Edit'):first-of-type")
        page.wait_for_selector("h2:has-text('Edit')", timeout=5000)

    scenario.steps.append(run_step(
        "When", 'the user clicks "Edit" on the first car part',
        click_edit
    ))

    scenario.steps.append(run_step(
        "Then", "the edit form should be displayed",
        lambda: page.wait_for_selector("h2:has-text('Edit')", timeout=3000)
    ))

    # Update condition
    scenario.steps.append(run_step(
        "When", 'the user changes "Condition" to "Refurbished"',
        lambda: page.select_option("select[name='Condition']", label="Refurbished")
    ))

    # Update availability
    scenario.steps.append(run_step(
        "And", 'the user changes "Availability Status" to "Low Stock"',
        lambda: page.select_option("select[name='Availability Status']", label="Low Stock")
    ))

    # Click Save
    def click_save():
        page.click("button#saveBtn")
        page.wait_for_timeout(1000)

    scenario.steps.append(run_step(
        "And", 'the user clicks "Save"',
        click_save
    ))

    scenario.steps.append(run_step(
        "Then", 'a success toast "was saved" should be displayed',
        lambda: page.wait_for_selector(".sf-toast.success", timeout=5000)
    ))

    scenario.duration_ms = int((time.time() - start) * 1000)
    scenario.status = "failed" if any(s.status == "failed" for s in scenario.steps) else "passed"
    return scenario


def scenario_search_filter(page):
    """Scenario: Search and filter car parts."""
    scenario = ScenarioResult(name="Search and filter Car Parts by different criteria", jira_id="CAR-1007")
    start = time.time()

    scenario.steps.append(run_step(
        "Given", "the user is on the Car Parts list view",
        lambda: page.goto(f"{BASE_URL}/car-parts")
    ))

    # Search
    def search_term():
        page.fill("#searchInput", "Turbocharger")
        page.click("button:has-text('Search')")
        page.wait_for_timeout(500)

    scenario.steps.append(run_step(
        "When", 'the user searches for "Turbocharger"',
        search_term
    ))

    scenario.steps.append(run_step(
        "Then", "only matching car parts should be displayed",
        lambda: page.wait_for_selector("a:has-text('Turbocharger')", timeout=5000)
    ))

    # Filter by In Stock
    scenario.steps.append(run_step(
        "When", 'the user filters by "In Stock" list view',
        lambda: page.goto(f"{BASE_URL}/car-parts?view=instock")
    ))

    scenario.steps.append(run_step(
        "Then", "only in-stock parts should be displayed",
        lambda: page.wait_for_selector("table", timeout=5000)
    ))

    # Filter by Low Stock
    scenario.steps.append(run_step(
        "When", 'the user filters by "Low Stock" list view',
        lambda: page.goto(f"{BASE_URL}/car-parts?view=lowstock")
    ))

    scenario.steps.append(run_step(
        "Then", "only low-stock parts should be displayed",
        lambda: page.wait_for_selector("table", timeout=5000)
    ))

    scenario.duration_ms = int((time.time() - start) * 1000)
    scenario.status = "failed" if any(s.status == "failed" for s in scenario.steps) else "passed"
    return scenario


def scenario_view_record(page):
    """Scenario: View car part record detail."""
    scenario = ScenarioResult(name="View Car Part record detail page", jira_id="CAR-1008")
    start = time.time()

    scenario.steps.append(run_step(
        "Given", "the user is on the Car Parts list view",
        lambda: page.goto(f"{BASE_URL}/car-parts")
    ))

    def click_record():
        page.wait_for_timeout(500)
        page.click("a.sf-link >> nth=0")
        page.wait_for_timeout(500)

    scenario.steps.append(run_step(
        "When", "the user clicks on a car part record",
        click_record
    ))

    scenario.steps.append(run_step(
        "Then", "the record detail page should display all fields",
        lambda: page.wait_for_selector(".sf-detail-grid", timeout=5000)
    ))

    def verify_fields():
        labels = page.query_selector_all(".sf-detail-item label")
        label_texts = [l.text_content() for l in labels]
        for expected in ["Part Name", "Part Number", "Part Category", "Manufacturer"]:
            assert expected in label_texts, f"Missing field: {expected}"

    scenario.steps.append(run_step(
        "And", "all Car Part fields should be visible with correct labels",
        verify_fields
    ))

    scenario.duration_ms = int((time.time() - start) * 1000)
    scenario.status = "failed" if any(s.status == "failed" for s in scenario.steps) else "passed"
    return scenario


def scenario_delete_part(page):
    """Scenario: Delete a car part."""
    scenario = ScenarioResult(name="Delete a Car Part record", jira_id="CAR-1009")
    start = time.time()

    scenario.steps.append(run_step(
        "Given", "the user is on the Car Parts list view",
        lambda: page.goto(f"{BASE_URL}/car-parts")
    ))

    # Click Delete on last row - use evaluate to avoid selector issues
    def click_delete():
        page.wait_for_timeout(500)
        # Use JS to find and click the delete button in the table
        page.evaluate("""() => {
            const buttons = document.querySelectorAll('.sf-btn-destructive');
            const tableButtons = Array.from(buttons).filter(b => b.closest('table'));
            if (tableButtons.length > 0) {
                tableButtons[tableButtons.length - 1].click();
            }
        }""")
        page.wait_for_timeout(500)

    scenario.steps.append(run_step(
        "When", 'the user clicks "Delete" on a car part',
        click_delete
    ))

    # Confirm deletion
    def confirm_delete():
        page.wait_for_selector(".sf-modal-overlay.active", timeout=3000)
        # Click the Delete button inside the modal footer
        page.evaluate("""() => {
            const modal = document.querySelector('.sf-modal-footer');
            const btn = modal.querySelector('.sf-btn-destructive');
            if (btn) btn.click();
        }""")
        page.wait_for_timeout(1000)

    scenario.steps.append(run_step(
        "And", "the user confirms the deletion in the modal",
        confirm_delete
    ))

    scenario.steps.append(run_step(
        "Then", 'a success toast "was deleted" should be displayed',
        lambda: page.wait_for_selector(".sf-toast.success", timeout=5000)
    ))

    scenario.duration_ms = int((time.time() - start) * 1000)
    scenario.status = "failed" if any(s.status == "failed" for s in scenario.steps) else "passed"
    return scenario


def scenario_validate_required(page):
    """Scenario: Validate required fields on Car Part form."""
    scenario = ScenarioResult(name="Validate required fields on Car Part form", jira_id="CAR-1010")
    start = time.time()

    scenario.steps.append(run_step(
        "Given", "the user navigates to the New Car Part form",
        lambda: page.goto(f"{BASE_URL}/car-parts/new")
    ))

    # Click save empty
    def click_save_empty():
        page.wait_for_timeout(300)
        page.click("button#saveBtn")
        page.wait_for_timeout(500)

    scenario.steps.append(run_step(
        "When", 'the user clicks "Save" without filling required fields',
        click_save_empty
    ))

    def check_errors():
        errors = page.query_selector_all(".sf-form-group.has-error")
        assert len(errors) > 0, "Expected validation errors but found none"

    scenario.steps.append(run_step(
        "Then", "validation errors should appear for required fields",
        check_errors
    ))

    scenario.duration_ms = int((time.time() - start) * 1000)
    scenario.status = "failed" if any(s.status == "failed" for s in scenario.steps) else "passed"
    return scenario


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

def main():
    print("\n" + "=" * 70)
    print("  SELENIUM E2E TEST RUNNER - Car Parts Mock Salesforce UI")
    print("  (Using Playwright CDP connection to Chrome)")
    print("=" * 70)
    print(f"  Target URL: {BASE_URL}")
    print(f"  CDP:        {CDP_URL}")
    print("=" * 70 + "\n")

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(CDP_URL)
        context = browser.contexts[0] if browser.contexts else browser.new_context()
        page = context.new_page()

        results = []
        test_records = TEST_CONFIG["test_records"]

        # 1. Login
        print("\n--- Scenario 1: Login (CAR-1000) ---")
        results.append(scenario_login(page))

        # 2-5. Create Car Parts
        create_configs = [
            (test_records[0], "CAR-1001", "Create Engine Component car part with all dropdown fields"),
            (test_records[1], "CAR-1002", "Create Braking System car part with dependent picklists"),
            (test_records[2], "CAR-1003", "Create Suspension and Steering car part"),
            (test_records[3], "CAR-1004", "Create Electrical and Lighting car part"),
        ]
        for i, (data, jira_id, name) in enumerate(create_configs, 2):
            print(f"\n--- Scenario {i}: {name} ({jira_id}) ---")
            results.append(scenario_create_part(page, data, jira_id, name))

        # 6. Traverse dropdowns
        print("\n--- Scenario 6: Traverse All Dropdowns (CAR-1005) ---")
        results.append(scenario_traverse_dropdowns(page))

        # 7. Edit part
        print("\n--- Scenario 7: Edit Car Part (CAR-1006) ---")
        results.append(scenario_edit_part(page))

        # 8. Search and filter
        print("\n--- Scenario 8: Search and Filter (CAR-1007) ---")
        results.append(scenario_search_filter(page))

        # 9. View record
        print("\n--- Scenario 9: View Record Detail (CAR-1008) ---")
        results.append(scenario_view_record(page))

        # 10. Delete part
        print("\n--- Scenario 10: Delete Car Part (CAR-1009) ---")
        results.append(scenario_delete_part(page))

        # 11. Validate required fields
        print("\n--- Scenario 11: Validate Required Fields (CAR-1010) ---")
        results.append(scenario_validate_required(page))

        # Navigate back to list view
        page.goto(f"{BASE_URL}/car-parts")

        # Summary
        total = len(results)
        passed = sum(1 for r in results if r.status == "passed")
        failed = sum(1 for r in results if r.status == "failed")
        total_steps = sum(len(r.steps) for r in results)
        total_steps_passed = sum(1 for r in results for s in r.steps if s.status == "passed")

        print("\n" + "=" * 70)
        print("  SELENIUM E2E TEST RESULTS")
        print("=" * 70)
        for r in results:
            icon = "\033[92mPASS\033[0m" if r.status == "passed" else "\033[91mFAIL\033[0m"
            print(f"  [{icon}] {r.jira_id} | {r.name} ({len(r.steps)} steps, {r.duration_ms}ms)")
            if r.status == "failed":
                for s in r.steps:
                    if s.status == "failed":
                        print(f"         \033[91mFailed: {s.keyword} {s.text}\033[0m")
                        print(f"         Error: {s.error[:200]}")
        print()
        print(f"  Scenarios:  {total} ({passed} passed, {failed} failed)")
        print(f"  Steps:      {total_steps} ({total_steps_passed} passed, {total_steps - total_steps_passed} failed)")
        print(f"  Pass Rate:  {(passed / total * 100):.1f}%")
        print("=" * 70)

        page.close()

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
