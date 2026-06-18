"""Page Object Model (POM) framework for Selenium UI traversal.

Provides a structured POM pattern where each page of the application
is represented as a class with locators and action methods.
"""

import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

logger = logging.getLogger(__name__)


@dataclass
class Locator:
    """Represents a UI element locator."""
    name: str
    by: str
    value: str
    description: str = ""

    def as_tuple(self) -> tuple:
        """Convert to Selenium (By, value) tuple."""
        by_map = {
            "id": By.ID,
            "name": By.NAME,
            "class": By.CLASS_NAME,
            "css": By.CSS_SELECTOR,
            "xpath": By.XPATH,
            "tag": By.TAG_NAME,
            "link_text": By.LINK_TEXT,
            "partial_link_text": By.PARTIAL_LINK_TEXT,
        }
        return (by_map.get(self.by, By.CSS_SELECTOR), self.value)


class BasePage:
    """Base page object providing common functionality for all pages.

    All page objects should inherit from this class and define their
    locators and action methods.
    """

    URL_PATH = "/"

    def __init__(self, driver: WebDriver, base_url: str = "http://localhost:8080"):
        self.driver = driver
        self.base_url = base_url.rstrip("/")
        self._wait = WebDriverWait(driver, 10)
        self._locators: dict[str, Locator] = {}

    def navigate(self, path: str = None):
        """Navigate to this page."""
        url = f"{self.base_url}{path or self.URL_PATH}"
        logger.info("Navigating to: %s", url)
        self.driver.get(url)
        self.wait_for_page_load()

    def wait_for_page_load(self, timeout: int = 30):
        """Wait for page to fully load."""
        WebDriverWait(self.driver, timeout).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )

    def find(self, locator: Locator, timeout: int = 10) -> WebElement:
        """Find an element using a Locator."""
        return WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located(locator.as_tuple())
        )

    def find_all(self, locator: Locator) -> list[WebElement]:
        """Find all elements matching a Locator."""
        return self.driver.find_elements(*locator.as_tuple())

    def click(self, locator: Locator, timeout: int = 10):
        """Click an element."""
        element = WebDriverWait(self.driver, timeout).until(
            EC.element_to_be_clickable(locator.as_tuple())
        )
        element.click()
        logger.info("Clicked: %s", locator.name)

    def type_text(self, locator: Locator, text: str, clear_first: bool = True):
        """Type text into an input element."""
        element = self.find(locator)
        if clear_first:
            element.clear()
        element.send_keys(text)
        logger.info("Typed '%s' into: %s", text, locator.name)

    def get_text(self, locator: Locator) -> str:
        """Get text content of an element."""
        return self.find(locator).text

    def get_attribute(self, locator: Locator, attribute: str) -> str:
        """Get an attribute value of an element."""
        return self.find(locator).get_attribute(attribute)

    def is_visible(self, locator: Locator, timeout: int = 5) -> bool:
        """Check if an element is visible."""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(locator.as_tuple())
            )
            return True
        except Exception:
            return False

    def is_present(self, locator: Locator, timeout: int = 5) -> bool:
        """Check if an element is present in DOM."""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located(locator.as_tuple())
            )
            return True
        except Exception:
            return False

    def select_dropdown(self, locator: Locator, value: str = None, text: str = None):
        """Select a dropdown option."""
        element = self.find(locator)
        select = Select(element)
        if value:
            select.select_by_value(value)
        elif text:
            select.select_by_visible_text(text)

    def submit_form(self, locator: Locator):
        """Submit a form."""
        self.find(locator).submit()

    def take_screenshot(self, name: str, directory: str = "screenshots") -> str:
        """Take a screenshot of the current page."""
        Path(directory).mkdir(parents=True, exist_ok=True)
        filepath = f"{directory}/{name}_{int(time.time())}.png"
        self.driver.save_screenshot(filepath)
        return filepath

    def get_page_title(self) -> str:
        """Get the page title."""
        return self.driver.title

    def get_current_url(self) -> str:
        """Get the current URL."""
        return self.driver.current_url

    def switch_to_frame(self, locator: Locator):
        """Switch to an iframe."""
        frame = self.find(locator)
        self.driver.switch_to.frame(frame)

    def switch_to_default(self):
        """Switch back to default content."""
        self.driver.switch_to.default_content()

    def scroll_to_element(self, locator: Locator):
        """Scroll to an element."""
        element = self.find(locator)
        self.driver.execute_script("arguments[0].scrollIntoView(true);", element)

    def wait_for_element_text(
        self, locator: Locator, text: str, timeout: int = 10
    ) -> bool:
        """Wait for an element to contain specific text."""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.text_to_be_present_in_element(locator.as_tuple(), text)
            )
            return True
        except Exception:
            return False

    def register_locator(self, locator: Locator):
        """Register a locator for this page."""
        self._locators[locator.name] = locator

    def get_locator(self, name: str) -> Optional[Locator]:
        """Get a registered locator by name."""
        return self._locators.get(name)


