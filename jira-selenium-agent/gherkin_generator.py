"""Gherkin feature file generator from Jira user stories."""

import logging
import os
import re
from pathlib import Path

from jira_client import AcceptanceCriteria, UserStory
from config import OutputConfig

logger = logging.getLogger(__name__)


class GherkinGenerator:
    """Generates Gherkin .feature files from Jira user stories."""

    def __init__(self, config: OutputConfig):
        self.config = config

    def generate_feature_file(self, story: UserStory) -> str:
        """Generate a complete Gherkin feature file from a user story.

        Args:
            story: The UserStory to convert.

        Returns:
            The generated Gherkin feature content as a string.
        """
        lines = []

        lines.extend(self._generate_tags(story))
        lines.append(f"Feature: {story.summary}")
        lines.append(f"  # Jira Story: {story.key}")
        lines.append(f"  # Priority: {story.priority}")
        if story.assignee:
            lines.append(f"  # Assignee: {story.assignee}")
        lines.append("")

        if story.description:
            wrapped_desc = self._wrap_description(story.description)
            for desc_line in wrapped_desc:
                lines.append(f"  {desc_line}")
            lines.append("")

        lines.extend(self._generate_background(story))

        if story.acceptance_criteria:
            for idx, ac in enumerate(story.acceptance_criteria, 1):
                lines.extend(self._generate_scenario(story, ac, idx))
                lines.append("")
        else:
            lines.extend(self._generate_default_scenario(story))

        return "\n".join(lines)

    def generate_and_save(self, story: UserStory) -> Path:
        """Generate a feature file and save it to disk.

        Args:
            story: The UserStory to convert.

        Returns:
            Path to the created feature file.
        """
        content = self.generate_feature_file(story)
        filename = self._story_to_filename(story)
        output_path = Path(self.config.output_dir) / filename

        output_path.parent.mkdir(parents=True, exist_ok=True)

        if output_path.exists() and not self.config.overwrite_existing:
            logger.warning(
                "Feature file already exists and overwrite is disabled: %s",
                output_path
            )
            base = output_path.stem
            counter = 1
            while output_path.exists():
                output_path = output_path.parent / f"{base}_{counter}.feature"
                counter += 1

        output_path.write_text(content, encoding="utf-8")
        logger.info("Feature file created: %s", output_path)
        return output_path

    def generate_batch(self, stories: list[UserStory]) -> list[Path]:
        """Generate feature files for multiple user stories.

        Args:
            stories: List of UserStory objects.

        Returns:
            List of paths to the created feature files.
        """
        created_files = []
        for story in stories:
            try:
                path = self.generate_and_save(story)
                created_files.append(path)
            except Exception as e:
                logger.error("Failed to generate feature for %s: %s", story.key, e)
        return created_files

    def _generate_tags(self, story: UserStory) -> list[str]:
        """Generate Gherkin tags from story metadata."""
        tags = [f"@{story.key.replace('-', '_')}"]

        if story.priority:
            tags.append(f"@priority_{story.priority.lower().replace(' ', '_')}")

        for label in story.labels:
            sanitized = re.sub(r"[^a-zA-Z0-9_]", "_", label)
            tags.append(f"@{sanitized}")

        for component in story.components:
            sanitized = re.sub(r"[^a-zA-Z0-9_]", "_", component)
            tags.append(f"@component_{sanitized}")

        return [" ".join(tags)]

    def _wrap_description(self, description: str) -> list[str]:
        """Wrap story description as Gherkin comments, filtering out AC sections."""
        result = []
        in_ac_section = False

        for line in description.split("\n"):
            stripped = line.strip().lower()
            if any(kw in stripped for kw in [
                "acceptance criteria", "ac:", "acceptance:", "criteria:"
            ]):
                in_ac_section = True
                continue

            if in_ac_section and any(
                stripped.startswith(kw) for kw in ["given ", "when ", "then "]
            ):
                continue

            if not in_ac_section and line.strip():
                result.append(f"# {line.strip()}")

        return result

    def _generate_background(self, story: UserStory) -> list[str]:
        """Generate Background section if applicable."""
        lines = []

        has_api_context = any(
            kw in story.description.lower()
            for kw in ["api", "endpoint", "rest", "http", "url", "service"]
        ) if story.description else False

        has_ui_context = any(
            kw in story.description.lower()
            for kw in ["page", "button", "click", "form", "login", "ui", "screen", "navigate", "browser"]
        ) if story.description else False

        if has_api_context:
            lines.append("  Background:")
            lines.append("    Given http baseUri is /api/")
            lines.append("    And I set http headers to:")
            lines.append("      | Accept       | application/json |")
            lines.append("      | Content-Type | application/json |")
            lines.append("")
        elif has_ui_context:
            lines.append("  Background:")
            lines.append("    Given the user opens the browser")
            lines.append("    And the user navigates to the application")
            lines.append("")

        return lines

    def _generate_scenario(
        self, story: UserStory, ac: AcceptanceCriteria, index: int
    ) -> list[str]:
        """Generate a single Gherkin scenario from an acceptance criterion."""
        lines = []
        scenario_name = self._generate_scenario_name(story, ac, index)

        lines.append(f"  Scenario: {scenario_name}")

        if ac.given and ac.when and ac.then:
            lines.extend(self._format_gwt_steps(ac))
        elif ac.raw_text:
            lines.extend(self._convert_raw_to_steps(ac.raw_text, story))
        else:
            lines.append(f"    Given the precondition for {story.summary} is met")
            lines.append(f"    When the user performs the action for scenario {index}")
            lines.append(f"    Then the expected outcome for scenario {index} is verified")

        return lines

    def _generate_default_scenario(self, story: UserStory) -> list[str]:
        """Generate a default scenario when no acceptance criteria exist."""
        lines = []
        summary_clean = re.sub(r"[^a-zA-Z0-9 ]", "", story.summary)

        lines.append(f"  Scenario: Verify {summary_clean}")

        if story.description:
            lines.extend(self._convert_description_to_steps(story.description, story))
        else:
            lines.append(f"    Given the system is ready for {summary_clean}")
            lines.append(f"    When the user performs {summary_clean}")
            lines.append(f"    Then the {summary_clean} should be successful")

        return lines

    def _format_gwt_steps(self, ac: AcceptanceCriteria) -> list[str]:
        """Format Given/When/Then acceptance criteria into Gherkin steps."""
        lines = []

        given_parts = ac.given.split("\n")
        for i, part in enumerate(given_parts):
            text = part.strip()
            if text.lower().startswith("given "):
                text = text[6:]
            if i == 0:
                lines.append(f"    Given {text}")
            else:
                if text.lower().startswith("and "):
                    text = text[4:]
                lines.append(f"    And {text}")

        when_parts = ac.when.split("\n")
        for i, part in enumerate(when_parts):
            text = part.strip()
            if text.lower().startswith("when "):
                text = text[5:]
            if i == 0:
                lines.append(f"    When {text}")
            else:
                if text.lower().startswith("and "):
                    text = text[4:]
                lines.append(f"    And {text}")

        then_parts = ac.then.split("\n")
        for i, part in enumerate(then_parts):
            text = part.strip()
            if text.lower().startswith("then "):
                text = text[5:]
            if i == 0:
                lines.append(f"    Then {text}")
            else:
                if text.lower().startswith("and "):
                    text = text[4:]
                lines.append(f"    And {text}")

        return lines

    def _convert_raw_to_steps(self, raw_text: str, story: UserStory) -> list[str]:
        """Convert raw acceptance criteria text into Gherkin steps."""
        lines = []
        text = raw_text.strip()

        if self._is_ui_related(text):
            lines.extend(self._generate_ui_steps(text, story))
        elif self._is_api_related(text):
            lines.extend(self._generate_api_steps(text, story))
        else:
            lines.append(f"    Given the system is in the expected state")
            lines.append(f"    When {self._sanitize_step_text(text)}")
            lines.append(f"    Then the expected result is achieved")

        return lines

    def _convert_description_to_steps(
        self, description: str, story: UserStory
    ) -> list[str]:
        """Convert story description into basic Gherkin steps."""
        lines = []

        as_match = re.search(r"[Aa]s\s+(?:a|an)\s+(.+?)(?:,|\n|$)", description)
        want_match = re.search(r"[Ii]\s+want\s+(?:to\s+)?(.+?)(?:,|\n|$)", description)
        so_match = re.search(
            r"[Ss]o\s+that\s+(.+?)(?:\.|,|\n|$)", description
        )

        if as_match:
            role = as_match.group(1).strip()
            lines.append(f"    Given I am a {role}")
        else:
            lines.append(f"    Given the system is ready")

        if want_match:
            action = want_match.group(1).strip()
            lines.append(f"    When I {action}")
        else:
            lines.append(f"    When the user performs the required action")

        if so_match:
            outcome = so_match.group(1).strip()
            lines.append(f"    Then I should be able to {outcome}")
        else:
            lines.append(f"    Then the expected outcome is achieved")

        return lines

    def _generate_ui_steps(self, text: str, story: UserStory) -> list[str]:
        """Generate UI/Selenium-oriented Gherkin steps."""
        lines = []
        lines.append("    Given the user is on the application page")

        action_keywords = {
            "click": "the user clicks on",
            "enter": "the user enters",
            "type": "the user types",
            "select": "the user selects",
            "navigate": "the user navigates to",
            "submit": "the user submits",
            "login": "the user logs in",
            "search": "the user searches for",
            "upload": "the user uploads",
            "download": "the user downloads",
        }

        text_lower = text.lower()
        step_added = False
        for keyword, step_prefix in action_keywords.items():
            if keyword in text_lower:
                lines.append(f"    When {step_prefix} the element")
                step_added = True
                break

        if not step_added:
            lines.append(f"    When {self._sanitize_step_text(text)}")

        verification_keywords = {
            "display": "the element should be displayed",
            "visible": "the element should be visible",
            "message": "the success message should appear",
            "redirect": "the user should be redirected",
            "error": "the error message should be shown",
        }

        then_added = False
        for keyword, step_text in verification_keywords.items():
            if keyword in text_lower:
                lines.append(f"    Then {step_text}")
                then_added = True
                break

        if not then_added:
            lines.append("    Then the expected result should be verified")

        return lines

    def _generate_api_steps(self, text: str, story: UserStory) -> list[str]:
        """Generate API-oriented Gherkin steps."""
        lines = []
        text_lower = text.lower()

        method = "GET"
        for m in ["post", "put", "delete", "patch", "get"]:
            if m in text_lower:
                method = m.upper()
                break

        endpoint_match = re.search(r"/[\w/{}]+", text)
        endpoint = endpoint_match.group(0) if endpoint_match else f"/api/{story.key.lower()}"

        lines.append(f"    Given http baseUri is /api/")

        if method in ("POST", "PUT", "PATCH"):
            lines.append(f'    And I set http body to {{}}')

        lines.append(f"    When I {method} {endpoint}")

        status_match = re.search(r"(\d{3})", text)
        if status_match:
            lines.append(
                f"    Then http response code should be {status_match.group(1)}"
            )
        else:
            lines.append("    Then http response code should be 200")

        lines.append("    And http response body should be valid json")
        return lines

    def _generate_scenario_name(
        self, story: UserStory, ac: AcceptanceCriteria, index: int
    ) -> str:
        """Generate a meaningful scenario name."""
        if ac.when:
            text = ac.when.strip()
            if text.lower().startswith("when "):
                text = text[5:]
            return self._sanitize_scenario_name(text)

        if ac.raw_text:
            text = ac.raw_text.strip().split("\n")[0]
            return self._sanitize_scenario_name(text)

        return f"{story.summary} - Scenario {index}"

    def _sanitize_scenario_name(self, text: str) -> str:
        """Sanitize text for use as a scenario name."""
        text = re.sub(r"[^\w\s-]", "", text)
        text = text.strip()
        if len(text) > 80:
            text = text[:77] + "..."
        return text if text else "Unnamed Scenario"

    def _story_to_filename(self, story: UserStory) -> str:
        """Convert a user story to a feature file name."""
        name = re.sub(r"[^a-zA-Z0-9]+", "-", story.summary).strip("-").lower()
        return f"{story.key.lower()}-{name}.feature"

    def _sanitize_step_text(self, text: str) -> str:
        """Sanitize text for use in a Gherkin step."""
        text = text.strip().rstrip(".")
        if len(text) > 120:
            text = text[:117] + "..."
        return text

    def _is_ui_related(self, text: str) -> bool:
        """Check if the text relates to UI interactions."""
        ui_keywords = [
            "page", "button", "click", "form", "login", "screen",
            "navigate", "browser", "display", "visible", "ui",
            "input", "dropdown", "checkbox", "modal", "dialog",
            "menu", "tab", "link", "submit", "upload"
        ]
        text_lower = text.lower()
        return any(kw in text_lower for kw in ui_keywords)

    def _is_api_related(self, text: str) -> bool:
        """Check if the text relates to API interactions."""
        api_keywords = [
            "api", "endpoint", "rest", "http", "request", "response",
            "get", "post", "put", "delete", "patch", "json",
            "status code", "header", "payload", "url"
        ]
        text_lower = text.lower()
        return any(kw in text_lower for kw in api_keywords)
