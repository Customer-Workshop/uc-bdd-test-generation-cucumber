"""Multi-UI Framework Page Objects.

Provides specialized Page Object Model classes for:
- Salesforce UI (Lightning, Aura, LWC components)
- React applications (data-testid, React component patterns)
- Angular applications (ng-model, ng-click, Angular component selectors)

Each framework has its own locator strategies and common patterns.
"""

import logging
import re
import time
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from page_object_model import BasePage, Locator

logger = logging.getLogger(__name__)


class UIFramework(Enum):
    """Supported UI frameworks."""
    SALESFORCE = "salesforce"
    REACT = "react"
    ANGULAR = "angular"
    GENERIC = "generic"


# ---------------------------------------------------------------------------
# Salesforce Lightning / Aura / LWC Page Objects
# ---------------------------------------------------------------------------

class SalesforcePage(BasePage):
    """Base page object for Salesforce Lightning UI.

    Handles Shadow DOM traversal, Lightning component selectors,
    Aura framework waits, and LWC component patterns.
    """

    # Common Salesforce Lightning selectors
    APP_LAUNCHER = Locator("app_launcher", "css", "button.slds-icon-waffle_container, div.appLauncher", "App Launcher")
    GLOBAL_SEARCH = Locator("global_search", "css", "input.slds-input[type='search'], lightning-input.search-input input", "Global Search")
    NAV_BAR = Locator("nav_bar", "css", "one-app-nav-bar, nav[role='navigation']", "Navigation Bar")
    TOAST_MESSAGE = Locator("toast", "css", "div.toastMessage, lightning-primitive-icon.toastIcon", "Toast Message")
    MODAL_DIALOG = Locator("modal", "css", "section[role='dialog'], div.modal-container", "Modal Dialog")
    LOADING_SPINNER = Locator("spinner", "css", "lightning-spinner, div.slds-spinner_container", "Loading Spinner")

    # Record page selectors
    RECORD_FORM = Locator("record_form", "css", "records-record-layout-event, lightning-record-form", "Record Form")
    RECORD_DETAIL = Locator("record_detail", "css", "records-lwc-detail-panel, force-record-layout-section", "Record Detail")
    SAVE_BUTTON = Locator("save_button", "css", "button[name='SaveEdit'], lightning-button[data-aura-class='uiButton'] button", "Save Button")
    EDIT_BUTTON = Locator("edit_button", "css", "button[name='Edit'], lightning-button-icon[title='Edit']", "Edit Button")
    DELETE_BUTTON = Locator("delete_button", "css", "button[name='Delete'], a[title='Delete']", "Delete Button")

    # List view selectors
    LIST_VIEW = Locator("list_view", "css", "lightning-list-view, force-list-view-manager-grid", "List View")
    LIST_VIEW_ROWS = Locator("list_rows", "css", "table tbody tr, lightning-datatable tbody tr", "List View Rows")
    NEW_BUTTON = Locator("new_button", "css", "a[title='New'], lightning-button[title='New']", "New Button")

    def __init__(self, driver: WebDriver, base_url: str = ""):
        super().__init__(driver, base_url)
        self._shadow_host_cache: dict[str, WebElement] = {}

    def wait_for_lightning_ready(self, timeout: int = 30):
        """Wait for Salesforce Lightning framework to be fully loaded."""
        WebDriverWait(self.driver, timeout).until(
            lambda d: d.execute_script(
                "return typeof $A !== 'undefined' && $A.get('e.force:navigateToURL') !== undefined"
                " || document.querySelector('lightning-app') !== null"
            )
        )
        self._wait_for_spinner_gone(timeout)

    def _wait_for_spinner_gone(self, timeout: int = 15):
        """Wait for Lightning spinners to disappear."""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.invisibility_of_element_located((
                    By.CSS_SELECTOR,
                    "lightning-spinner, div.slds-spinner_container"
                ))
            )
        except Exception:
            pass

    def find_lightning_input(self, label: str) -> WebElement:
        """Find a Lightning input field by its label text."""
        xpath = (
            f"//lightning-input[.//label[contains(text(), '{label}')]]//input"
            f" | //lightning-textarea[.//label[contains(text(), '{label}')]]//textarea"
            f" | //lightning-combobox[.//label[contains(text(), '{label}')]]//input"
            f" | //force-record-layout-item[.//span[contains(text(), '{label}')]]//input"
        )
        return self.find(Locator(f"input_{label}", "xpath", xpath))

    def set_lightning_input(self, label: str, value: str):
        """Set a value in a Lightning input field."""
        element = self.find_lightning_input(label)
        element.clear()
        element.send_keys(value)
        logger.info("Set Lightning input '%s' to '%s'", label, value)

    def click_lightning_button(self, label: str):
        """Click a Lightning button by its label."""
        xpath = (
            f"//lightning-button[.//button[contains(text(), '{label}')]]//button"
            f" | //button[contains(text(), '{label}')]"
            f" | //lightning-button[@label='{label}']//button"
        )
        self.click(Locator(f"button_{label}", "xpath", xpath))

    def find_lwc_component(self, tag_name: str) -> WebElement:
        """Find a Lightning Web Component by its tag name."""
        return self.find(Locator(f"lwc_{tag_name}", "css", tag_name))

    def get_lwc_shadow_element(
        self, host_selector: str, shadow_selector: str
    ) -> WebElement:
        """Traverse Shadow DOM to find an element inside an LWC component.

        Args:
            host_selector: CSS selector for the shadow host element.
            shadow_selector: CSS selector within the shadow root.

        Returns:
            The element inside the shadow root.
        """
        return self.driver.execute_script(
            "return document.querySelector(arguments[0])"
            ".shadowRoot.querySelector(arguments[1])",
            host_selector,
            shadow_selector,
        )

    def navigate_to_object(self, object_name: str):
        """Navigate to a Salesforce object tab."""
        self.driver.get(f"{self.base_url}/lightning/o/{object_name}/list")
        self.wait_for_lightning_ready()

    def navigate_to_record(self, record_id: str):
        """Navigate to a specific Salesforce record."""
        self.driver.get(f"{self.base_url}/lightning/r/{record_id}/view")
        self.wait_for_lightning_ready()

    def open_app_launcher(self):
        """Open the Salesforce App Launcher."""
        self.click(self.APP_LAUNCHER)
        time.sleep(1)

    def search_app_launcher(self, app_name: str):
        """Search for an app in the App Launcher."""
        self.open_app_launcher()
        search_input = self.find(Locator(
            "app_search", "css",
            "input.slds-input[placeholder*='Search'], one-app-launcher-search-bar input"
        ))
        search_input.send_keys(app_name)
        time.sleep(1)

    def get_toast_message(self) -> str:
        """Get the toast notification message text."""
        if self.is_visible(self.TOAST_MESSAGE, timeout=5):
            return self.get_text(self.TOAST_MESSAGE)
        return ""

    def is_modal_open(self) -> bool:
        """Check if a modal dialog is open."""
        return self.is_visible(self.MODAL_DIALOG, timeout=3)

    def get_record_field_value(self, field_label: str) -> str:
        """Get a field value from a record detail page."""
        xpath = (
            f"//force-record-layout-item[.//span[contains(text(), '{field_label}')]]"
            f"//lightning-formatted-text | "
            f"//records-record-layout-item[.//span[contains(text(), '{field_label}')]]"
            f"//lightning-formatted-text"
        )
        return self.get_text(Locator(f"field_{field_label}", "xpath", xpath))

    def select_list_view(self, view_name: str):
        """Select a list view by name."""
        xpath = f"//a[contains(@title, '{view_name}')] | //span[text()='{view_name}']"
        self.click(Locator(f"view_{view_name}", "xpath", xpath))
        self.wait_for_lightning_ready()


