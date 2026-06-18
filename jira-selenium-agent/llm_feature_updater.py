"""LLM-based Feature File Updater.

Uses an LLM model to analyze code changes and automatically update
Gherkin feature files when source code is modified for an existing user story.
"""

import json
import logging
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import requests

logger = logging.getLogger(__name__)


@dataclass
class CodeChange:
    """Represents a code change from a git commit."""
    file_path: str
    change_type: str  # added, modified, deleted, renamed
    diff_content: str
    added_lines: list[str] = field(default_factory=list)
    removed_lines: list[str] = field(default_factory=list)


@dataclass
class FeatureUpdateResult:
    """Result of an LLM-based feature file update."""
    story_key: str
    feature_file: str
    original_content: str
    updated_content: str
    changes_summary: str
    llm_model: str
    confidence: float = 0.0


class LLMClient:
    """Client for interacting with LLM APIs (OpenAI-compatible)."""

    def __init__(
        self,
        api_key: str = None,
        api_url: str = None,
        model: str = None,
    ):
        self.api_key = api_key or os.getenv("LLM_API_KEY", "")
        self.api_url = api_url or os.getenv(
            "LLM_API_URL", "https://api.openai.com/v1/chat/completions"
        )
        self.model = model or os.getenv("LLM_MODEL", "gpt-4")
        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.3"))

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Send a prompt to the LLM and get a response.

        Args:
            system_prompt: System-level instructions.
            user_prompt: User prompt with context.

        Returns:
            The LLM's response text.
        """
        if not self.api_key:
            logger.warning("LLM API key not configured. Using template-based fallback.")
            return ""

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": self.temperature,
            "max_tokens": 4000,
        }

        try:
            response = requests.post(
                self.api_url, headers=headers, json=payload, timeout=60
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except requests.RequestException as e:
            logger.error("LLM API request failed: %s", e)
            return ""
        except (KeyError, IndexError) as e:
            logger.error("Unexpected LLM response format: %s", e)
            return ""


class LLMFeatureUpdater:
    """Updates Gherkin feature files using LLM analysis of code changes."""

    SYSTEM_PROMPT = """You are a BDD test automation expert. Your task is to update Gherkin feature files
based on code changes. You understand:
- Gherkin syntax (Feature, Scenario, Given/When/Then steps)
- How code changes map to test behavior changes
- REST API patterns (endpoints, request/response structures)
- UI interaction patterns (page navigation, form submission, etc.)

Rules:
1. Preserve existing scenarios that are still valid
2. Update scenarios that are affected by the code changes
3. Add new scenarios for new functionality
4. Remove scenarios for deleted functionality
5. Keep the Gherkin syntax valid and well-formatted
6. Maintain tags and metadata
7. Use concrete, meaningful step descriptions
8. Return ONLY the complete updated feature file content, no explanations"""

    def __init__(self, llm_client: LLMClient = None):
        self.llm = llm_client or LLMClient()

    def update_feature_from_changes(
        self,
        story_key: str,
        current_feature: str,
        code_changes: list[CodeChange],
        story_summary: str = "",
    ) -> FeatureUpdateResult:
        """Update a feature file based on code changes using LLM.

        Args:
            story_key: The Jira story key.
            current_feature: Current feature file content.
            code_changes: List of code changes from the commit.
            story_summary: Summary of the user story.

        Returns:
            FeatureUpdateResult with the updated content.
        """
        user_prompt = self._build_update_prompt(
            story_key, current_feature, code_changes, story_summary
        )

        llm_response = self.llm.generate(self.SYSTEM_PROMPT, user_prompt)

        if llm_response:
            updated_content = self._extract_feature_content(llm_response)
            changes_summary = self._summarize_changes(
                current_feature, updated_content
            )
        else:
            updated_content = self._template_based_update(
                current_feature, code_changes, story_key
            )
            changes_summary = "Updated using template-based fallback (no LLM)"

        return FeatureUpdateResult(
            story_key=story_key,
            feature_file="",
            original_content=current_feature,
            updated_content=updated_content,
            changes_summary=changes_summary,
            llm_model=self.llm.model if llm_response else "template-fallback",
            confidence=0.8 if llm_response else 0.5,
        )

    def generate_feature_from_story(
        self, story_key: str, summary: str, description: str
    ) -> str:
        """Generate a new feature file from a user story using LLM.

        Args:
            story_key: The Jira story key.
            summary: Story summary.
            description: Story description with acceptance criteria.

        Returns:
            Generated Gherkin feature content.
        """
        user_prompt = f"""Generate a complete Gherkin feature file for this user story:

