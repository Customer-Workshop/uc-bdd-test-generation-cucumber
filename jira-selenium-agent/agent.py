"""Main agent orchestrator - connects Jira, Gherkin generation, and Selenium."""

import argparse
import json
import logging
import sys
from pathlib import Path

from config import AgentConfig, JiraConfig, OutputConfig, SeleniumConfig
from gherkin_generator import GherkinGenerator
from jira_client import JiraClient, UserStory, AcceptanceCriteria
from selenium_runner import SeleniumRunner, SeleniumStepExecutor

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
    """Orchestrates the Jira-to-Gherkin-to-Selenium pipeline."""

    def __init__(self, config: AgentConfig):
        self.config = config
        self.jira_client = JiraClient(config.jira)
        self.gherkin_generator = GherkinGenerator(config.output)
        self.selenium_runner = SeleniumRunner(config.selenium)
        self.step_executor = None

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
        self, status_filter: str = None, story_keys: list[str] = None
    ):
        """Run the complete pipeline including Selenium test execution.

        Args:
            status_filter: Optional Jira status filter.
            story_keys: Optional list of specific story keys to process.
        """
        logger.info("=" * 60)
        logger.info("Jira-Selenium-Gherkin Agent Starting (with Selenium)")
        logger.info("=" * 60)

        stories = self._fetch_stories(status_filter, story_keys)
        if not stories:
            logger.warning("No stories found to process.")
            return

        feature_files = self._generate_features(stories)

        if self.selenium_runner.setup():
            self.step_executor = SeleniumStepExecutor(self.selenium_runner)
            test_results = self._run_selenium_tests(stories)
            self.selenium_runner.teardown()
        else:
            logger.error("Selenium setup failed. Skipping browser tests.")
            test_results = {}

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

        report = self._generate_report(stories, feature_files)
        logger.info("\n%s", report)

        print("\n--- Generated Feature Files ---")
        for fp in feature_files:
            print(f"\nFile: {fp}")
            print(fp.read_text())
            print("-" * 40)

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
        choices=["jira", "demo", "selenium"],
        default="demo",
        help="Run mode: 'jira' (connect to Jira), 'demo' (use sample stories), 'selenium' (with browser tests)",
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


if __name__ == "__main__":
    main()