class SalesforceLoginPage(SalesforcePage):
    """Salesforce login page object."""

    USERNAME = Locator("username", "id", "username", "Username field")
    PASSWORD = Locator("password", "id", "password", "Password field")
    LOGIN_BUTTON = Locator("login", "id", "Login", "Login button")
    ERROR_MESSAGE = Locator("error", "id", "error", "Login error message")

    def login(self, username: str, password: str):
        """Login to Salesforce."""
        self.navigate("/")
        self.type_text(self.USERNAME, username)
        self.type_text(self.PASSWORD, password)
        self.click(self.LOGIN_BUTTON)
        self.wait_for_lightning_ready()


# ---------------------------------------------------------------------------
# React Application Page Objects
# ---------------------------------------------------------------------------

class ReactPage(BasePage):
    """Base page object for React applications.

    Uses React-specific selectors: data-testid, data-cy, React component
    structure, and handles SPA routing and virtual DOM updates.
    """

    ROOT = Locator("root", "id", "root", "React root element")

    def __init__(self, driver: WebDriver, base_url: str = "http://localhost:3000"):
        super().__init__(driver, base_url)

    def wait_for_react_ready(self, timeout: int = 15):
        """Wait for React application to be fully loaded."""
        WebDriverWait(self.driver, timeout).until(
            lambda d: d.execute_script(
                "return document.getElementById('root') !== null"
                " && document.getElementById('root').children.length > 0"
            )
        )

    def find_by_testid(self, testid: str, timeout: int = 10) -> WebElement:
        """Find element by data-testid attribute (React Testing Library pattern)."""
        locator = Locator(f"testid_{testid}", "css", f"[data-testid='{testid}']")
        return self.find(locator, timeout)

    def find_by_cy(self, cy_id: str, timeout: int = 10) -> WebElement:
        """Find element by data-cy attribute (Cypress pattern)."""
        locator = Locator(f"cy_{cy_id}", "css", f"[data-cy='{cy_id}']")
        return self.find(locator, timeout)

    def click_by_testid(self, testid: str):
        """Click element by data-testid."""
        locator = Locator(f"testid_{testid}", "css", f"[data-testid='{testid}']")
        self.click(locator)

    def type_by_testid(self, testid: str, text: str):
        """Type text into element by data-testid."""
        locator = Locator(f"testid_{testid}", "css", f"[data-testid='{testid}']")
        self.type_text(locator, text)

    def get_text_by_testid(self, testid: str) -> str:
        """Get text from element by data-testid."""
        locator = Locator(f"testid_{testid}", "css", f"[data-testid='{testid}']")
        return self.get_text(locator)

    def find_component(self, component_name: str) -> WebElement:
        """Find a React component by its data attribute or class."""
        selectors = [
            f"[data-component='{component_name}']",
            f"[data-react-class='{component_name}']",
            f".{component_name}",
            f"[class*='{component_name}']",
        ]
        for sel in selectors:
            try:
                return self.driver.find_element(By.CSS_SELECTOR, sel)
            except Exception:
                continue
        raise Exception(f"React component not found: {component_name}")

    def wait_for_state_update(self, timeout: float = 2.0):
        """Wait for React state update / re-render cycle."""
        time.sleep(timeout)

    def get_react_state(self, element_selector: str) -> dict:
        """Get React component state via dev tools (debug mode only)."""
        return self.driver.execute_script(f"""
            const el = document.querySelector('{element_selector}');
            if (el && el._reactInternals) {{
                const fiber = el._reactInternals;
                return fiber.memoizedState;
            }}
            return null;
        """)

    def navigate_react_route(self, route: str):
        """Navigate using React Router (SPA navigation)."""
        self.driver.execute_script(
            f"window.history.pushState(null, '', '{route}');"
            "window.dispatchEvent(new PopStateEvent('popstate'));"
        )
        time.sleep(0.5)

    def is_component_rendered(self, testid: str, timeout: int = 5) -> bool:
        """Check if a React component is rendered."""
        return self.is_present(
            Locator(f"testid_{testid}", "css", f"[data-testid='{testid}']"),
            timeout,
        )


