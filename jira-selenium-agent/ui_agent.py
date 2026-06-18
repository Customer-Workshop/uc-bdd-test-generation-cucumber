"""Unified UI Agent for multi-framework Selenium testing.

Auto-detects the UI framework (Salesforce, React, Angular) and uses
the appropriate Page Object Model for test execution.
"""

import logging
import re
import time
from typing import Optional

from selenium.webdriver.remote.webdriver import WebDriver

from page_object_model import BasePage, Locator, PageObjectFactory
from ui_framework_pages import (
    AngularFormPage,
    AngularPage,
    ReactFormPage,
    ReactPage,
    ReactTablePage,
    SalesforceLoginPage,
    SalesforcePage,
    UIFramework,
)

logger = logging.getLogger(__name__)


class UIFrameworkDetector:
    """Detects which UI framework the target application uses."""

    def __init__(self, driver: WebDriver):
        self.driver = driver

    def detect(self, url: str = None) -> UIFramework:
        """Detect the UI framework of the current or given page.

        Args:
            url: Optional URL to navigate to before detection.

        Returns:
            Detected UIFramework enum value.
        """
        if url:
            self.driver.get(url)
            time.sleep(3)

        if self._is_salesforce():
            logger.info("Detected UI framework: Salesforce Lightning")
            return UIFramework.SALESFORCE

        if self._is_react():
            logger.info("Detected UI framework: React")
            return UIFramework.REACT

        if self._is_angular():
            logger.info("Detected UI framework: Angular")
            return UIFramework.ANGULAR

        logger.info("No specific framework detected, using generic selectors")
        return UIFramework.GENERIC

    def _is_salesforce(self) -> bool:
        """Detect Salesforce Lightning / Aura / LWC."""
        checks = [
            "return typeof $A !== 'undefined'",
            "return document.querySelector('lightning-app') !== null",
            "return document.querySelector('one-app') !== null",
            "return document.querySelector('aura-component') !== null",
            "return window.location.host.includes('.force.com') || window.location.host.includes('.salesforce.com') || window.location.host.includes('.lightning.force.com')",
        ]
        for check in checks:
            try:
                if self.driver.execute_script(check):
                    return True
            except Exception:
                pass
        return False

    def _is_react(self) -> bool:
        """Detect React application."""
        checks = [
            "return document.getElementById('root') !== null && document.getElementById('root')._reactRootContainer !== undefined",
            "return document.querySelector('[data-reactroot]') !== null",
            "return typeof __REACT_DEVTOOLS_GLOBAL_HOOK__ !== 'undefined'",
            "return document.querySelector('[data-testid]') !== null && document.getElementById('root') !== null",
        ]
        for check in checks:
            try:
                if self.driver.execute_script(check):
                    return True
            except Exception:
                pass
        return False

    def _is_angular(self) -> bool:
        """Detect Angular application."""
        checks = [
            "return window.getAllAngularTestabilities !== undefined",
            "return document.querySelector('app-root') !== null",
            "return document.querySelector('[ng-app]') !== null",
            "return typeof window.ng !== 'undefined'",
            "return document.querySelector('[_nghost]') !== null || document.querySelector('[ng-version]') !== null",
        ]
        for check in checks:
            try:
                if self.driver.execute_script(check):
                    return True
            except Exception:
                pass
        return False


