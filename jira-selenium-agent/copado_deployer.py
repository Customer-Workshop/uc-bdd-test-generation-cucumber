"""Copado CI/CD Integration.

Deploys test results and feature files to Copado, triggers Copado pipelines,
and publishes executed test reports into Copado's test execution framework.
"""

import json
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import requests

from config import AgentConfig
from report_generator import TestExecutionReport

logger = logging.getLogger(__name__)


@dataclass
class CopadoConfig:
    """Copado connection configuration."""
    instance_url: str = os.getenv("COPADO_INSTANCE_URL", "")
    api_token: str = os.getenv("COPADO_API_TOKEN", "")
    org_id: str = os.getenv("COPADO_ORG_ID", "")
    pipeline_id: str = os.getenv("COPADO_PIPELINE_ID", "")
    environment_id: str = os.getenv("COPADO_ENVIRONMENT_ID", "")
    credential_id: str = os.getenv("COPADO_CREDENTIAL_ID", "")
    api_version: str = os.getenv("COPADO_API_VERSION", "v2")


@dataclass
class CopadoTestResult:
    """A single test result in Copado format."""
    test_name: str
    test_class: str
    status: str  # Pass, Fail, Skip
    duration_seconds: float = 0.0
    error_message: str = ""
    stack_trace: str = ""
    story_key: str = ""


@dataclass
class CopadoDeploymentResult:
    """Result of a Copado deployment."""
    deployment_id: str = ""
    status: str = ""
    message: str = ""
    report_url: str = ""
    test_results_url: str = ""


