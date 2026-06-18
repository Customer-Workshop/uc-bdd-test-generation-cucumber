"""Git Commit Watcher Agent.

Monitors GitHub repository for commits related to existing user stories.
When a commit references a story key, automatically updates the corresponding
Gherkin feature file using the LLM model and triggers re-execution.
"""

import json
import logging
import os
import re
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import requests

from config import AgentConfig
from gherkin_generator import GherkinGenerator
from jira_client import JiraClient, UserStory
from llm_feature_updater import CodeChange, LLMClient, LLMFeatureUpdater

logger = logging.getLogger(__name__)


@dataclass
class CommitInfo:
    """Represents a git commit."""
    sha: str
    message: str
    author: str
    timestamp: str
    files_changed: list[str] = field(default_factory=list)
    story_keys: list[str] = field(default_factory=list)


class GitCommitWatcher:
    """Watches for git commits and auto-updates feature files.

    Flow:
    1. Monitor repo for new commits (polling or webhook)
    2. Extract story keys from commit messages
    3. Get the code diff for the commit
    4. Use LLM to analyze changes and update feature files
    5. Trigger re-execution of affected tests
    """

    STORY_KEY_PATTERN = re.compile(r"([A-Z][A-Z0-9]+-\d+)")

    def __init__(
        self,
        config: AgentConfig,
        repo_path: str = ".",
        github_token: str = None,
        github_repo: str = None,
    ):
        self.config = config
        self.repo_path = Path(repo_path).resolve()
        self.github_token = github_token or os.getenv("GITHUB_TOKEN", "")
        self.github_repo = github_repo or os.getenv("GITHUB_REPO", "")
        self.llm_updater = LLMFeatureUpdater()
        self.gherkin_generator = GherkinGenerator(config.output)
        self._last_processed_sha = ""
        self._feature_dir = Path(config.output.output_dir)

    def watch(self, interval_seconds: int = 30, max_iterations: int = None):
        """Start watching for new commits (polling mode).

        Args:
            interval_seconds: Polling interval in seconds.
            max_iterations: Max iterations before stopping (None = infinite).
        """
        logger.info(
            "Starting Git Commit Watcher (polling every %ds)...", interval_seconds
        )
        self._last_processed_sha = self._get_latest_commit_sha()
        logger.info("Starting from commit: %s", self._last_processed_sha)

        iteration = 0
        while max_iterations is None or iteration < max_iterations:
            try:
                new_commits = self._check_for_new_commits()
                if new_commits:
                    logger.info("Found %d new commit(s)", len(new_commits))
                    for commit in new_commits:
                        self._process_commit(commit)
                    self._last_processed_sha = new_commits[-1].sha
                else:
                    logger.debug("No new commits found.")

            except Exception as e:
                logger.error("Error during watch cycle: %s", e)

            iteration += 1
            if max_iterations is None or iteration < max_iterations:
                time.sleep(interval_seconds)

        logger.info("Git Commit Watcher stopped.")

    def process_single_commit(self, commit_sha: str) -> list[str]:
        """Process a single commit by SHA.

        Args:
            commit_sha: The commit SHA to process.

        Returns:
            List of updated feature file paths.
        """
        commit = self._get_commit_info(commit_sha)
        if not commit:
            logger.error("Could not fetch commit: %s", commit_sha)
            return []

        return self._process_commit(commit)

    def process_commit_range(self, from_sha: str, to_sha: str) -> list[str]:
        """Process a range of commits.

        Args:
            from_sha: Starting commit SHA (exclusive).
            to_sha: Ending commit SHA (inclusive).

        Returns:
            List of all updated feature file paths.
        """
        commits = self._get_commits_in_range(from_sha, to_sha)
        all_updated = []
        for commit in commits:
            updated = self._process_commit(commit)
            all_updated.extend(updated)
        return all_updated

    def setup_webhook_handler(self, port: int = 9090) -> None:
        """Set up a simple HTTP webhook handler for GitHub push events.

        Creates a lightweight HTTP server that listens for GitHub webhook
        push events and processes commits automatically.

        Args:
            port: Port to listen on.
        """
        from http.server import HTTPServer, BaseHTTPRequestHandler

        watcher = self

        class WebhookHandler(BaseHTTPRequestHandler):
            def do_POST(self):
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length)
                payload = json.loads(body)

                event_type = self.headers.get("X-GitHub-Event", "")

                if event_type == "push":
                    commits = payload.get("commits", [])
                    for commit_data in commits:
                        commit = CommitInfo(
                            sha=commit_data["id"],
                            message=commit_data["message"],
                            author=commit_data["author"]["name"],
                            timestamp=commit_data["timestamp"],
                            files_changed=(
                                commit_data.get("added", [])
                                + commit_data.get("modified", [])
                                + commit_data.get("removed", [])
                            ),
                        )
                        commit.story_keys = watcher._extract_story_keys(
                            commit.message
                        )
                        if commit.story_keys:
                            watcher._process_commit(commit)

                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"OK")

            def log_message(self, format, *args):
                logger.debug(format, *args)

        server = HTTPServer(("0.0.0.0", port), WebhookHandler)
        logger.info("Webhook handler listening on port %d", port)
        server.serve_forever()

    def _process_commit(self, commit: CommitInfo) -> list[str]:
        """Process a single commit: update affected feature files."""
        logger.info(
            "Processing commit %s: %s", commit.sha[:8], commit.message.split("\n")[0]
        )

        story_keys = commit.story_keys or self._extract_story_keys(commit.message)

        if not story_keys:
            logger.info("No story keys found in commit message. Skipping.")
            return []

        logger.info("Story keys found: %s", story_keys)

        code_changes = self._get_code_changes(commit.sha)
        updated_files = []

        for story_key in story_keys:
            feature_path = self._find_feature_file(story_key)

            if feature_path and feature_path.exists():
                current_content = feature_path.read_text(encoding="utf-8")
                result = self.llm_updater.update_feature_from_changes(
                    story_key=story_key,
                    current_feature=current_content,
                    code_changes=code_changes,
                    story_summary=commit.message,
                )

                if result.updated_content and result.updated_content != current_content:
                    feature_path.write_text(
                        result.updated_content, encoding="utf-8"
                    )
                    logger.info(
                        "Updated feature file for %s: %s (%s)",
                        story_key,
                        feature_path,
                        result.changes_summary,
                    )
                    updated_files.append(str(feature_path))

                    self._save_update_log(commit, story_key, result)
                else:
                    logger.info(
                        "No changes needed for %s feature file.", story_key
                    )
            else:
                logger.info(
                    "No existing feature file for %s. Consider generating one.",
                    story_key,
                )

        return updated_files

    def _check_for_new_commits(self) -> list[CommitInfo]:
        """Check for new commits since last processed."""
        try:
            result = subprocess.run(
                [
                    "git", "log",
                    f"{self._last_processed_sha}..HEAD",
                    "--format=%H|%s|%an|%aI",
                    "--no-merges",
                ],
                capture_output=True,
                text=True,
                cwd=str(self.repo_path),
            )

            if result.returncode != 0:
                subprocess.run(
                    ["git", "pull", "--rebase"],
                    capture_output=True,
                    cwd=str(self.repo_path),
                )
                result = subprocess.run(
                    [
                        "git", "log",
                        f"{self._last_processed_sha}..HEAD",
                        "--format=%H|%s|%an|%aI",
                        "--no-merges",
                    ],
                    capture_output=True,
                    text=True,
                    cwd=str(self.repo_path),
                )

            commits = []
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue
                parts = line.split("|", 3)
                if len(parts) >= 4:
                    commit = CommitInfo(
                        sha=parts[0],
                        message=parts[1],
                        author=parts[2],
                        timestamp=parts[3],
                    )
                    commit.story_keys = self._extract_story_keys(commit.message)
                    commits.append(commit)

            return list(reversed(commits))

        except Exception as e:
            logger.error("Failed to check for new commits: %s", e)
            return []

    def _get_commit_info(self, sha: str) -> Optional[CommitInfo]:
        """Get info about a specific commit."""
        try:
            msg_result = subprocess.run(
                ["git", "log", "-1", "--format=%H|%s|%an|%aI", sha],
                capture_output=True,
                text=True,
                cwd=str(self.repo_path),
            )

            files_result = subprocess.run(
                ["git", "diff-tree", "--no-commit-id", "-r", "--name-only", sha],
                capture_output=True,
                text=True,
                cwd=str(self.repo_path),
            )

            parts = msg_result.stdout.strip().split("|", 3)
            if len(parts) >= 4:
                commit = CommitInfo(
                    sha=parts[0],
                    message=parts[1],
                    author=parts[2],
                    timestamp=parts[3],
                    files_changed=files_result.stdout.strip().split("\n"),
                )
                commit.story_keys = self._extract_story_keys(commit.message)
                return commit

        except Exception as e:
            logger.error("Failed to get commit info: %s", e)

        return None

    def _get_commits_in_range(
        self, from_sha: str, to_sha: str
    ) -> list[CommitInfo]:
        """Get all commits in a range."""
        try:
            result = subprocess.run(
                [
                    "git", "log",
                    f"{from_sha}..{to_sha}",
                    "--format=%H|%s|%an|%aI",
                    "--no-merges",
                ],
                capture_output=True,
                text=True,
                cwd=str(self.repo_path),
            )

            commits = []
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue
                parts = line.split("|", 3)
                if len(parts) >= 4:
                    commit = CommitInfo(
                        sha=parts[0],
                        message=parts[1],
                        author=parts[2],
                        timestamp=parts[3],
                    )
                    commit.story_keys = self._extract_story_keys(commit.message)
                    commits.append(commit)

            return list(reversed(commits))

        except Exception as e:
            logger.error("Failed to get commit range: %s", e)
            return []

    def _get_code_changes(self, sha: str) -> list[CodeChange]:
        """Get code changes for a commit."""
        changes = []
        try:
            result = subprocess.run(
                ["git", "diff", f"{sha}~1", sha, "--name-status"],
                capture_output=True,
                text=True,
                cwd=str(self.repo_path),
            )

            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue
                parts = line.split("\t")
                if len(parts) >= 2:
                    status_map = {
                        "A": "added",
                        "M": "modified",
                        "D": "deleted",
                        "R": "renamed",
                    }
                    change_type = status_map.get(parts[0][0], "modified")
                    file_path = parts[-1]

                    diff_result = subprocess.run(
                        ["git", "diff", f"{sha}~1", sha, "--", file_path],
                        capture_output=True,
                        text=True,
                        cwd=str(self.repo_path),
                    )

                    added_lines = [
                        l[1:]
                        for l in diff_result.stdout.split("\n")
                        if l.startswith("+") and not l.startswith("+++")
                    ]
                    removed_lines = [
                        l[1:]
                        for l in diff_result.stdout.split("\n")
                        if l.startswith("-") and not l.startswith("---")
                    ]

                    changes.append(
                        CodeChange(
                            file_path=file_path,
                            change_type=change_type,
                            diff_content=diff_result.stdout[:5000],
                            added_lines=added_lines,
                            removed_lines=removed_lines,
                        )
                    )

        except Exception as e:
            logger.error("Failed to get code changes: %s", e)

        return changes

    def _extract_story_keys(self, message: str) -> list[str]:
        """Extract Jira story keys from a commit message."""
        return self.STORY_KEY_PATTERN.findall(message)

    def _find_feature_file(self, story_key: str) -> Optional[Path]:
        """Find the feature file for a story key."""
        key_lower = story_key.lower()
        key_underscore = story_key.replace("-", "_").lower()

        search_dirs = [
            self._feature_dir,
            self._feature_dir.parent,
            self.repo_path / "src" / "test" / "resources" / "features",
        ]

        for search_dir in search_dirs:
            if not search_dir.exists():
                continue
            for feature_file in search_dir.rglob("*.feature"):
                name = feature_file.stem.lower()
                if key_lower in name or key_underscore in name:
                    return feature_file

                content = feature_file.read_text(encoding="utf-8")
                if story_key in content:
                    return feature_file

        return None

    def _get_latest_commit_sha(self) -> str:
        """Get the latest commit SHA."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                cwd=str(self.repo_path),
            )
            return result.stdout.strip()
        except Exception:
            return ""

    def _save_update_log(self, commit: CommitInfo, story_key: str, result) -> None:
        """Save a log of the feature update."""
        log_dir = self._feature_dir.parent / "update-logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        log_entry = {
            "timestamp": commit.timestamp,
            "commit_sha": commit.sha,
            "commit_message": commit.message,
            "story_key": story_key,
            "changes_summary": result.changes_summary,
            "llm_model": result.llm_model,
            "confidence": result.confidence,
        }

        log_path = log_dir / f"{story_key}-updates.jsonl"
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")


class GitHubWebhookSetup:
    """Helper to set up GitHub webhook for commit watching."""

    def __init__(self, github_token: str, github_repo: str):
        self.token = github_token
        self.repo = github_repo
        self.api_url = f"https://api.github.com/repos/{github_repo}"

    def create_webhook(self, webhook_url: str, secret: str = "") -> dict:
        """Create a GitHub webhook for push events.

        Args:
            webhook_url: URL to receive webhook events.
            secret: Webhook secret for signature verification.

        Returns:
            Webhook creation response.
        """
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
        }

        payload = {
            "name": "web",
            "active": True,
            "events": ["push"],
            "config": {
                "url": webhook_url,
                "content_type": "json",
            },
        }

        if secret:
            payload["config"]["secret"] = secret

        response = requests.post(
            f"{self.api_url}/hooks",
            headers=headers,
            json=payload,
            timeout=30,
        )

        if response.status_code == 201:
            logger.info("Webhook created successfully.")
            return response.json()
        else:
            logger.error(
                "Failed to create webhook: %s %s",
                response.status_code,
                response.text,
            )
            return {}