Story Key: {story_key}
Summary: {summary}
Description:
{description}

Requirements:
- Include appropriate tags (@{story_key.replace('-', '_')}, priority, component tags)
- Add Background section if applicable
- Create scenarios from acceptance criteria
- Use Given/When/Then steps with clear, testable descriptions
- Include both positive and negative test scenarios where appropriate
- For API stories, use REST API step patterns (e.g., "When I POST /api/endpoint")
- For UI stories, use Selenium-compatible step patterns (e.g., "When the user clicks on...")

Return only the complete .feature file content."""

        response = self.llm.generate(self.SYSTEM_PROMPT, user_prompt)

        if response:
            return self._extract_feature_content(response)

        return self._generate_template_feature(story_key, summary, description)

    def analyze_impact(
        self, code_changes: list[CodeChange], feature_files: dict[str, str]
    ) -> dict[str, list[str]]:
        """Analyze which feature files are impacted by code changes.

        Args:
            code_changes: List of code changes.
            feature_files: Dict mapping story_key to feature file content.

        Returns:
            Dict mapping story_key to list of impacted scenario names.
        """
        impact_map = {}

        change_keywords = set()
        for change in code_changes:
            keywords = self._extract_keywords_from_diff(change.diff_content)
            change_keywords.update(keywords)

        for story_key, feature_content in feature_files.items():
            impacted_scenarios = []
            scenarios = self._parse_scenarios(feature_content)

            for scenario_name, scenario_text in scenarios:
                scenario_keywords = set(
                    re.findall(r"\b\w+\b", scenario_text.lower())
                )
                overlap = change_keywords & scenario_keywords
                if len(overlap) >= 2:
                    impacted_scenarios.append(scenario_name)

            if impacted_scenarios:
                impact_map[story_key] = impacted_scenarios

        return impact_map

    def _build_update_prompt(
        self,
        story_key: str,
        current_feature: str,
        code_changes: list[CodeChange],
        story_summary: str,
    ) -> str:
        """Build the LLM prompt for feature file update."""
        changes_text = ""
        for change in code_changes:
            changes_text += f"\n--- {change.file_path} ({change.change_type}) ---\n"
            changes_text += change.diff_content[:2000]
            changes_text += "\n"

        return f"""Update the following Gherkin feature file based on the code changes below.

Story Key: {story_key}
Story Summary: {story_summary}

CURRENT FEATURE FILE:
```gherkin
{current_feature}
```

CODE CHANGES:
{changes_text}