class UIAgent:
    """Unified UI Agent that handles Salesforce, React, and Angular applications.

    Auto-detects the UI framework and uses appropriate POM for test execution.
    Maps Gherkin steps to framework-specific Selenium actions.
    """

    def __init__(self, driver: WebDriver, base_url: str = ""):
        self.driver = driver
        self.base_url = base_url
        self.detector = UIFrameworkDetector(driver)
        self.framework: UIFramework = UIFramework.GENERIC
        self._current_page: Optional[BasePage] = None
        self._variables: dict[str, str] = {}

    def detect_and_setup(self, url: str = None) -> UIFramework:
        """Detect the framework and set up appropriate page objects.

        Args:
            url: Optional URL to navigate to.

        Returns:
            Detected UIFramework.
        """
        self.framework = self.detector.detect(url)
        logger.info("UI Agent initialized for framework: %s", self.framework.value)
        return self.framework

    def get_page(self, page_type: str = "base") -> BasePage:
        """Get a page object appropriate for the detected framework.

        Args:
            page_type: Type of page (login, form, list, dashboard, base).

        Returns:
            Framework-specific page object.
        """
        if self.framework == UIFramework.SALESFORCE:
            return self._get_salesforce_page(page_type)
        elif self.framework == UIFramework.REACT:
            return self._get_react_page(page_type)
        elif self.framework == UIFramework.ANGULAR:
            return self._get_angular_page(page_type)
        else:
            return BasePage(self.driver, self.base_url)

    def execute_step(self, step_type: str, step_text: str) -> bool:
        """Execute a Gherkin step using framework-appropriate actions.

        Args:
            step_type: Given, When, Then, And.
            step_text: The step text.

        Returns:
            True if step passed.
        """
        text_lower = step_text.lower()

        try:
            if "navigate" in text_lower or "open" in text_lower or "go to" in text_lower:
                return self._handle_navigation(step_text)

            if "login" in text_lower or "log in" in text_lower or "sign in" in text_lower:
                return self._handle_login(step_text)

            if any(kw in text_lower for kw in ["click", "press", "tap"]):
                return self._handle_click(step_text)

            if any(kw in text_lower for kw in ["enter", "type", "input", "fill", "set"]):
                return self._handle_input(step_text)

            if any(kw in text_lower for kw in ["select", "choose", "pick"]):
                return self._handle_select(step_text)

            if "submit" in text_lower:
                return self._handle_submit(step_text)

            if "search" in text_lower:
                return self._handle_search(step_text)

            if any(kw in text_lower for kw in [
                "should be displayed", "should be visible", "should see",
                "should contain", "should show", "should appear",
                "is displayed", "is visible"
            ]):
                return self._handle_positive_assertion(step_text)

            if any(kw in text_lower for kw in [
                "should not", "should be hidden", "should disappear",
                "is not visible", "is not displayed"
            ]):
                return self._handle_negative_assertion(step_text)

            if any(kw in text_lower for kw in ["error", "validation", "invalid"]):
                return self._handle_error_check(step_text)

            if any(kw in text_lower for kw in ["wait", "loading", "spinner"]):
                return self._handle_wait(step_text)

            logger.info("Step handled generically: %s %s", step_type, step_text)
            return True

        except Exception as e:
            logger.error("UI step failed [%s]: %s %s - %s", self.framework.value, step_type, step_text, e)
            if self._current_page:
                self._current_page.take_screenshot(f"failure_{step_type}_{self.framework.value}")
            return False

    def _handle_navigation(self, step_text: str) -> bool:
        """Handle navigation steps across frameworks."""
        url = self._extract_quoted_value(step_text) or self._extract_url(step_text)

        if self.framework == UIFramework.SALESFORCE:
            page = SalesforcePage(self.driver, self.base_url)
            if url:
                if "/" not in url and not url.startswith("http"):
                    page.navigate_to_object(url)
                else:
                    page.navigate(url)
            page.wait_for_lightning_ready()
            self._current_page = page

        elif self.framework == UIFramework.REACT:
            page = ReactPage(self.driver, self.base_url)
            if url:
                page.navigate_react_route(url)
            else:
                page.navigate()
            page.wait_for_react_ready()
            self._current_page = page

        elif self.framework == UIFramework.ANGULAR:
            page = AngularPage(self.driver, self.base_url)
            if url:
                page.navigate_angular_route(url)
            else:
                page.navigate()
            page.wait_for_angular_ready()
            self._current_page = page

        else:
            page = BasePage(self.driver, self.base_url)
            page.navigate(url or "/")
            self._current_page = page

        return True

    def _handle_login(self, step_text: str) -> bool:
        """Handle login across frameworks."""
        creds = re.findall(r'"([^"]+)"', step_text)
        username = creds[0] if len(creds) > 0 else ""
        password = creds[1] if len(creds) > 1 else ""

        if not username:
            match = re.search(r"(\w+)/(\w+)", step_text)
            if match:
                username, password = match.group(1), match.group(2)

        if self.framework == UIFramework.SALESFORCE:
            page = SalesforceLoginPage(self.driver, self.base_url)
            page.login(username, password)
            self._current_page = page

        elif self.framework == UIFramework.REACT:
            page = ReactFormPage(self.driver, self.base_url)
            page.navigate("/login")
            page.wait_for_react_ready()
            try:
                page.type_by_testid("username", username)
                page.type_by_testid("password", password)
                page.click_by_testid("login-button")
            except Exception:
                page.type_text(Locator("user", "css", "input[type='text'], input[name='username'], #username"), username)
                page.type_text(Locator("pass", "css", "input[type='password'], input[name='password'], #password"), password)
                page.click(Locator("submit", "css", "button[type='submit']"))
            self._current_page = page

        elif self.framework == UIFramework.ANGULAR:
            page = AngularFormPage(self.driver, self.base_url)
            page.navigate_angular_route("/login")
            page.wait_for_angular_ready()
            try:
                page.type_by_formcontrol("username", username)
                page.type_by_formcontrol("password", password)
                page.submit()
            except Exception:
                page.type_mat_input("Username", username)
                page.type_mat_input("Password", password)
                page.click_mat_button("Login")
            self._current_page = page

        else:
            page = BasePage(self.driver, self.base_url)
            page.navigate("/login")
            page.type_text(Locator("user", "css", "#username, input[name='username']"), username)
            page.type_text(Locator("pass", "css", "#password, input[name='password']"), password)
            page.click(Locator("submit", "css", "button[type='submit']"))
            self._current_page = page

        return True

    def _handle_click(self, step_text: str) -> bool:
        """Handle click actions across frameworks."""
        target = self._extract_quoted_value(step_text)
        if not self._current_page:
            self._current_page = self.get_page()

        if self.framework == UIFramework.SALESFORCE:
            sf_page = SalesforcePage(self.driver, self.base_url)
            sf_page.click_lightning_button(target or "Submit")

        elif self.framework == UIFramework.REACT:
            if target:
                try:
                    ReactPage(self.driver, self.base_url).click_by_testid(
                        target.lower().replace(" ", "-")
                    )
                except Exception:
                    self._current_page.click(
                        Locator("dynamic", "xpath", f"//*[contains(text(), '{target}')]")
                    )

        elif self.framework == UIFramework.ANGULAR:
            if target:
                try:
                    AngularPage(self.driver, self.base_url).click_mat_button(target)
                except Exception:
                    self._current_page.click(
                        Locator("dynamic", "xpath", f"//*[contains(text(), '{target}')]")
                    )

        else:
            if target:
                self._current_page.click(
                    Locator("dynamic", "xpath", f"//*[contains(text(), '{target}')]")
                )

        return True

    def _handle_input(self, step_text: str) -> bool:
        """Handle text input across frameworks."""
        values = re.findall(r'"([^"]+)"', step_text)
        if len(values) < 1:
            return True

        value = values[0]
        field_ref = values[1] if len(values) > 1 else ""

        if not self._current_page:
            self._current_page = self.get_page()

        if self.framework == UIFramework.SALESFORCE:
            sf_page = SalesforcePage(self.driver, self.base_url)
            sf_page.set_lightning_input(field_ref or "Input", value)

        elif self.framework == UIFramework.REACT:
            react_page = ReactPage(self.driver, self.base_url)
            if field_ref:
                testid = field_ref.lower().replace(" ", "-")
                try:
                    react_page.type_by_testid(testid, value)
                except Exception:
                    self._current_page.type_text(
                        Locator("field", "css", f"[name='{field_ref}'], #{field_ref}"), value
                    )
            else:
                self._current_page.type_text(
                    Locator("field", "css", "input:focus, input:first-of-type"), value
                )

        elif self.framework == UIFramework.ANGULAR:
            angular_page = AngularPage(self.driver, self.base_url)
            if field_ref:
                try:
                    angular_page.type_mat_input(field_ref, value)
                except Exception:
                    angular_page.type_by_formcontrol(field_ref.lower().replace(" ", ""), value)
            else:
                self._current_page.type_text(
                    Locator("field", "css", "input:focus, input:first-of-type"), value
                )

        else:
            if field_ref:
                self._current_page.type_text(
                    Locator("field", "css", f"[name='{field_ref}'], #{field_ref}"), value
                )

        return True

    def _handle_select(self, step_text: str) -> bool:
        """Handle dropdown selection across frameworks."""
        values = re.findall(r'"([^"]+)"', step_text)
        if not values:
            return True

        option = values[0]
        dropdown_ref = values[1] if len(values) > 1 else ""

        if self.framework == UIFramework.ANGULAR:
            AngularPage(self.driver, self.base_url).select_mat_option(dropdown_ref or "Select", option)
        elif self.framework == UIFramework.REACT:
            ReactFormPage(self.driver, self.base_url).select_dropdown(
                dropdown_ref.lower().replace(" ", "-") if dropdown_ref else "select", option
            )
        else:
            if self._current_page:
                self._current_page.select_dropdown(
                    Locator("select", "css", "select, [role='listbox']"), text=option
                )

        return True

    def _handle_submit(self, step_text: str) -> bool:
        """Handle form submission across frameworks."""
        if self.framework == UIFramework.SALESFORCE:
            SalesforcePage(self.driver, self.base_url).click(SalesforcePage.SAVE_BUTTON)
        elif self.framework == UIFramework.REACT:
            ReactFormPage(self.driver, self.base_url).submit_form()
        elif self.framework == UIFramework.ANGULAR:
            AngularFormPage(self.driver, self.base_url).submit()
        elif self._current_page:
            self._current_page.click(Locator("submit", "css", "button[type='submit']"))

        return True

    def _handle_search(self, step_text: str) -> bool:
        """Handle search across frameworks."""
        term = self._extract_quoted_value(step_text) or ""

        if self.framework == UIFramework.SALESFORCE:
            sf_page = SalesforcePage(self.driver, self.base_url)
            sf_page.type_text(sf_page.GLOBAL_SEARCH, term)
        elif self.framework == UIFramework.REACT:
            ReactTablePage(self.driver, self.base_url).search_table("search-input", term)
        elif self.framework == UIFramework.ANGULAR:
            AngularPage(self.driver, self.base_url).type_mat_input("Search", term)
        elif self._current_page:
            self._current_page.type_text(
                Locator("search", "css", "input[type='search'], .search-input"), term
            )

        return True

    def _handle_positive_assertion(self, step_text: str) -> bool:
        """Handle positive assertions (should be visible/contain)."""
        expected = self._extract_quoted_value(step_text)

        if expected:
            page_source = self.driver.page_source
            if expected not in page_source:
                logger.warning("Expected text not found: '%s'", expected)
                return False

        if self.framework == UIFramework.SALESFORCE:
            toast = SalesforcePage(self.driver, self.base_url).get_toast_message()
            if expected and toast and expected.lower() in toast.lower():
                return True

        return True

    def _handle_negative_assertion(self, step_text: str) -> bool:
        """Handle negative assertions (should not be visible/contain)."""
        unexpected = self._extract_quoted_value(step_text)
        if unexpected:
            page_source = self.driver.page_source
            if unexpected in page_source:
                logger.warning("Unexpected text found: '%s'", unexpected)
                return False
        return True

    def _handle_error_check(self, step_text: str) -> bool:
        """Handle error message checking across frameworks."""
        expected_error = self._extract_quoted_value(step_text)

        if self.framework == UIFramework.SALESFORCE:
            toast = SalesforcePage(self.driver, self.base_url).get_toast_message()
            if expected_error:
                return expected_error.lower() in toast.lower()

        elif self.framework == UIFramework.REACT:
            errors = ReactFormPage(self.driver, self.base_url).get_validation_errors()
            if expected_error:
                return any(expected_error.lower() in e.lower() for e in errors)
            return len(errors) > 0

        elif self.framework == UIFramework.ANGULAR:
            error = AngularPage(self.driver, self.base_url).get_mat_error()
            if expected_error:
                return expected_error.lower() in error.lower()
            return bool(error)

        return True

    def _handle_wait(self, step_text: str) -> bool:
        """Handle framework-specific waits."""
        if self.framework == UIFramework.SALESFORCE:
            SalesforcePage(self.driver, self.base_url).wait_for_lightning_ready()
        elif self.framework == UIFramework.REACT:
            ReactPage(self.driver, self.base_url).wait_for_react_ready()
        elif self.framework == UIFramework.ANGULAR:
            AngularPage(self.driver, self.base_url).wait_for_angular_ready()
        else:
            time.sleep(2)
        return True

    def _get_salesforce_page(self, page_type: str) -> BasePage:
        """Get Salesforce-specific page object."""
        pages = {
            "login": SalesforceLoginPage(self.driver, self.base_url),
            "base": SalesforcePage(self.driver, self.base_url),
        }
        return pages.get(page_type, SalesforcePage(self.driver, self.base_url))

    def _get_react_page(self, page_type: str) -> BasePage:
        """Get React-specific page object."""
        pages = {
            "form": ReactFormPage(self.driver, self.base_url),
            "table": ReactTablePage(self.driver, self.base_url),
            "list": ReactTablePage(self.driver, self.base_url),
            "base": ReactPage(self.driver, self.base_url),
        }
        return pages.get(page_type, ReactPage(self.driver, self.base_url))

    def _get_angular_page(self, page_type: str) -> BasePage:
        """Get Angular-specific page object."""
        pages = {
            "form": AngularFormPage(self.driver, self.base_url),
            "base": AngularPage(self.driver, self.base_url),
        }
        return pages.get(page_type, AngularPage(self.driver, self.base_url))

    def _extract_quoted_value(self, text: str) -> str:
        """Extract first quoted value from text."""
        match = re.search(r'"([^"]+)"', text)
        return match.group(1) if match else ""

    def _extract_url(self, text: str) -> str:
        """Extract URL from text."""
        match = re.search(r'(https?://\S+|/\S+)', text)
        return match.group(1) if match else ""