class ReactFormPage(ReactPage):
    """Page Object for React form components."""

    def fill_form_by_testid(self, field_map: dict[str, str]):
        """Fill form fields using data-testid attributes.

        Args:
            field_map: Dict of testid -> value.
        """
        for testid, value in field_map.items():
            self.type_by_testid(testid, value)

    def submit_form(self, submit_testid: str = "submit-button"):
        """Submit a React form."""
        self.click_by_testid(submit_testid)
        self.wait_for_state_update()

    def get_validation_errors(self, error_testid: str = "error-message") -> list[str]:
        """Get validation error messages."""
        elements = self.driver.find_elements(
            By.CSS_SELECTOR, f"[data-testid='{error_testid}'], .error-message, .validation-error"
        )
        return [e.text for e in elements if e.text]

    def select_dropdown(self, testid: str, value: str):
        """Select a React dropdown/select option."""
        self.click_by_testid(testid)
        time.sleep(0.3)
        option = Locator("option", "xpath", f"//*[contains(text(), '{value}')]")
        self.click(option)


class ReactTablePage(ReactPage):
    """Page Object for React table/list components."""

    def get_table_rows(self, table_testid: str = "data-table") -> list[WebElement]:
        """Get all rows in a React table."""
        return self.driver.find_elements(
            By.CSS_SELECTOR,
            f"[data-testid='{table_testid}'] tbody tr, [data-testid='{table_testid}'] [role='row']"
        )

    def get_row_count(self, table_testid: str = "data-table") -> int:
        """Get number of rows."""
        return len(self.get_table_rows(table_testid))

    def search_table(self, search_testid: str, term: str):
        """Search in a React table."""
        self.type_by_testid(search_testid, term)
        self.wait_for_state_update()

    def click_row_action(self, row_index: int, action_testid: str):
        """Click an action button in a specific table row."""
        rows = self.get_table_rows()
        if row_index < len(rows):
            action = rows[row_index].find_element(
                By.CSS_SELECTOR, f"[data-testid='{action_testid}']"
            )
            action.click()


