"""Main agent orchestrator - connects Jira, Gherkin generation, Selenium, POM, LLM, Copado, and multi-UI frameworks."""

import argparse
import json
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from config import AgentConfig, JiraConfig, OutputConfig, SeleniumConfig
from gherkin_generator import GherkinGenerator
from git_commit_watcher import GitCommitWatcher
from jira_client import JiraClient, UserStory, AcceptanceCriteria
from llm_feature_updater import LLMClient, LLMFeatureUpdater
from page_object_model import PageObjectFactory, POMStepExecutor
from report_generator import (
    FeatureResult,
    ReportGenerator,
    ScenarioResult,
    StepResult,
    TestExecutionReport,
)
from copado_deployer import CopadoDeployer
from selenium_runner import SeleniumRunner, SeleniumStepExecutor
from test_data_agent import TestDataAgent, TestDataSet
from ui_agent import UIAgent, UIFrameworkDetector

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("agent.log", mode="a"),
    ],
)
logger = logging.getLogger(__name__)


class JiraSeleniumAgent:
    """Orchestrates the Jira-to-Gherkin-to-Selenium pipeline.

    Integrates:
    - Jira client for fetching user stories
    - Gherkin generator for creating feature files
    - Selenium runner with POM for browser test execution
    - Test data agent for managing test artifacts
    - Report generator for CI/CD integration
    - Git commit watcher with LLM for auto-updating features
    """

    def __init__(self, config: AgentConfig):
        self.config = config
        self.jira_client = JiraClient(config.jira)
        self.gherkin_generator = GherkinGenerator(config.output)
        self.selenium_runner = SeleniumRunner(config.selenium)
        self.test_data_agent = TestDataAgent(config)
        self.report_generator = ReportGenerator()
        self.copado_deployer = CopadoDeployer(config)
        self.llm_updater = LLMFeatureUpdater()
        self.step_executor = None
        self.pom_executor = None
        self.ui_agent = None

    def run(self, status_filter: str = None, story_keys: list[str] = None):
        """Run the complete pipeline.

        Args:
            status_filter: Optional Jira status filter.
            story_keys: Optional list of specific story keys to process.
        """
        logger.info("=" * 60)
        logger.info("Jira-Selenium-Gherkin Agent Starting")
        logger.info("=" * 60)

        stories = self._fetch_stories(status_filter, story_keys)
        if not stories:
            logger.warning("No stories found to process.")
            return

        logger.info("Processing %d user stories...", len(stories))

        feature_files = self._generate_features(stories)
        logger.info("Generated %d feature files.", len(feature_files))

        report = self._generate_report(stories, feature_files)
        logger.info("\n%s", report)

        logger.info("=" * 60)
        logger.info("Agent pipeline complete.")
        logger.info("=" * 60)

    def run_with_selenium(
        self, status_filter: str = None, story_keys: list[str] = None,
        use_pom: bool = True,
    ):
        """Run the complete pipeline including Selenium test execution with POM.

        Args:
            status_filter: Optional Jira status filter.
            story_keys: Optional list of specific story keys to process.
            use_pom: Whether to use Page Object Model for execution.
        """
        logger.info("=" * 60)
        logger.info("Jira-Selenium-Gherkin Agent Starting (with Selenium + POM)")
        logger.info("=" * 60)

        stories = self._fetch_stories(status_filter, story_keys)
        if not stories:
            logger.warning("No stories found to process.")
            return

        feature_files = self._generate_features(stories)

        # Upload test data for each story
        for story in stories:
            self._upload_test_data(story, feature_files)

        if self.selenium_runner.setup():
            self.step_executor = SeleniumStepExecutor(self.selenium_runner)

            # Initialize UI Agent with auto-detection
            self.ui_agent = UIAgent(
                self.selenium_runner.driver, self.config.selenium.base_url
            )
            detected = self.ui_agent.detect_and_setup(self.config.selenium.base_url)
            logger.info("UI framework detected: %s", detected.value)

            if use_pom:
                factory = PageObjectFactory(
                    self.selenium_runner.driver, self.config.selenium.base_url
                )
                self.pom_executor = POMStepExecutor(factory)

            test_results = self._run_selenium_tests(stories)
            self.selenium_runner.teardown()
        else:
            logger.error("Selenium setup failed. Skipping browser tests.")
            test_results = {}

        # Generate CI/CD reports
        execution_report = self._build_execution_report(stories, test_results)
        report_files = self.report_generator.generate_report(execution_report)
        logger.info("CI/CD reports generated: %s", report_files)

        # Deploy to Copado
        story_keys_list = [s.key for s in stories]
        copado_result = self.copado_deployer.deploy_test_results(
            execution_report, report_files, story_keys_list
        )
        logger.info("Copado deployment: %s - %s", copado_result.status, copado_result.message)

        report = self._generate_report(stories, feature_files, test_results)
        logger.info("\n%s", report)

    def run_demo(self, demo_stories: list[dict] = None):
        """Run a demo with sample user stories (no Jira connection needed).

        Args:
            demo_stories: Optional list of story dicts to use as demo data.
        """
        logger.info("=" * 60)
        logger.info("Jira-Selenium-Gherkin Agent - DEMO MODE")
        logger.info("=" * 60)

        stories = self._get_demo_stories(demo_stories)

        feature_files = self._generate_features(stories)
        logger.info("Generated %d feature files in demo mode.", len(feature_files))

        # Upload test data for demo stories
        for story in stories:
            self._upload_test_data(story, feature_files)

        # Generate demo CI/CD report
        demo_report = self._build_demo_execution_report(stories)
        report_files = self.report_generator.generate_report(demo_report)
        logger.info("Demo CI/CD reports generated: %s", report_files)

        # Deploy to Copado (local mode if not configured)
        story_keys_list = [s.key for s in stories]
        copado_result = self.copado_deployer.deploy_test_results(
            demo_report, report_files, story_keys_list
        )
        logger.info("Copado deployment: %s - %s", copado_result.status, copado_result.message)

        report = self._generate_report(stories, feature_files)
        logger.info("\n%s", report)

        print("\n--- Generated Feature Files ---")
        for fp in feature_files:
            print(f"\nFile: {fp}")
            print(fp.read_text())
            print("-" * 40)

    def run_watcher(self, repo_path: str = ".", interval: int = 30):
        """Run the Git Commit Watcher mode.

        Monitors the repo for commits referencing story keys and
        auto-updates feature files using LLM.

        Args:
            repo_path: Path to the git repository.
            interval: Polling interval in seconds.
        """
        logger.info("=" * 60)
        logger.info("Jira-Selenium-Gherkin Agent - WATCHER MODE")
        logger.info("=" * 60)

        watcher = GitCommitWatcher(
            config=self.config,
            repo_path=repo_path,
        )
        watcher.watch(interval_seconds=interval)

    def run_webhook(self, repo_path: str = ".", port: int = 9090):
        """Run the Git Webhook Handler mode.

        Listens for GitHub push events and auto-updates feature files.

        Args:
            repo_path: Path to the git repository.
            port: Port to listen on for webhooks.
        """
        logger.info("=" * 60)
        logger.info("Jira-Selenium-Gherkin Agent - WEBHOOK MODE")
        logger.info("=" * 60)

        watcher = GitCommitWatcher(
            config=self.config,
            repo_path=repo_path,
        )
        watcher.setup_webhook_handler(port=port)

    def process_commit(self, commit_sha: str, repo_path: str = "."):
        """Process a single commit to update feature files.

        Args:
            commit_sha: Git commit SHA to process.
            repo_path: Path to the git repository.
        """
        logger.info("Processing commit: %s", commit_sha)
        watcher = GitCommitWatcher(
            config=self.config,
            repo_path=repo_path,
        )
        updated = watcher.process_single_commit(commit_sha)
        logger.info("Updated %d feature files.", len(updated))
        return updated

    def _fetch_stories(
        self, status_filter: str = None, story_keys: list[str] = None
    ) -> list[UserStory]:
        """Fetch stories from Jira."""
        logger.info("Connecting to Jira...")
        if not self.jira_client.connect():
            logger.error("Failed to connect to Jira.")
            return []

        if story_keys:
            stories = []
            for key in story_keys:
                story = self.jira_client.fetch_story_by_key(key)
                if story:
                    stories.append(story)
            return stories

        return self.jira_client.fetch_assigned_stories(status_filter)

    def _generate_features(self, stories: list[UserStory]) -> list[Path]:
        """Generate Gherkin feature files from stories."""
        return self.gherkin_generator.generate_batch(stories)

    def _upload_test_data(self, story: UserStory, feature_files: list[Path]):
        """Upload test data for a user story."""
        feature_path = ""
        for fp in feature_files:
            if story.key.lower().replace("-", "") in fp.stem.lower().replace("-", ""):
                feature_path = str(fp)
                break

        dataset = TestDataSet(
            story_key=story.key,
            test_data={
                "story_summary": story.summary,
                "story_description": story.description,
                "acceptance_criteria_count": len(story.acceptance_criteria),
                "priority": story.priority,
            },
            feature_file_path=feature_path,
            app_url=self.config.selenium.base_url,
            environment="test",
        )
        self.test_data_agent.upload_test_data(dataset)

    def _build_execution_report(
        self, stories: list[UserStory], test_results: dict
    ) -> TestExecutionReport:
        """Build a TestExecutionReport from Selenium test results."""
        run_id = f"run-{int(time.time())}"
        report = TestExecutionReport(
            run_id=run_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            environment="test",
            app_url=self.config.selenium.base_url,
        )

        for story in stories:
            feature = FeatureResult(
                name=story.summary,
                story_key=story.key,
                file_path="",
                status="passed",
            )

            story_result = test_results.get(story.key, {})
            for idx, ac in enumerate(story.acceptance_criteria, 1):
                scenario = ScenarioResult(
                    name=f"Scenario {idx}",
                    status="passed",
                    tags=[f"@{story.key.replace('-', '_')}"],
                )

                for step_data in story_result.get("steps", []):
                    step = StepResult(
                        step_type=step_data.get("type", "Given"),
                        step_text=step_data.get("text", ""),
                        status=step_data.get("status", "passed"),
                    )
                    scenario.steps.append(step)
                    if step.status == "failed":
                        scenario.status = "failed"

                feature.scenarios.append(scenario)
                if scenario.status == "failed":
                    feature.status = "failed"

            report.features.append(feature)

        return report

    def _build_demo_execution_report(
        self, stories: list[UserStory]
    ) -> TestExecutionReport:
        """Build a demo execution report (all passing)."""
        run_id = f"demo-{int(time.time())}"
        report = TestExecutionReport(
            run_id=run_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            environment="demo",
            app_url=self.config.selenium.base_url,
        )

        for story in stories:
            feature = FeatureResult(
                name=story.summary,
                story_key=story.key,
                file_path="",
                status="passed",
            )

            for idx, ac in enumerate(story.acceptance_criteria, 1):
                scenario = ScenarioResult(
                    name=f"Scenario {idx}: {ac.when[:50] if ac.when else 'verify'}",
                    status="passed",
                    tags=[f"@{story.key.replace('-', '_')}"],
                )
                if ac.given:
                    scenario.steps.append(
                        StepResult("Given", ac.given, "passed", 50.0)
                    )
                if ac.when:
                    scenario.steps.append(
                        StepResult("When", ac.when, "passed", 100.0)
                    )
                if ac.then:
                    scenario.steps.append(
                        StepResult("Then", ac.then, "passed", 75.0)
                    )
                feature.scenarios.append(scenario)

            report.features.append(feature)

        report.total_duration_ms = sum(
            s.duration_ms
            for f in report.features
            for s in f.scenarios
        )
        return report

    def _run_selenium_tests(self, stories: list[UserStory]) -> dict:
        """Run Selenium-based tests for the generated features."""
        results = {}

        for story in stories:
            story_results = {"passed": 0, "failed": 0, "skipped": 0, "steps": []}

            for ac in story.acceptance_criteria:
                steps = self._extract_steps_from_ac(ac)
                for step_type, step_text in steps:
                    passed = self.step_executor.execute_step(step_type, step_text)
                    step_result = {
                        "type": step_type,
                        "text": step_text,
                        "status": "passed" if passed else "failed",
                    }
                    story_results["steps"].append(step_result)
                    if passed:
                        story_results["passed"] += 1
                    else:
                        story_results["failed"] += 1

            results[story.key] = story_results

        return results

    def _extract_steps_from_ac(self, ac: AcceptanceCriteria) -> list[tuple[str, str]]:
        """Extract step type and text from acceptance criteria."""
        steps = []
        if ac.given:
            for line in ac.given.split("\n"):
                line = line.strip()
                if line.lower().startswith("given "):
                    steps.append(("Given", line[6:]))
                elif line.lower().startswith("and "):
                    steps.append(("And", line[4:]))
                else:
                    steps.append(("Given", line))
        if ac.when:
            for line in ac.when.split("\n"):
                line = line.strip()
                if line.lower().startswith("when "):
                    steps.append(("When", line[5:]))
                elif line.lower().startswith("and "):
                    steps.append(("And", line[4:]))
                else:
                    steps.append(("When", line))
        if ac.then:
            for line in ac.then.split("\n"):
                line = line.strip()
                if line.lower().startswith("then "):
                    steps.append(("Then", line[5:]))
                elif line.lower().startswith("and "):
                    steps.append(("And", line[4:]))
                else:
                    steps.append(("Then", line))
        return steps

    def _generate_report(
        self,
        stories: list[UserStory],
        feature_files: list[Path],
        test_results: dict = None,
    ) -> str:
        """Generate an execution report."""
        lines = [
            "=" * 60,
            "  JIRA-SELENIUM-GHERKIN AGENT REPORT",
            "=" * 60,
            "",
            f"  Stories Processed: {len(stories)}",
            f"  Feature Files Generated: {len(feature_files)}",
            "",
        ]

        lines.append("  Stories:")
        for story in stories:
            lines.append(f"    [{story.key}] {story.summary}")
            lines.append(f"      Priority: {story.priority} | Status: {story.status}")
            lines.append(
                f"      Acceptance Criteria: {len(story.acceptance_criteria)}"
            )

        lines.append("")
        lines.append("  Generated Files:")
        for fp in feature_files:
            lines.append(f"    - {fp}")

        if test_results:
            lines.append("")
            lines.append("  Selenium Test Results:")
            total_passed = 0
            total_failed = 0
            for key, results in test_results.items():
                total_passed += results["passed"]
                total_failed += results["failed"]
                status = "PASS" if results["failed"] == 0 else "FAIL"
                lines.append(
                    f"    [{key}] {status} - "
                    f"Passed: {results['passed']}, Failed: {results['failed']}"
                )
            lines.append("")
            lines.append(
                f"  Total: {total_passed} passed, {total_failed} failed"
            )

        lines.append("")
        lines.append("=" * 60)
        return "\n".join(lines)

    def _get_demo_stories(self, demo_stories: list[dict] = None) -> list[UserStory]:
        """Get demo user stories for testing without Jira."""
        if demo_stories:
            return [self._dict_to_story(d) for d in demo_stories]

        return [
            UserStory(
                key="DEMO-101",
                summary="User Login Authentication",
                description=(
                    "As a registered user\n"
                    "I want to log in to the application\n"
                    "So that I can access my dashboard\n\n"
                    "Acceptance Criteria:\n"
                    "Given the user is on the login page\n"
                    "When the user enters valid credentials\n"
                    "Then the user should be redirected to the dashboard\n"
                    "And the welcome message should be displayed\n\n"
                    "Given the user is on the login page\n"
                    "When the user enters invalid credentials\n"
                    "Then an error message should be displayed\n"
                    "And the user should remain on the login page"
                ),
                acceptance_criteria=[
                    AcceptanceCriteria(
                        given="Given the user is on the login page",
                        when="When the user enters valid credentials",
                        then="Then the user should be redirected to the dashboard\nAnd the welcome message should be displayed",
                    ),
                    AcceptanceCriteria(
                        given="Given the user is on the login page",
                        when="When the user enters invalid credentials",
                        then="Then an error message should be displayed\nAnd the user should remain on the login page",
                    ),
                ],
                priority="High",
                labels=["authentication", "login"],
                status="In Progress",
                assignee="Demo User",
                components=["frontend", "auth"],
            ),
            UserStory(
                key="DEMO-102",
                summary="REST API Create User Endpoint",
                description=(
                    "As an admin user\n"
                    "I want to create new users via REST API\n"
                    "So that I can manage the user base\n\n"
                    "Acceptance Criteria:\n"
                    "Given the admin is authenticated\n"
                    "When a POST request is sent to /api/users with valid data\n"
                    "Then the response code should be 201\n"
                    "And the response body should contain the new user data\n\n"
                    "Given the admin is authenticated\n"
                    "When a POST request is sent to /api/users with missing fields\n"
                    "Then the response code should be 400\n"
                    "And the response should contain validation errors"
                ),
                acceptance_criteria=[
                    AcceptanceCriteria(
                        given="Given the admin is authenticated",
                        when="When a POST request is sent to /api/users with valid data",
                        then="Then the response code should be 201\nAnd the response body should contain the new user data",
                    ),
                    AcceptanceCriteria(
                        given="Given the admin is authenticated",
                        when="When a POST request is sent to /api/users with missing fields",
                        then="Then the response code should be 400\nAnd the response should contain validation errors",
                    ),
                ],
                priority="High",
                labels=["api", "users"],
                status="To Do",
                assignee="Demo User",
                components=["backend", "api"],
            ),
            UserStory(
                key="DEMO-103",
                summary="Product Search and Filter",
                description=(
                    "As a customer\n"
                    "I want to search and filter products\n"
                    "So that I can find what I need quickly\n\n"
                    "Acceptance Criteria:\n"
                    "Given the user is on the products page\n"
                    "When the user enters a search term in the search bar\n"
                    "Then matching products should be displayed\n"
                    "And non-matching products should be hidden\n\n"
                    "Given search results are displayed\n"
                    "When the user applies a price filter\n"
                    "Then only products within the price range should show\n"
                    "And the result count should update"
                ),
                acceptance_criteria=[
                    AcceptanceCriteria(
                        given="Given the user is on the products page",
                        when="When the user enters a search term in the search bar",
                        then="Then matching products should be displayed\nAnd non-matching products should be hidden",
                    ),
                    AcceptanceCriteria(
                        given="Given search results are displayed",
                        when="When the user applies a price filter",
                        then="Then only products within the price range should show\nAnd the result count should update",
                    ),
                ],
                priority="Medium",
                labels=["search", "products", "ui"],
                status="To Do",
                assignee="Demo User",
                components=["frontend", "search"],
            ),
        ]

    def _dict_to_story(self, data: dict) -> UserStory:
        """Convert a dictionary to a UserStory."""
        criteria = []
        for ac_data in data.get("acceptance_criteria", []):
            if isinstance(ac_data, dict):
                criteria.append(AcceptanceCriteria(**ac_data))
            elif isinstance(ac_data, str):
                criteria.append(AcceptanceCriteria(raw_text=ac_data))

        return UserStory(
            key=data.get("key", "UNKNOWN-0"),
            summary=data.get("summary", ""),
            description=data.get("description", ""),
            acceptance_criteria=criteria,
            priority=data.get("priority", "Medium"),
            labels=data.get("labels", []),
            status=data.get("status", ""),
            assignee=data.get("assignee", ""),
            components=data.get("components", []),
        )