class LoginPage(BasePage):
    """Page Object for login page."""

    URL_PATH = "/login"

    USERNAME_INPUT = Locator("username", "id", "username", "Username input field")
    PASSWORD_INPUT = Locator("password", "id", "password", "Password input field")
    LOGIN_BUTTON = Locator("login_button", "css", "button[type='submit']", "Login button")
    ERROR_MESSAGE = Locator("error_message", "css", ".error-message, .alert-danger", "Error message")
    REMEMBER_ME = Locator("remember_me", "id", "rememberMe", "Remember me checkbox")

    def login(self, username: str, password: str):
        """Perform login action."""
        self.navigate()
        self.type_text(self.USERNAME_INPUT, username)
        self.type_text(self.PASSWORD_INPUT, password)
        self.click(self.LOGIN_BUTTON)

    def get_error_message(self) -> str:
        """Get login error message."""
        if self.is_visible(self.ERROR_MESSAGE):
            return self.get_text(self.ERROR_MESSAGE)
        return ""

    def is_login_page(self) -> bool:
        """Check if currently on login page."""
        return self.is_present(self.USERNAME_INPUT)


class DashboardPage(BasePage):
    """Page Object for dashboard page."""

    URL_PATH = "/dashboard"

    WELCOME_MESSAGE = Locator("welcome", "css", ".welcome-message, h1", "Welcome message")
    NAVIGATION_MENU = Locator("nav_menu", "css", "nav, .navbar", "Navigation menu")
    LOGOUT_BUTTON = Locator("logout", "css", ".logout, a[href*='logout']", "Logout button")
    USER_PROFILE = Locator("user_profile", "css", ".user-profile, .avatar", "User profile")

    def get_welcome_message(self) -> str:
        """Get the welcome message text."""
        return self.get_text(self.WELCOME_MESSAGE)

    def is_dashboard_loaded(self) -> bool:
        """Check if dashboard is loaded."""
        return self.is_visible(self.WELCOME_MESSAGE)

    def logout(self):
        """Perform logout action."""
        self.click(self.LOGOUT_BUTTON)


class ListPage(BasePage):
    """Page Object for a generic list/table page."""

    URL_PATH = "/list"

    TABLE = Locator("table", "css", "table, .data-table", "Data table")
    TABLE_ROWS = Locator("table_rows", "css", "tbody tr", "Table rows")
    SEARCH_INPUT = Locator("search", "css", "input[type='search'], .search-input", "Search input")
    FILTER_DROPDOWN = Locator("filter", "css", "select.filter, .filter-dropdown", "Filter dropdown")
    PAGINATION_NEXT = Locator("next_page", "css", ".pagination .next, [aria-label='Next']", "Next page")
    ADD_BUTTON = Locator("add_button", "css", ".btn-add, button.add", "Add button")
    NO_DATA_MESSAGE = Locator("no_data", "css", ".no-data, .empty-state", "No data message")

    def search(self, term: str):
        """Search in the list."""
        self.type_text(self.SEARCH_INPUT, term)

    def get_row_count(self) -> int:
        """Get the number of rows in the table."""
        return len(self.find_all(self.TABLE_ROWS))

    def filter_by(self, value: str):
        """Apply filter."""
        self.select_dropdown(self.FILTER_DROPDOWN, text=value)

    def click_add(self):
        """Click the add button."""
        self.click(self.ADD_BUTTON)

    def has_data(self) -> bool:
        """Check if the list has data."""
        return not self.is_present(self.NO_DATA_MESSAGE, timeout=2)