Instructions:
- Analyze the code changes to understand what behavior changed
- Update existing scenarios to reflect the new behavior
- Add new scenarios if new functionality was added
- Remove scenarios if functionality was removed
- Keep the feature file well-structured and valid
- Preserve tags and metadata
- Return the COMPLETE updated feature file"""

    def _extract_feature_content(self, llm_response: str) -> str:
        """Extract feature file content from LLM response."""
        gherkin_match = re.search(
            r"```(?:gherkin)?\s*\n(.*?)```", llm_response, re.DOTALL
        )
        if gherkin_match:
            return gherkin_match.group(1).strip()

        if "Feature:" in llm_response:
            feature_start = llm_response.index("Feature:")
            lines = llm_response[feature_start:].split("\n")
            feature_lines = []
            for line in lines:
                if line.strip().startswith("```"):
                    break
                feature_lines.append(line)
            return "\n".join(feature_lines).strip()

        return llm_response.strip()

    def _summarize_changes(self, original: str, updated: str) -> str:
        """Summarize the differences between original and updated feature."""
        original_scenarios = set(
            re.findall(r"Scenario(?:\s+Outline)?:\s*(.+)", original)
        )
        updated_scenarios = set(
            re.findall(r"Scenario(?:\s+Outline)?:\s*(.+)", updated)
        )

        added = updated_scenarios - original_scenarios
        removed = original_scenarios - updated_scenarios
        kept = original_scenarios & updated_scenarios

        parts = []
        if added:
            parts.append(f"Added scenarios: {', '.join(added)}")
        if removed:
            parts.append(f"Removed scenarios: {', '.join(removed)}")
        if kept:
            parts.append(f"Scenarios preserved/updated: {len(kept)}")

        return "; ".join(parts) if parts else "No significant changes detected"

    def _template_based_update(
        self,
        current_feature: str,
        code_changes: list[CodeChange],
        story_key: str,
    ) -> str:
        """Fallback: update feature using template-based logic when LLM is unavailable."""
        lines = current_feature.split("\n")
        new_scenarios = []

        for change in code_changes:
            if change.change_type == "added":
                new_scenarios.extend(
                    self._infer_scenarios_from_code(change, story_key)
                )
            elif change.change_type == "modified":
                pass

        if new_scenarios:
            lines.append("")
            lines.append(
                f"  # Auto-generated scenarios from code changes (template-based)"
            )
            lines.extend(new_scenarios)

        return "\n".join(lines)

    def _infer_scenarios_from_code(
        self, change: CodeChange, story_key: str
    ) -> list[str]:
        """Infer new scenarios from added code."""
        scenarios = []

        endpoint_matches = re.findall(
            r'@(Get|Post|Put|Delete|Patch)Mapping\s*\(\s*"([^"]+)"',
            change.diff_content,
        )
        for method, path in endpoint_matches:
            scenarios.extend([
                "",
                f"  Scenario: {method.upper()} {path} endpoint",
                f"    Given http baseUri is /api/",
                f"    When I {method.upper()} {path}",
                f"    Then http response code should be 200",
                f"    And http response body should be valid json",
            ])

        method_matches = re.findall(
            r"(?:public|private|protected)\s+\w+\s+(\w+)\s*\(", change.diff_content
        )
        for method_name in method_matches:
            if method_name in ("main", "toString", "equals", "hashCode"):
                continue
            readable = re.sub(r"([A-Z])", r" \1", method_name).strip().lower()
            scenarios.extend([
                "",
                f"  Scenario: Verify {readable}",
                f"    Given the system is in the expected state",
                f"    When the {readable} action is performed",
                f"    Then the expected result is achieved",
            ])

        return scenarios

    def _generate_template_feature(
        self, story_key: str, summary: str, description: str
    ) -> str:
        """Generate feature file using templates when LLM is unavailable."""
        tag = story_key.replace("-", "_")
        lines = [
            f"@{tag}",
            f"Feature: {summary}",
            f"  # Jira Story: {story_key}",
            "",
        ]

        if description:
            for line in description.split("\n"):
                stripped = line.strip()
                if stripped:
                    lines.append(f"  # {stripped}")
            lines.append("")

        lines.extend([
            f"  Scenario: Verify {summary}",
            f"    Given the system is ready",
            f"    When the user performs the action",
            f"    Then the expected outcome is achieved",
        ])

        return "\n".join(lines)

    def _extract_keywords_from_diff(self, diff: str) -> set[str]:
        """Extract meaningful keywords from a diff."""
        words = re.findall(r"\b[a-zA-Z]{3,}\b", diff.lower())
        stopwords = {
            "the", "and", "for", "with", "from", "this", "that", "import",
            "public", "private", "protected", "static", "void", "class",
            "return", "string", "int", "boolean", "new", "null", "true", "false",
        }
        return set(words) - stopwords

    def _parse_scenarios(self, feature_content: str) -> list[tuple[str, str]]:
        """Parse scenarios from feature file content."""
        scenarios = []
        current_name = ""
        current_lines = []

        for line in feature_content.split("\n"):
            stripped = line.strip()
            if stripped.startswith("Scenario:") or stripped.startswith(
                "Scenario Outline:"
            ):
                if current_name:
                    scenarios.append((current_name, "\n".join(current_lines)))
                current_name = stripped.split(":", 1)[1].strip()
                current_lines = [stripped]
            elif current_name:
                current_lines.append(stripped)

        if current_name:
            scenarios.append((current_name, "\n".join(current_lines)))

        return scenarios
