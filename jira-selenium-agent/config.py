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
class LLMConfig:
    """LLM configuration for feature file auto-updates."""
    api_key: str = os.getenv("LLM_API_KEY", "")
    api_url: str = os.getenv("LLM_API_URL", "https://api.openai.com/v1/chat/completions")
    model: str = os.getenv("LLM_MODEL", "gpt-4")
    temperature: float = float(os.getenv("LLM_TEMPERATURE", "0.3"))


@dataclass
class WatcherConfig:
    """Git commit watcher configuration."""
    github_token: str = os.getenv("GITHUB_TOKEN", "")
    github_repo: str = os.getenv("GITHUB_REPO", "")
    poll_interval: int = int(os.getenv("WATCHER_POLL_INTERVAL", "30"))
    webhook_port: int = int(os.getenv("WEBHOOK_PORT", "9090"))


@dataclass
class AgentConfig:
    """Top-level agent configuration."""
    jira: JiraConfig = field(default_factory=JiraConfig)
    selenium: SeleniumConfig = field(default_factory=SeleniumConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    watcher: WatcherConfig = field(default_factory=WatcherConfig)