class CopadoClient:
    """Client for Copado REST API interactions."""

    def __init__(self, config: CopadoConfig = None):
        self.config = config or CopadoConfig()
        self._session = requests.Session()
        if self.config.api_token:
            self._session.headers.update({
                "Authorization": f"Bearer {self.config.api_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            })

    @property
    def _base_url(self) -> str:
        return f"{self.config.instance_url}/services/apexrest/copado/{self.config.api_version}"

    @property
    def _sf_api_url(self) -> str:
        return f"{self.config.instance_url}/services/data/v58.0"

    def is_configured(self) -> bool:
        """Check if Copado credentials are configured."""
        return bool(self.config.instance_url and self.config.api_token)

    def create_test_run(
        self, name: str, environment: str, story_keys: list[str] = None
    ) -> str:
        """Create a new test run in Copado.

        Args:
            name: Test run name.
            environment: Target environment.
            story_keys: Related user story keys.

        Returns:
            Test run ID.
        """
        payload = {
            "Name": name,
            "copado__Environment__c": environment or self.config.environment_id,
            "copado__Status__c": "In Progress",
            "copado__Type__c": "BDD Automated Test",
            "Description__c": f"Auto-generated BDD test run for stories: {', '.join(story_keys or [])}",
        }

        try:
            response = self._session.post(
                f"{self._sf_api_url}/sobjects/copado__Test_Run__c",
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            result = response.json()
            test_run_id = result.get("id", "")
            logger.info("Created Copado test run: %s", test_run_id)
            return test_run_id
        except requests.RequestException as e:
            logger.error("Failed to create Copado test run: %s", e)
            return ""

    def upload_test_results(
        self, test_run_id: str, results: list[CopadoTestResult]
    ) -> bool:
        """Upload test results to a Copado test run.

        Args:
            test_run_id: The Copado test run ID.
            results: List of test results.

        Returns:
            True if upload succeeded.
        """
        records = []
        for r in results:
            records.append({
                "copado__Test_Run__c": test_run_id,
                "copado__Test_Name__c": r.test_name,
                "copado__Test_Class__c": r.test_class,
                "copado__Status__c": r.status,
                "copado__Duration__c": r.duration_seconds,
                "copado__Error_Message__c": r.error_message[:32000] if r.error_message else "",
                "copado__Stack_Trace__c": r.stack_trace[:32000] if r.stack_trace else "",
            })

        payload = {"records": records}

        try:
            response = self._session.post(
                f"{self._sf_api_url}/composite/sobjects/copado__Test_Result__c",
                json=payload,
                timeout=60,
            )
            response.raise_for_status()
            logger.info("Uploaded %d test results to Copado test run %s", len(results), test_run_id)
            return True
        except requests.RequestException as e:
            logger.error("Failed to upload test results: %s", e)
            return False

    def update_test_run_status(self, test_run_id: str, status: str) -> bool:
        """Update the status of a test run.

        Args:
            test_run_id: The Copado test run ID.
            status: New status (Passed, Failed, In Progress).

        Returns:
            True if update succeeded.
        """
        payload = {"copado__Status__c": status}

        try:
            response = self._session.patch(
                f"{self._sf_api_url}/sobjects/copado__Test_Run__c/{test_run_id}",
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            logger.info("Updated Copado test run %s status to: %s", test_run_id, status)
            return True
        except requests.RequestException as e:
            logger.error("Failed to update test run status: %s", e)
            return False

    def trigger_pipeline(self, pipeline_id: str = None) -> str:
        """Trigger a Copado deployment pipeline.

        Args:
            pipeline_id: Pipeline ID to trigger. Uses config default if not provided.

        Returns:
            Deployment ID.
        """
        pid = pipeline_id or self.config.pipeline_id
        payload = {
            "copado__Pipeline__c": pid,
            "copado__Status__c": "Scheduled",
        }

        try:
            response = self._session.post(
                f"{self._sf_api_url}/sobjects/copado__Deployment__c",
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            result = response.json()
            deployment_id = result.get("id", "")
            logger.info("Triggered Copado pipeline %s, deployment: %s", pid, deployment_id)
            return deployment_id
        except requests.RequestException as e:
            logger.error("Failed to trigger Copado pipeline: %s", e)
            return ""

    def attach_test_report(
        self, parent_id: str, report_path: str, report_name: str
    ) -> bool:
        """Attach a test report file to a Copado record.

        Args:
            parent_id: Salesforce record ID to attach to.
            report_path: Path to the report file.
            report_name: Name for the attachment.

        Returns:
            True if attachment succeeded.
        """
        report_file = Path(report_path)
        if not report_file.exists():
            logger.error("Report file not found: %s", report_path)
            return False

        import base64
        content = base64.b64encode(report_file.read_bytes()).decode("utf-8")

        payload = {
            "ParentId": parent_id,
            "Name": report_name,
            "Body": content,
            "ContentType": self._get_content_type(report_file.suffix),
        }

        try:
            response = self._session.post(
                f"{self._sf_api_url}/sobjects/Attachment",
                json=payload,
                timeout=60,
            )
            response.raise_for_status()
            logger.info("Attached report %s to %s", report_name, parent_id)
            return True
        except requests.RequestException as e:
            logger.error("Failed to attach report: %s", e)
            return False

    def get_deployment_status(self, deployment_id: str) -> dict:
        """Get the status of a deployment.

        Args:
            deployment_id: The deployment ID.

        Returns:
            Deployment status dict.
        """
        try:
            response = self._session.get(
                f"{self._sf_api_url}/sobjects/copado__Deployment__c/{deployment_id}",
                timeout=30,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error("Failed to get deployment status: %s", e)
            return {}

    def _get_content_type(self, suffix: str) -> str:
        """Get MIME content type from file extension."""
        types = {
            ".html": "text/html",
            ".json": "application/json",
            ".xml": "application/xml",
            ".txt": "text/plain",
            ".csv": "text/csv",
            ".png": "image/png",
        }
        return types.get(suffix, "application/octet-stream")


class CopadoDeployer:
    """Deploys BDD test results to Copado CI/CD pipeline."""

    def __init__(self, config: AgentConfig):
        self.config = config
        self.copado_config = CopadoConfig()
        self.client = CopadoClient(self.copado_config)

    def deploy_test_results(
        self,
        report: TestExecutionReport,
        report_files: dict[str, str],
        story_keys: list[str] = None,
    ) -> CopadoDeploymentResult:
        """Deploy test execution results to Copado.

        Creates a test run, uploads results, attaches reports,
        and optionally triggers the deployment pipeline.

        Args:
            report: The test execution report.
            report_files: Dict of format -> file path for generated reports.
            story_keys: Related story keys.

        Returns:
            CopadoDeploymentResult with deployment details.
        """
        result = CopadoDeploymentResult()

        if not self.client.is_configured():
            logger.info("Copado not configured. Generating local Copado-format report.")
            local_report = self._generate_copado_local_report(report, report_files)
            result.status = "local"
            result.message = f"Local Copado report: {local_report}"
            result.report_url = str(local_report)
            return result

        test_run_name = f"BDD Test Run - {report.run_id}"
        test_run_id = self.client.create_test_run(
            name=test_run_name,
            environment=report.environment,
            story_keys=story_keys or [],
        )

        if not test_run_id:
            result.status = "failed"
            result.message = "Failed to create Copado test run"
            return result

        copado_results = self._convert_to_copado_results(report)
        self.client.upload_test_results(test_run_id, copado_results)

        for fmt, path in report_files.items():
            self.client.attach_test_report(
                test_run_id, path, f"bdd-report-{report.run_id}.{fmt}"
            )

        final_status = "Passed" if report.failed_scenarios == 0 else "Failed"
        self.client.update_test_run_status(test_run_id, final_status)

        if self.copado_config.pipeline_id and report.failed_scenarios == 0:
            deployment_id = self.client.trigger_pipeline()
            result.deployment_id = deployment_id

        result.status = final_status.lower()
        result.message = (
            f"Copado test run {test_run_id}: {report.passed_scenarios} passed, "
            f"{report.failed_scenarios} failed"
        )
        result.test_results_url = (
            f"{self.copado_config.instance_url}/{test_run_id}"
        )

        return result

    def _convert_to_copado_results(
        self, report: TestExecutionReport
    ) -> list[CopadoTestResult]:
        """Convert TestExecutionReport to Copado test results."""
        results = []

        for feature in report.features:
            for scenario in feature.scenarios:
                status_map = {"passed": "Pass", "failed": "Fail", "skipped": "Skip"}

                error_msg = ""
                stack_trace = ""
                for step in scenario.steps:
                    if step.status == "failed":
                        error_msg = f"{step.step_type} {step.step_text}: {step.error_message}"
                        stack_trace = step.error_message

                results.append(CopadoTestResult(
                    test_name=scenario.name,
                    test_class=f"{feature.story_key}.{feature.name}",
                    status=status_map.get(scenario.status, "Skip"),
                    duration_seconds=scenario.duration_ms / 1000,
                    error_message=error_msg,
                    stack_trace=stack_trace,
                    story_key=feature.story_key,
                ))

        return results

    def _generate_copado_local_report(
        self,
        report: TestExecutionReport,
        report_files: dict[str, str],
    ) -> Path:
        """Generate a Copado-compatible report locally when not connected."""
        copado_report = {
            "testRunName": f"BDD Test Run - {report.run_id}",
            "timestamp": report.timestamp,
            "environment": report.environment,
            "status": "Passed" if report.failed_scenarios == 0 else "Failed",
            "summary": {
                "totalTests": report.total_scenarios,
                "passed": report.passed_scenarios,
                "failed": report.failed_scenarios,
                "skipped": report.skipped_scenarios,
                "passRate": round(report.pass_rate, 2),
                "duration": report.total_duration_ms,
            },
            "testResults": [],
            "reportFiles": report_files,
            "copadoMetadata": {
                "format": "copado-test-result-v2",
                "source": "jira-selenium-gherkin-agent",
                "pipelineReady": True,
            },
        }

        for feature in report.features:
            for scenario in feature.scenarios:
                status_map = {"passed": "Pass", "failed": "Fail", "skipped": "Skip"}

                steps_detail = []
                for step in scenario.steps:
                    steps_detail.append({
                        "keyword": step.step_type,
                        "name": step.step_text,
                        "status": step.status,
                        "duration": step.duration_ms,
                        "error": step.error_message,
                    })

                copado_report["testResults"].append({
                    "testName": scenario.name,
                    "testClass": f"{feature.story_key}.{feature.name}",
                    "status": status_map.get(scenario.status, "Skip"),
                    "duration": scenario.duration_ms / 1000,
                    "storyKey": feature.story_key,
                    "tags": scenario.tags,
                    "steps": steps_detail,
                })

        report_dir = Path("test-reports")
        report_dir.mkdir(parents=True, exist_ok=True)
        report_path = report_dir / f"copado-report-{report.run_id}.json"
        report_path.write_text(json.dumps(copado_report, indent=2), encoding="utf-8")
        logger.info("Local Copado report generated: %s", report_path)
        return report_path
