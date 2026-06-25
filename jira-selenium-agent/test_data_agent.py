"""Test Data Upload Agent.

Manages test data for user stories: uploads test data files, BDD feature files,
Selenium configuration, and application URL for test execution.
"""

import json
import logging
import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from config import AgentConfig

logger = logging.getLogger(__name__)


@dataclass
class TestDataSet:
    """Represents a test data set for a user story."""
    story_key: str
    test_data: dict = field(default_factory=dict)
    feature_file_path: str = ""
    selenium_config: dict = field(default_factory=dict)
    app_url: str = ""
    environment: str = "test"
    data_files: list[str] = field(default_factory=list)


class TestDataAgent:
    """Agent that manages test data upload and configuration for test execution.

    Responsibilities:
    - Upload and manage test data for each user story
    - Associate BDD feature files with test data
    - Configure Selenium settings per story (browser, app URL, etc.)
    - Provide test data to the execution pipeline
    """

    TEST_DATA_DIR = "test-data"
    SELENIUM_CONFIG_DIR = "selenium-configs"
    FEATURE_ARCHIVE_DIR = "feature-archive"

    def __init__(self, config: AgentConfig):
        self.config = config
        self.base_dir = Path(config.output.output_dir).parent
        self._ensure_directories()

    def _ensure_directories(self):
        """Create required directories."""
        for d in [self.TEST_DATA_DIR, self.SELENIUM_CONFIG_DIR, self.FEATURE_ARCHIVE_DIR]:
            (self.base_dir / d).mkdir(parents=True, exist_ok=True)

    def upload_test_data(self, dataset: TestDataSet) -> Path:
        """Upload test data for a user story.

        Creates a structured JSON file containing all test data,
        selenium config, and references for the story.

        Args:
            dataset: The TestDataSet to upload.

        Returns:
            Path to the created test data file.
        """
        test_data_dir = self.base_dir / self.TEST_DATA_DIR / dataset.story_key
        test_data_dir.mkdir(parents=True, exist_ok=True)

        manifest = {
            "story_key": dataset.story_key,
            "environment": dataset.environment,
            "app_url": dataset.app_url or self.config.selenium.base_url,
            "test_data": dataset.test_data,
            "feature_file": dataset.feature_file_path,
            "selenium_config": dataset.selenium_config or self._default_selenium_config(),
            "data_files": dataset.data_files,
        }

        manifest_path = test_data_dir / "test-manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        logger.info("Test data uploaded for %s: %s", dataset.story_key, manifest_path)

        if dataset.test_data:
            data_path = test_data_dir / "test-data.json"
            data_path.write_text(
                json.dumps(dataset.test_data, indent=2), encoding="utf-8"
            )

        for data_file in dataset.data_files:
            src = Path(data_file)
            if src.exists():
                dst = test_data_dir / src.name
                shutil.copy2(src, dst)
                logger.info("Copied data file: %s -> %s", src, dst)

        return manifest_path

    def upload_selenium_config(
        self, story_key: str, config_overrides: dict = None
    ) -> Path:
        """Upload Selenium configuration for a specific story.

        Args:
            story_key: The Jira story key.
            config_overrides: Optional overrides for default Selenium config.

        Returns:
            Path to the created Selenium config file.
        """
        config = self._default_selenium_config()
        if config_overrides:
            config.update(config_overrides)

        config_dir = self.base_dir / self.SELENIUM_CONFIG_DIR
        config_path = config_dir / f"{story_key.lower()}-selenium.json"
        config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
        logger.info("Selenium config uploaded for %s: %s", story_key, config_path)
        return config_path

    def upload_feature_file(self, story_key: str, feature_content: str) -> Path:
        """Archive a feature file for a story.

        Args:
            story_key: The Jira story key.
            feature_content: The Gherkin feature file content.

        Returns:
            Path to the archived feature file.
        """
        archive_dir = self.base_dir / self.FEATURE_ARCHIVE_DIR / story_key
        archive_dir.mkdir(parents=True, exist_ok=True)

        feature_path = archive_dir / f"{story_key.lower()}.feature"
        feature_path.write_text(feature_content, encoding="utf-8")
        logger.info("Feature file archived for %s: %s", story_key, feature_path)
        return feature_path

    def get_test_data(self, story_key: str) -> Optional[dict]:
        """Retrieve test data for a story.

        Args:
            story_key: The Jira story key.

        Returns:
            The test data manifest dict, or None if not found.
        """
        manifest_path = (
            self.base_dir / self.TEST_DATA_DIR / story_key / "test-manifest.json"
        )
        if not manifest_path.exists():
            logger.warning("No test data found for %s", story_key)
            return None

        return json.loads(manifest_path.read_text(encoding="utf-8"))

    def get_selenium_config(self, story_key: str) -> Optional[dict]:
        """Retrieve Selenium configuration for a story.

        Args:
            story_key: The Jira story key.

        Returns:
            Selenium config dict, or None if not found.
        """
        config_path = (
            self.base_dir
            / self.SELENIUM_CONFIG_DIR
            / f"{story_key.lower()}-selenium.json"
        )
        if not config_path.exists():
            return self._default_selenium_config()

        return json.loads(config_path.read_text(encoding="utf-8"))

    def get_app_url(self, story_key: str) -> str:
        """Get the application URL for testing a story.

        Args:
            story_key: The Jira story key.

        Returns:
            The application URL configured for this story.
        """
        test_data = self.get_test_data(story_key)
        if test_data and test_data.get("app_url"):
            return test_data["app_url"]
        return self.config.selenium.base_url

    def list_test_data(self) -> list[str]:
        """List all story keys that have test data uploaded.

        Returns:
            List of story keys.
        """
        test_data_dir = self.base_dir / self.TEST_DATA_DIR
        if not test_data_dir.exists():
            return []
        return [
            d.name
            for d in test_data_dir.iterdir()
            if d.is_dir() and (d / "test-manifest.json").exists()
        ]

    def prepare_execution_bundle(self, story_key: str) -> dict:
        """Prepare a complete execution bundle for a story.

        Combines test data, Selenium config, and feature file references
        into a single bundle ready for the test execution pipeline.

        Args:
            story_key: The Jira story key.

        Returns:
            Execution bundle dict with all test artifacts.
        """
        test_data = self.get_test_data(story_key) or {}
        selenium_config = self.get_selenium_config(story_key) or {}
        app_url = self.get_app_url(story_key)

        feature_path = (
            self.base_dir
            / self.FEATURE_ARCHIVE_DIR
            / story_key
            / f"{story_key.lower()}.feature"
        )
        feature_content = ""
        if feature_path.exists():
            feature_content = feature_path.read_text(encoding="utf-8")

        return {
            "story_key": story_key,
            "app_url": app_url,
            "test_data": test_data.get("test_data", {}),
            "selenium_config": selenium_config,
            "feature_content": feature_content,
            "feature_file": str(feature_path) if feature_path.exists() else "",
            "data_files": test_data.get("data_files", []),
        }

    def _default_selenium_config(self) -> dict:
        """Generate default Selenium configuration."""
        return {
            "browser": self.config.selenium.browser,
            "headless": self.config.selenium.headless,
            "base_url": self.config.selenium.base_url,
            "implicit_wait": self.config.selenium.implicit_wait,
            "explicit_wait": 10,
            "page_load_timeout": 30,
            "screenshot_on_failure": True,
            "screenshot_dir": self.config.selenium.screenshot_dir,
            "window_size": {"width": 1920, "height": 1080},
            "capabilities": {
                "acceptInsecureCerts": True,
                "unhandledPromptBehavior": "dismiss",
            },
        }
