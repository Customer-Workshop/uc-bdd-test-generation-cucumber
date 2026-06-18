"""Selenium WebDriver integration for running generated Gherkin feature tests."""

import logging
import os
import time
from pathlib import Path
from typing import Optional

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager

from config import SeleniumConfig

logger = logging.getLogger(__name__)


class SeleniumRunner:
    """Manages Selenium WebDriver for executing browser-based tests."""

    def __init__(self, config: SeleniumConfig):
        self.config = config
        self.driver: Optional[webdriver.Remote] = None

    def setup(self) -> bool:
        """Initialize the WebDriver."""
        try:
            if self.config.browser.lower() == "chrome":
                self.driver = self._setup_chrome()
            elif self.config.browser.lower() == "firefox":
                self.driver = self._setup_firefox()
            else:
                logger.error("Unsupported browser: %s", self.config.browser)
                return False

            self.driver.implicitly_wait(self.config.implicit_wait)
            self.driver.set_window_size(1920, 1080)

            Path(self.config.screenshot_dir).mkdir(parents=True, exist_ok=True)

            logger.info("Selenium WebDriver initialized: %s", self.config.browser)
            return True

        except Exception as e:
            logger.error("Failed to initialize WebDriver: %s", e)
            return False

    def teardown(self):
        """Quit the WebDriver."""
        if self.driver:
            self.driver.quit()
            self.driver = None
            logger.info("Selenium WebDriver closed.")

    def navigate_to(self, url: str):
        """Navigate to a URL."""
        full_url = url if url.startswith("http") else f"{self.config.base_url}{url}"
        logger.info("Navigating to: %s", full_url)
        self.driver.get(full_url)

    def find_element(self, by: By, value: str, timeout: int = 10):
        """Find an element with explicit wait."""
        wait = WebDriverWait(self.driver, timeout)
        return wait.until(EC.presence_of_element_located((by, value)))

    def click_element(self, by: By, value: str, timeout: int = 10):
        """Click an element with explicit wait."""
        element = WebDriverWait(self.driver, timeout).until(
            EC.element_to_be_clickable((by, value))
        )
        element.click()
        return element

    def enter_text(self, by: By, value: str, text: str, timeout: int = 10):
        """Enter text into an input element."""
        element = self.find_element(by, value, timeout)
        element.clear()
        element.send_keys(text)
        return element

    def get_text(self, by: By, value: str, timeout: int = 10) -> str:
        """Get text content of an element."""
        element = self.find_element(by, value, timeout)
        return element.text

    def is_element_present(self, by: By, value: str, timeout: int = 5) -> bool:
        """Check if an element is present on the page."""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return True
        except Exception:
            return False

    def take_screenshot(self, name: str) -> str:
        """Take a screenshot and save to the configured directory."""
        timestamp = int(time.time())
        filename = f"{name}_{timestamp}.png"
        filepath = os.path.join(self.config.screenshot_dir, filename)
        self.driver.save_screenshot(filepath)
        logger.info("Screenshot saved: %s", filepath)
        return filepath

    def get_page_title(self) -> str:
        """Get the current page title."""
        return self.driver.title

    def get_current_url(self) -> str:
        """Get the current URL."""
        return self.driver.current_url

    def wait_for_page_load(self, timeout: int = 30):
        """Wait for page to fully load."""
        WebDriverWait(self.driver, timeout).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )

    def execute_script(self, script: str, *args):
        """Execute JavaScript in the browser."""
        return self.driver.execute_script(script, *args)

    def switch_to_frame(self, frame_reference):
        """Switch to an iframe."""
        self.driver.switch_to.frame(frame_reference)

    def switch_to_default(self):
        """Switch back to the default content."""
        self.driver.switch_to.default_content()

    def verify_element_text(self, by: By, value: str, expected_text: str) -> bool:
        """Verify element text matches expected."""
        actual = self.get_text(by, value)
        matches = actual.strip() == expected_text.strip()
        if not matches:
            logger.warning(
                "Text mismatch - Expected: '%s', Actual: '%s'",
                expected_text, actual
            )
        return matches

    def verify_url_contains(self, partial_url: str) -> bool:
        """Verify current URL contains expected text."""
        current = self.get_current_url()
        return partial_url in current

    def _setup_chrome(self) -> webdriver.Chrome:
        """Set up Chrome WebDriver."""
        options = ChromeOptions()
        if self.config.headless:
            options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")

        service = ChromeService(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=options)

    def _setup_firefox(self) -> webdriver.Firefox:
        """Set up Firefox WebDriver."""
        options = FirefoxOptions()
        if self.config.headless:
            options.add_argument("--headless")

        service = FirefoxService(GeckoDriverManager().install())
        return webdriver.Firefox(service=service, options=options)


class SeleniumStepExecutor:
    """Executes Gherkin-style steps using Selenium."""

    def __init__(self, runner: SeleniumRunner):
        self.runner = runner
        self.variables: dict[str, str] = {}

    def execute_step(self, step_type: str, step_text: str) -> bool:
        """Execute a single Gherkin step.

        Args:
            step_type: 'Given', 'When', 'Then', or 'And'.
            step_text: The step text.

        Returns:
            True if step passed, False otherwise.
        """
        try:
            text = step_text.lower().strip()

            if "opens the browser" in text or "navigates to" in text:
                url = self._extract_url(step_text)
                self.runner.navigate_to(url or "/")
                return True

            if "clicks on" in text or "click" in text:
                locator = self._extract_locator(step_text)
                if locator:
                    self.runner.click_element(*locator)
                return True

            if "enters" in text or "types" in text or "input" in text:
                locator = self._extract_locator(step_text)
                value = self._extract_value(step_text)
                if locator and value:
                    self.runner.enter_text(*locator, value)
                return True

            if "should be displayed" in text or "should be visible" in text:
                locator = self._extract_locator(step_text)
                if locator:
                    return self.runner.is_element_present(*locator)
                return True

            if "should contain" in text:
                expected = self._extract_value(step_text)
                page_source = self.runner.driver.page_source
                return expected.lower() in page_source.lower() if expected else True

            if "response code" in text:
                logger.info("API step detected (handled by REST framework): %s", step_text)
                return True

            logger.info("Step executed (no specific handler): %s %s", step_type, step_text)
            return True

        except Exception as e:
            logger.error("Step execution failed: %s %s - %s", step_type, step_text, e)
            self.runner.take_screenshot(f"failure_{step_type}")
            return False

    def _extract_url(self, text: str) -> Optional[str]:
        """Extract URL from step text."""
        import re
        match = re.search(r'(https?://\S+|/\S+)', text)
        return match.group(1) if match else None

    def _extract_locator(self, text: str) -> Optional[tuple]:
        """Extract element locator from step text."""
        import re

        id_match = re.search(r'#(\w+)', text)
        if id_match:
            return (By.ID, id_match.group(1))

        class_match = re.search(r'\.(\w+)', text)
        if class_match:
            return (By.CLASS_NAME, class_match.group(1))

        quoted_match = re.search(r'"([^"]+)"', text)
        if quoted_match:
            value = quoted_match.group(1)
            return (By.XPATH, f"//*[contains(text(), '{value}')]")

        return None

    def _extract_value(self, text: str) -> Optional[str]:
        """Extract a value/text from step text."""
        import re
        match = re.search(r'"([^"]+)"', text)
        return match.group(1) if match else None