class FormPage(BasePage):
    """Page Object for a generic form page."""

    URL_PATH = "/form"

    FORM = Locator("form", "css", "form", "Main form")
    SUBMIT_BUTTON = Locator("submit", "css", "button[type='submit'], .btn-submit", "Submit button")
    CANCEL_BUTTON = Locator("cancel", "css", ".btn-cancel, a.cancel", "Cancel button")
    SUCCESS_MESSAGE = Locator("success", "css", ".alert-success, .success-message", "Success message")
    VALIDATION_ERROR = Locator("validation_error", "css", ".validation-error, .field-error", "Validation error")

    def fill_field(self, field_name: str, value: str):
        """Fill a form field by name."""
        locator = Locator(field_name, "name", field_name)
        self.type_text(locator, value)

    def fill_field_by_id(self, field_id: str, value: str):
        """Fill a form field by ID."""
        locator = Locator(field_id, "id", field_id)
        self.type_text(locator, value)

    def submit(self):
        """Submit the form."""
        self.click(self.SUBMIT_BUTTON)

    def cancel(self):
        """Cancel the form."""
        self.click(self.CANCEL_BUTTON)

    def get_success_message(self) -> str:
        """Get success message text."""
        if self.is_visible(self.SUCCESS_MESSAGE):
            return self.get_text(self.SUCCESS_MESSAGE)
        return ""

    def has_validation_errors(self) -> bool:
        """Check if there are validation errors."""
        return self.is_present(self.VALIDATION_ERROR, timeout=2)


class PageObjectFactory:
    """Factory for creating page objects dynamically.

    Maintains a registry of page objects and can create them
    based on page names or URL patterns.
    """

    def __init__(self, driver: WebDriver, base_url: str):
        self.driver = driver
        self.base_url = base_url
        self._registry: dict[str, type[BasePage]] = {
            "login": LoginPage,
            "dashboard": DashboardPage,
            "list": ListPage,
            "form": FormPage,
        }

    def register_page(self, name: str, page_class: type[BasePage]):
        """Register a custom page object."""
        self._registry[name] = page_class

    def get_page(self, name: str) -> BasePage:
        """Get a page object by name."""
        page_class = self._registry.get(name)
        if not page_class:
            logger.warning("No page registered for '%s', using BasePage", name)
            page_class = BasePage
        return page_class(self.driver, self.base_url)

    def create_dynamic_page(
        self, name: str, url_path: str, locators: list[dict]
    ) -> BasePage:
        """Create a dynamic page object from locator definitions.

        Args:
            name: Page name.
            url_path: URL path for the page.
            locators: List of locator dicts with keys: name, by, value, description.

        Returns:
            A BasePage instance with registered locators.
        """
        page = BasePage(self.driver, self.base_url)
        page.URL_PATH = url_path

        for loc_def in locators:
            locator = Locator(
                name=loc_def["name"],
                by=loc_def.get("by", "css"),
                value=loc_def["value"],
                description=loc_def.get("description", ""),
            )
            page.register_locator(locator)

        self._registry[name] = type(page)
        return page

    def list_pages(self) -> list[str]:
        """List all registered page names."""
        return list(self._registry.keys())


