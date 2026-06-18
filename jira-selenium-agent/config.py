"""Configuration module for Jira-Selenium-Gherkin Agent."""

import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


@dataclass
class JiraConfig:
    """Jira connection configuration."""
    server_url: str = os.getenv("JIRA_SERVER_URL", "https://your-domain.atlassian.net")
    username: str = os.getenv("JIRA_USERNAME", "")
    api_token: str = os.getenv("JIRA_API_TOKEN", "")
    project_key: str = os.getenv("JIRA_PROJECT_KEY", "")
    assignee: str = os.getenv("JIRA_ASSIGNEE", "currentUser()")
    story_issue_type: str = os.getenv("JIRA_STORY_TYPE", "Story")
    max_results: int = int(os.getenv("JIRA_MAX_RESULTS", "50"))


@dataclass
class SeleniumConfig:
    """Selenium WebDriver configuration."""
    browser: str = os.getenv("SELENIUM_BROWSER", "chrome")
    headless: bool = os.getenv("SELENIUM_HEADLESS", "true").lower() == "true"
    base_url: str = os.getenv("APP_BASE_URL", "http://localhost:8080")
    implicit_wait: int = int(os.getenv("SELENIUM_IMPLICIT_WAIT", "10"))
    screenshot_dir: str = os.getenv("SCREENSHOT_DIR", "screenshots")


@dataclass
class OutputConfig:
    """Feature file output configuration."""
    output_dir: str = os.getenv(
        "FEATURE_OUTPUT_DIR",
        "src/test/resources/features/generated"
    )
    step_definitions_dir: str = os.getenv(
        "STEP_DEFINITIONS_DIR",
        "src/test/java/generated/steps"
    )
    overwrite_existing: bool = os.getenv("OVERWRITE_FEATURES", "false").lower() == "true"


@dataclass
class AgentConfig:
    """Top-level agent configuration."""
    jira: JiraConfig = field(default_factory=JiraConfig)
    selenium: SeleniumConfig = field(default_factory=SeleniumConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