def main():
    parser = argparse.ArgumentParser(
        description="Jira-Selenium-Gherkin Agent: Convert Jira user stories to Gherkin feature files"
    )

    parser.add_argument(
        "--mode",
        choices=["jira", "demo", "selenium", "watcher", "webhook", "commit"],
        default="demo",
        help=(
            "Run mode: 'jira' (connect to Jira), 'demo' (sample stories), "
            "'selenium' (with browser+POM tests), 'watcher' (poll git for commits), "
            "'webhook' (listen for GitHub push events), 'commit' (process single commit)"
        ),
    )
    parser.add_argument(
        "--status",
        type=str,
        default=None,
        help="Filter stories by Jira status (e.g., 'To Do', 'In Progress')",
    )
    parser.add_argument(
        "--stories",
        type=str,
        nargs="*",
        default=None,
        help="Specific Jira story keys to process (e.g., PROJ-123 PROJ-456)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Override the feature file output directory",
    )
    parser.add_argument(
        "--stories-file",
        type=str,
        default=None,
        help="Path to JSON file containing stories (for demo mode with custom data)",
    )
    parser.add_argument(
        "--repo-path",
        type=str,
        default=".",
        help="Path to the git repository (for watcher/webhook/commit modes)",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=30,
        help="Polling interval in seconds (for watcher mode)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=9090,
        help="Port for webhook listener (for webhook mode)",
    )
    parser.add_argument(
        "--commit-sha",
        type=str,
        default=None,
        help="Commit SHA to process (for commit mode)",
    )

    args = parser.parse_args()

    config = AgentConfig()

    if args.output_dir:
        config.output.output_dir = args.output_dir

    agent = JiraSeleniumAgent(config)

    if args.mode == "demo":
        demo_stories = None
        if args.stories_file:
            with open(args.stories_file) as f:
                demo_stories = json.load(f)
        agent.run_demo(demo_stories)

    elif args.mode == "jira":
        if not config.jira.username or not config.jira.api_token:
            logger.error(
                "Jira credentials not configured. Set JIRA_USERNAME and JIRA_API_TOKEN environment variables."
            )
            sys.exit(1)
        agent.run(status_filter=args.status, story_keys=args.stories)

    elif args.mode == "selenium":
        if not config.jira.username or not config.jira.api_token:
            logger.error(
                "Jira credentials not configured. Set JIRA_USERNAME and JIRA_API_TOKEN environment variables."
            )
            sys.exit(1)
        agent.run_with_selenium(status_filter=args.status, story_keys=args.stories)

    elif args.mode == "watcher":
        agent.run_watcher(repo_path=args.repo_path, interval=args.interval)

    elif args.mode == "webhook":
        agent.run_webhook(repo_path=args.repo_path, port=args.port)

    elif args.mode == "commit":
        if not args.commit_sha:
            logger.error("--commit-sha is required for commit mode.")
            sys.exit(1)
        agent.process_commit(args.commit_sha, repo_path=args.repo_path)


if __name__ == "__main__":
    main()