# ---------------------------------------------------------------------------
# Angular Application Page Objects
# ---------------------------------------------------------------------------

class AngularPage(BasePage):
    """Base page object for Angular applications.

    Handles Angular-specific patterns: ng-model, ng-click, Angular Material
    components, and Angular routing.
    """

    APP_ROOT = Locator("app_root", "css", "app-root, [ng-app]", "Angular app root")

    def __init__(self, driver: WebDriver, base_url: str = "http://localhost:4200"):
        super().__init__(driver, base_url)

    def wait_for_angular_ready(self, timeout: int = 15):
        """Wait for Angular to finish rendering."""
        WebDriverWait(self.driver, timeout).until(
            lambda d: d.execute_script(
                "if (window.getAllAngularTestabilities) {"
                "  return window.getAllAngularTestabilities()"
                "    .every(t => t.isStable());"
                "} else if (window.angular) {"
                "  return true;"
                "} else {"
                "  return document.querySelector('app-root') !== null;"
                "}"
            )
        )

    def find_by_ng_model(self, model: str) -> WebElement:
        """Find element by ng-model attribute (AngularJS)."""
        locator = Locator(f"ngmodel_{model}", "css", f"[ng-model='{model}']")
        return self.find(locator)

    def find_by_ng_bind(self, bind: str) -> WebElement:
        """Find element by ng-bind attribute."""
        locator = Locator(f"ngbind_{bind}", "css", f"[ng-bind='{bind}']")
        return self.find(locator)

    def find_by_formcontrol(self, control_name: str) -> WebElement:
        """Find element by formControlName (Angular Reactive Forms)."""
        locator = Locator(
            f"formcontrol_{control_name}", "css",
            f"[formControlName='{control_name}'], [formcontrolname='{control_name}']"
        )
        return self.find(locator)

    def type_by_formcontrol(self, control_name: str, text: str):
        """Type into an Angular Reactive Form control."""
        locator = Locator(
            f"formcontrol_{control_name}", "css",
            f"[formControlName='{control_name}'], [formcontrolname='{control_name}']"
        )
        self.type_text(locator, text)

    def find_component(self, component_selector: str) -> WebElement:
        """Find an Angular component by its selector."""
        return self.find(Locator(f"component_{component_selector}", "css", component_selector))

    def click_mat_button(self, label: str):
        """Click an Angular Material button."""
        xpath = (
            f"//button[contains(@class, 'mat-button') and contains(text(), '{label}')]"
            f" | //button[contains(@class, 'mat-raised-button') and contains(text(), '{label}')]"
            f" | //button[contains(@class, 'mat-flat-button') and contains(text(), '{label}')]"
        )
        self.click(Locator(f"mat_button_{label}", "xpath", xpath))

    def type_mat_input(self, label: str, text: str):
        """Type into an Angular Material input field."""
        xpath = (
            f"//mat-form-field[.//mat-label[contains(text(), '{label}')]]//input"
            f" | //mat-form-field[.//mat-label[contains(text(), '{label}')]]//textarea"
        )
        self.type_text(Locator(f"mat_input_{label}", "xpath", xpath), text)

    def select_mat_option(self, select_label: str, option_text: str):
        """Select an option from an Angular Material select/dropdown."""
        select_xpath = (
            f"//mat-form-field[.//mat-label[contains(text(), '{select_label}')]]//mat-select"
        )
        self.click(Locator(f"mat_select_{select_label}", "xpath", select_xpath))
        time.sleep(0.3)
        option_xpath = f"//mat-option[.//span[contains(text(), '{option_text}')]]"
        self.click(Locator(f"mat_option_{option_text}", "xpath", option_xpath))

    def get_mat_error(self) -> str:
        """Get Angular Material form error message."""
        locator = Locator("mat_error", "css", "mat-error")
        if self.is_visible(locator, timeout=3):
            return self.get_text(locator)
        return ""

    def toggle_mat_checkbox(self, label: str):
        """Toggle an Angular Material checkbox."""
        xpath = f"//mat-checkbox[.//span[contains(text(), '{label}')]]"
        self.click(Locator(f"mat_checkbox_{label}", "xpath", xpath))

    def toggle_mat_slide_toggle(self, label: str):
        """Toggle an Angular Material slide toggle."""
        xpath = f"//mat-slide-toggle[.//span[contains(text(), '{label}')]]"
        self.click(Locator(f"mat_toggle_{label}", "xpath", xpath))

    def get_mat_table_rows(self) -> list[WebElement]:
        """Get all rows in an Angular Material table."""
        return self.find_all(Locator("mat_rows", "css", "mat-row, tr.mat-row"))

    def get_mat_table_row_count(self) -> int:
        """Get number of rows in Angular Material table."""
        return len(self.get_mat_table_rows())

    def get_mat_snackbar_text(self) -> str:
        """Get Angular Material snackbar text."""
        locator = Locator("snackbar", "css", "simple-snack-bar, mat-snack-bar-container")
        if self.is_visible(locator, timeout=5):
            return self.get_text(locator)
        return ""

    def navigate_angular_route(self, route: str):
        """Navigate using Angular Router."""
        self.driver.get(f"{self.base_url}/{route.lstrip('/')}")
        self.wait_for_angular_ready()

    def wait_for_http_complete(self, timeout: int = 10):
        """Wait for Angular HTTP requests to complete."""
        WebDriverWait(self.driver, timeout).until(
            lambda d: d.execute_script(
                "if (window.getAllAngularTestabilities) {"
                "  return window.getAllAngularTestabilities()"
                "    .every(t => t.isStable());"
                "} return true;"
            )
        )

    def click_by_ng_click(self, expression: str):
        """Click element by ng-click attribute (AngularJS)."""
        locator = Locator(f"ngclick_{expression}", "css", f"[ng-click='{expression}']")
        self.click(locator)

    def is_ng_show_visible(self, expression: str) -> bool:
        """Check if ng-show element is visible."""
        locator = Locator(f"ngshow_{expression}", "css", f"[ng-show='{expression}']")
        return self.is_visible(locator)


class AngularFormPage(AngularPage):
    """Page Object for Angular form pages."""

    FORM = Locator("form", "css", "form", "Angular form")
    SUBMIT_BUTTON = Locator(
        "submit", "css",
        "button[type='submit'], button.mat-raised-button[type='submit']",
        "Submit button"
    )

    def fill_reactive_form(self, field_map: dict[str, str]):
        """Fill Angular Reactive Form fields.

        Args:
            field_map: Dict of formControlName -> value.
        """
        for control, value in field_map.items():
            self.type_by_formcontrol(control, value)

    def fill_material_form(self, field_map: dict[str, str]):
        """Fill Angular Material form fields by label.

        Args:
            field_map: Dict of label -> value.
        """
        for label, value in field_map.items():
            self.type_mat_input(label, value)

    def submit(self):
        """Submit the Angular form."""
        self.click(self.SUBMIT_BUTTON)
        self.wait_for_angular_ready()

    def has_form_errors(self) -> bool:
        """Check if form has validation errors."""
        return self.is_present(Locator("error", "css", "mat-error, .ng-invalid.ng-touched"), timeout=2)