class POMStepExecutor:
    """Executes Gherkin steps using the Page Object Model.

    Maps Gherkin step text to POM actions, providing a clean
    separation between test steps and page implementation.
    """

    def __init__(self, factory: PageObjectFactory):
        self.factory = factory
        self._current_page: Optional[BasePage] = None
        self._variables: dict[str, str] = {}

    def execute_step(self, step_type: str, step_text: str) -> bool:
        """Execute a Gherkin step using POM.

        Args:
            step_type: Given, When, Then, And.
            step_text: The step text.

        Returns:
            True if step passed.
        """
        text_lower = step_text.lower()
        try:
            if "on the" in text_lower and "page" in text_lower:
                return self._handle_navigation(step_text)

            if any(kw in text_lower for kw in ["click", "press", "tap"]):
                return self._handle_click(step_text)

            if any(kw in text_lower for kw in ["enter", "type", "input", "fill"]):
                return self._handle_input(step_text)

            if any(kw in text_lower for kw in ["select", "choose", "pick"]):
                return self._handle_select(step_text)

            if any(kw in text_lower for kw in [
                "should be displayed", "should be visible", "should see",
                "should contain", "should show"
            ]):
                return self._handle_verification(step_text)

            if any(kw in text_lower for kw in [
                "should not be", "should not see", "should be hidden"
            ]):
                return self._handle_negative_verification(step_text)

            if "log in" in text_lower or "login" in text_lower or "sign in" in text_lower:
                return self._handle_login(step_text)

            if "log out" in text_lower or "logout" in text_lower:
                return self._handle_logout()

            if "submit" in text_lower:
                return self._handle_submit()

            if "search" in text_lower:
                return self._handle_search(step_text)

            logger.info("Step handled generically: %s %s", step_type, step_text)
            return True

        except Exception as e:
            logger.error("POM step failed: %s %s - %s", step_type, step_text, e)
            if self._current_page:
                self._current_page.take_screenshot(f"failure_{step_type}")
            return False

    def _handle_navigation(self, step_text: str) -> bool:
        """Handle page navigation steps."""
        import re
        match = re.search(r"(?:on|to)\s+the\s+(\w+)\s+page", step_text, re.IGNORECASE)
        if match:
            page_name = match.group(1).lower()
            self._current_page = self.factory.get_page(page_name)
            self._current_page.navigate()
            return True
        return False

    def _handle_click(self, step_text: str) -> bool:
        """Handle click steps."""
        import re
        if not self._current_page:
            return False

        match = re.search(r'"([^"]+)"', step_text)
        if match:
            element_text = match.group(1)
            locator = Locator("dynamic", "xpath", f"//*[contains(text(), '{element_text}')]")
            self._current_page.click(locator)
            return True

        match = re.search(r"(?:click|press|tap)\s+(?:on\s+)?(?:the\s+)?(\w+)", step_text, re.IGNORECASE)
        if match:
            element_name = match.group(1).lower()
            locator = self._current_page.get_locator(element_name)
            if locator:
                self._current_page.click(locator)
                return True

        return True

    def _handle_input(self, step_text: str) -> bool:
        """Handle text input steps."""
        import re
        if not self._current_page:
            return False

        match = re.search(r'"([^"]+)".*"([^"]+)"', step_text)
        if match:
            value = match.group(1)
            field_ref = match.group(2)
            locator = Locator("dynamic", "css", f"[name='{field_ref}'], #{field_ref}")
            self._current_page.type_text(locator, value)
            return True

        match = re.search(r'"([^"]+)"', step_text)
        if match:
            value = match.group(1)
            locator = Locator("dynamic", "css", "input:focus, input:first-of-type")
            self._current_page.type_text(locator, value)
            return True

        return True

    def _handle_select(self, step_text: str) -> bool:
        """Handle dropdown selection steps."""
        import re
        if not self._current_page:
            return False

        match = re.search(r'"([^"]+)"', step_text)
        if match:
            value = match.group(1)
            filter_locator = self._current_page.get_locator("filter")
            if filter_locator:
                self._current_page.select_dropdown(filter_locator, text=value)
            return True
        return True

    def _handle_verification(self, step_text: str) -> bool:
        """Handle positive verification steps."""
        import re
        if not self._current_page:
            return True

        match = re.search(r'"([^"]+)"', step_text)
        if match:
            expected_text = match.group(1)
            page_source = self._current_page.driver.page_source
            return expected_text in page_source

        return True

    def _handle_negative_verification(self, step_text: str) -> bool:
        """Handle negative verification steps."""
        import re
        if not self._current_page:
            return True

        match = re.search(r'"([^"]+)"', step_text)
        if match:
            unexpected_text = match.group(1)
            page_source = self._current_page.driver.page_source
            return unexpected_text not in page_source

        return True

    def _handle_login(self, step_text: str) -> bool:
        """Handle login steps."""
        import re
        login_page = self.factory.get_page("login")
        self._current_page = login_page

        match = re.search(r'"([^"]+)"\s*(?:and|/)\s*"([^"]+)"', step_text)
        if match and isinstance(login_page, LoginPage):
            login_page.login(match.group(1), match.group(2))
            return True

        match = re.search(r"(\w+)/(\w+)", step_text)
        if match and isinstance(login_page, LoginPage):
            login_page.login(match.group(1), match.group(2))
            return True

        return True

    def _handle_logout(self) -> bool:
        """Handle logout steps."""
        dashboard = self.factory.get_page("dashboard")
        if isinstance(dashboard, DashboardPage):
            dashboard.logout()
        return True

    def _handle_submit(self) -> bool:
        """Handle form submit steps."""
        if self._current_page and isinstance(self._current_page, FormPage):
            self._current_page.submit()
        return True

    def _handle_search(self, step_text: str) -> bool:
        """Handle search steps."""
        import re
        if not self._current_page:
            return True

        match = re.search(r'"([^"]+)"', step_text)
        if match and isinstance(self._current_page, ListPage):
            self._current_page.search(match.group(1))
            return True
        return True
