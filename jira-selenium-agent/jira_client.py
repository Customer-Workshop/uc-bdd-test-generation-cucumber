"""Jira integration module - fetches assigned user stories."""

import logging
from dataclasses import dataclass, field
from typing import Optional

from jira import JIRA
from jira.exceptions import JIRAError

from config import JiraConfig

logger = logging.getLogger(__name__)


@dataclass
class AcceptanceCriteria:
    """Represents a single acceptance criterion from a user story."""
    given: str = ""
    when: str = ""
    then: str = ""
    raw_text: str = ""


@dataclass
class UserStory:
    """Represents a Jira user story with parsed fields."""
    key: str
    summary: str
    description: str
    acceptance_criteria: list[AcceptanceCriteria] = field(default_factory=list)
    story_points: Optional[float] = None
    priority: str = "Medium"
    labels: list[str] = field(default_factory=list)
    status: str = ""
    assignee: str = ""
    components: list[str] = field(default_factory=list)
    epic_link: str = ""


class JiraClient:
    """Client for connecting to Jira and fetching user stories."""

    def __init__(self, config: JiraConfig):
        self.config = config
        self._jira = None

    def connect(self) -> bool:
        """Establish connection to Jira."""
        try:
            self._jira = JIRA(
                server=self.config.server_url,
                basic_auth=(self.config.username, self.config.api_token)
            )
            logger.info("Successfully connected to Jira: %s", self.config.server_url)
            return True
        except JIRAError as e:
            logger.error("Failed to connect to Jira: %s", e.text)
            return False

    def fetch_assigned_stories(self, status_filter: Optional[str] = None) -> list[UserStory]:
        """Fetch user stories assigned to the configured user.

        Args:
            status_filter: Optional JQL status filter (e.g., 'To Do', 'In Progress').

        Returns:
            List of UserStory objects.
        """
        if not self._jira:
            raise RuntimeError("Not connected to Jira. Call connect() first.")

        jql = self._build_jql(status_filter)
        logger.info("Fetching stories with JQL: %s", jql)

        try:
            issues = self._jira.search_issues(
                jql,
                maxResults=self.config.max_results,
                fields="summary,description,priority,labels,status,assignee,components,customfield_10016"
            )
        except JIRAError as e:
            logger.error("Failed to fetch stories: %s", e.text)
            return []

        stories = []
        for issue in issues:
            story = self._parse_issue(issue)
            stories.append(story)
            logger.info("Fetched story: %s - %s", story.key, story.summary)

        logger.info("Total stories fetched: %d", len(stories))
        return stories

    def fetch_story_by_key(self, key: str) -> Optional[UserStory]:
        """Fetch a single user story by its Jira key."""
        if not self._jira:
            raise RuntimeError("Not connected to Jira. Call connect() first.")

        try:
            issue = self._jira.issue(key)
            return self._parse_issue(issue)
        except JIRAError as e:
            logger.error("Failed to fetch story %s: %s", key, e.text)
            return None

    def _build_jql(self, status_filter: Optional[str] = None) -> str:
        """Build JQL query for fetching assigned user stories."""
        parts = [
            f'project = "{self.config.project_key}"',
            f'issuetype = "{self.config.story_issue_type}"',
        ]

        if self.config.assignee == "currentUser()":
            parts.append("assignee = currentUser()")
        else:
            parts.append(f'assignee = "{self.config.assignee}"')

        if status_filter:
            parts.append(f'status = "{status_filter}"')

        parts.append("ORDER BY priority DESC, created DESC")
        return " AND ".join(parts[:-1]) + " " + parts[-1]

    def _parse_issue(self, issue) -> UserStory:
        """Parse a Jira issue into a UserStory object."""
        fields = issue.fields
        description = fields.description or ""

        acceptance_criteria = self._extract_acceptance_criteria(description)

        components = [c.name for c in (fields.components or [])]

        story_points = getattr(fields, "customfield_10016", None)

        assignee_name = ""
        if fields.assignee:
            assignee_name = fields.assignee.displayName

        return UserStory(
            key=issue.key,
            summary=fields.summary,
            description=description,
            acceptance_criteria=acceptance_criteria,
            story_points=story_points,
            priority=fields.priority.name if fields.priority else "Medium",
            labels=fields.labels or [],
            status=fields.status.name if fields.status else "",
            assignee=assignee_name,
            components=components,
        )

    def _extract_acceptance_criteria(self, description: str) -> list[AcceptanceCriteria]:
        """Extract acceptance criteria from the story description.

        Supports multiple formats:
        - Given/When/Then blocks
        - Numbered acceptance criteria
        - Bullet-pointed acceptance criteria
        """
        if not description:
            return []

        criteria = []
        lines = description.strip().split("\n")

        current_ac = AcceptanceCriteria()
        in_ac_section = False

        for line in lines:
            stripped = line.strip().lower()

            if any(kw in stripped for kw in [
                "acceptance criteria", "ac:", "acceptance:", "criteria:"
            ]):
                in_ac_section = True
                continue

            if in_ac_section or any(
                stripped.startswith(kw) for kw in ["given ", "when ", "then ", "and "]
            ):
                in_ac_section = True

                if stripped.startswith("given "):
                    if current_ac.given or current_ac.when or current_ac.then:
                        criteria.append(current_ac)
                        current_ac = AcceptanceCriteria()
                    current_ac.given = line.strip()
                    current_ac.raw_text += line.strip() + "\n"
                elif stripped.startswith("when "):
                    current_ac.when = line.strip()
                    current_ac.raw_text += line.strip() + "\n"
                elif stripped.startswith("then "):
                    current_ac.then = line.strip()
                    current_ac.raw_text += line.strip() + "\n"
                elif stripped.startswith("and "):
                    if current_ac.then:
                        current_ac.then += "\n" + line.strip()
                    elif current_ac.when:
                        current_ac.when += "\n" + line.strip()
                    elif current_ac.given:
                        current_ac.given += "\n" + line.strip()
                    current_ac.raw_text += line.strip() + "\n"
                elif stripped.startswith(("-", "*", "•")) or (
                    len(stripped) > 1 and stripped[0].isdigit() and stripped[1] in ".)"
                ):
                    raw = line.strip().lstrip("-*•0123456789.) ")
                    if raw:
                        ac = AcceptanceCriteria(raw_text=raw)
                        criteria.append(ac)

        if current_ac.given or current_ac.when or current_ac.then or current_ac.raw_text:
            criteria.append(current_ac)

        if not criteria:
            criteria = self._extract_criteria_from_plain_text(description)

        return criteria

    def _extract_criteria_from_plain_text(self, description: str) -> list[AcceptanceCriteria]:
        """Fallback: extract criteria from unstructured description text."""
        criteria = []
        sentences = description.replace("\r\n", "\n").split(".")

        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 10:
                criteria.append(AcceptanceCriteria(raw_text=sentence))

        return criteria
