"""CI/CD Test Execution Report Generator.

Generates structured test execution reports in multiple formats
(HTML, JSON, JUnit XML) suitable for CI/CD pipeline integration.
"""

import json
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from xml.etree import ElementTree as ET

logger = logging.getLogger(__name__)


@dataclass
class StepResult:
    """Result of a single step execution."""
    step_type: str
    step_text: str
    status: str  # passed, failed, skipped, pending
    duration_ms: float = 0.0
    error_message: str = ""
    screenshot_path: str = ""


@dataclass
class ScenarioResult:
    """Result of a scenario execution."""
    name: str
    status: str  # passed, failed, skipped
    steps: list[StepResult] = field(default_factory=list)
    duration_ms: float = 0.0
    tags: list[str] = field(default_factory=list)


@dataclass
class FeatureResult:
    """Result of a feature file execution."""
    name: str
    story_key: str
    file_path: str
    status: str  # passed, failed, skipped
    scenarios: list[ScenarioResult] = field(default_factory=list)
    duration_ms: float = 0.0


@dataclass
class TestExecutionReport:
    """Complete test execution report."""
    run_id: str
    timestamp: str
    environment: str
    app_url: str
    features: list[FeatureResult] = field(default_factory=list)
    total_duration_ms: float = 0.0
    metadata: dict = field(default_factory=dict)

    @property
    def total_scenarios(self) -> int:
        return sum(len(f.scenarios) for f in self.features)

    @property
    def passed_scenarios(self) -> int:
        return sum(
            1 for f in self.features for s in f.scenarios if s.status == "passed"
        )

    @property
    def failed_scenarios(self) -> int:
        return sum(
            1 for f in self.features for s in f.scenarios if s.status == "failed"
        )

    @property
    def skipped_scenarios(self) -> int:
        return sum(
            1 for f in self.features for s in f.scenarios if s.status == "skipped"
        )

    @property
    def total_steps(self) -> int:
        return sum(
            len(s.steps) for f in self.features for s in f.scenarios
        )

    @property
    def passed_steps(self) -> int:
        return sum(
            1
            for f in self.features
            for s in f.scenarios
            for st in s.steps
            if st.status == "passed"
        )

    @property
    def pass_rate(self) -> float:
        if self.total_scenarios == 0:
            return 0.0
        return (self.passed_scenarios / self.total_scenarios) * 100


class ReportGenerator:
    """Generates test execution reports for CI/CD integration."""

    REPORT_DIR = "test-reports"

    def __init__(self, output_dir: str = None):
        self.output_dir = Path(output_dir or self.REPORT_DIR)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_report(
        self,
        report: TestExecutionReport,
        formats: list[str] = None,
    ) -> dict[str, str]:
        """Generate reports in multiple formats.

        Args:
            report: The test execution report data.
            formats: List of formats to generate. Defaults to all.

        Returns:
            Dict mapping format name to file path.
        """
        if formats is None:
            formats = ["json", "html", "junit_xml", "summary"]

        generated_files = {}

        for fmt in formats:
            if fmt == "json":
                path = self._generate_json(report)
                generated_files["json"] = str(path)
            elif fmt == "html":
                path = self._generate_html(report)
                generated_files["html"] = str(path)
            elif fmt == "junit_xml":
                path = self._generate_junit_xml(report)
                generated_files["junit_xml"] = str(path)
            elif fmt == "summary":
                path = self._generate_summary(report)
                generated_files["summary"] = str(path)

        logger.info("Reports generated: %s", generated_files)
        return generated_files

    def _generate_json(self, report: TestExecutionReport) -> Path:
        """Generate JSON report."""
        data = {
            "run_id": report.run_id,
            "timestamp": report.timestamp,
            "environment": report.environment,
            "app_url": report.app_url,
            "summary": {
                "total_features": len(report.features),
                "total_scenarios": report.total_scenarios,
                "passed": report.passed_scenarios,
                "failed": report.failed_scenarios,
                "skipped": report.skipped_scenarios,
                "pass_rate": round(report.pass_rate, 2),
                "total_steps": report.total_steps,
                "passed_steps": report.passed_steps,
                "duration_ms": report.total_duration_ms,
            },
            "features": [],
            "metadata": report.metadata,
        }

        for feature in report.features:
            feature_data = {
                "name": feature.name,
                "story_key": feature.story_key,
                "file_path": feature.file_path,
                "status": feature.status,
                "duration_ms": feature.duration_ms,
                "scenarios": [],
            }
            for scenario in feature.scenarios:
                scenario_data = {
                    "name": scenario.name,
                    "status": scenario.status,
                    "tags": scenario.tags,
                    "duration_ms": scenario.duration_ms,
                    "steps": [
                        {
                            "type": step.step_type,
                            "text": step.step_text,
                            "status": step.status,
                            "duration_ms": step.duration_ms,
                            "error": step.error_message,
                            "screenshot": step.screenshot_path,
                        }
                        for step in scenario.steps
                    ],
                }
                feature_data["scenarios"].append(scenario_data)
            data["features"].append(feature_data)

        path = self.output_dir / f"report-{report.run_id}.json"
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return path

    def _generate_html(self, report: TestExecutionReport) -> Path:
        """Generate HTML report."""
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test Execution Report - {report.run_id}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; color: #333; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 20px; }}
        .header h1 {{ font-size: 24px; margin-bottom: 10px; }}
        .header .meta {{ opacity: 0.9; font-size: 14px; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin-bottom: 20px; }}
        .summary-card {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center; }}
        .summary-card .number {{ font-size: 36px; font-weight: bold; }}
        .summary-card .label {{ font-size: 12px; text-transform: uppercase; color: #666; margin-top: 5px; }}
        .passed .number {{ color: #27ae60; }}
        .failed .number {{ color: #e74c3c; }}
        .skipped .number {{ color: #f39c12; }}
        .rate .number {{ color: #3498db; }}
        .feature {{ background: white; border-radius: 8px; margin-bottom: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); overflow: hidden; }}
        .feature-header {{ padding: 15px 20px; border-bottom: 1px solid #eee; display: flex; justify-content: space-between; align-items: center; }}
        .feature-header h2 {{ font-size: 18px; }}
        .badge {{ padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; text-transform: uppercase; }}
        .badge-passed {{ background: #d4edda; color: #155724; }}
        .badge-failed {{ background: #f8d7da; color: #721c24; }}
        .badge-skipped {{ background: #fff3cd; color: #856404; }}
        .scenario {{ padding: 12px 20px; border-bottom: 1px solid #f0f0f0; }}
        .scenario:last-child {{ border-bottom: none; }}
        .scenario-name {{ font-weight: 500; margin-bottom: 8px; display: flex; align-items: center; gap: 8px; }}
        .step {{ padding: 4px 0 4px 30px; font-size: 14px; color: #555; }}
        .step .step-status {{ display: inline-block; width: 18px; text-align: center; }}
        .step-passed .step-status {{ color: #27ae60; }}
        .step-failed .step-status {{ color: #e74c3c; }}
        .step-skipped .step-status {{ color: #f39c12; }}
        .error-msg {{ color: #e74c3c; font-size: 12px; padding-left: 48px; font-style: italic; }}
        .footer {{ text-align: center; padding: 20px; color: #999; font-size: 12px; }}
        .tag {{ display: inline-block; background: #e8f0fe; color: #1a73e8; padding: 2px 8px; border-radius: 3px; font-size: 11px; margin-right: 4px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Test Execution Report</h1>
            <div class="meta">
                <div>Run ID: {report.run_id}</div>
                <div>Timestamp: {report.timestamp}</div>
                <div>Environment: {report.environment}</div>
                <div>App URL: {report.app_url}</div>
                <div>Duration: {report.total_duration_ms:.0f}ms</div>
            </div>
        </div>

        <div class="summary">
            <div class="summary-card">
                <div class="number">{report.total_scenarios}</div>
                <div class="label">Total Scenarios</div>
            </div>
            <div class="summary-card passed">
                <div class="number">{report.passed_scenarios}</div>
                <div class="label">Passed</div>
            </div>
            <div class="summary-card failed">
                <div class="number">{report.failed_scenarios}</div>
                <div class="label">Failed</div>
            </div>
            <div class="summary-card skipped">
                <div class="number">{report.skipped_scenarios}</div>
                <div class="label">Skipped</div>
            </div>
            <div class="summary-card rate">
                <div class="number">{report.pass_rate:.1f}%</div>
                <div class="label">Pass Rate</div>
            </div>
        </div>
"""

        for feature in report.features:
            badge_class = f"badge-{feature.status}"
            html += f"""
        <div class="feature">
            <div class="feature-header">
                <h2>{feature.name} <small style="color:#999">({feature.story_key})</small></h2>
                <span class="badge {badge_class}">{feature.status}</span>
            </div>
"""
            for scenario in feature.scenarios:
                tags_html = "".join(
                    f'<span class="tag">{tag}</span>' for tag in scenario.tags
                )
                status_icon = {"passed": "&#10004;", "failed": "&#10008;", "skipped": "&#9888;"}.get(scenario.status, "?")
                html += f"""
            <div class="scenario">
                <div class="scenario-name">
                    <span class="badge badge-{scenario.status}">{status_icon}</span>
                    {scenario.name}
                    {tags_html}
                    <small style="color:#999">({scenario.duration_ms:.0f}ms)</small>
                </div>
"""
                for step in scenario.steps:
                    step_icon = {"passed": "&#10004;", "failed": "&#10008;", "skipped": "&#9888;"}.get(step.status, "?")
                    html += f"""
                <div class="step step-{step.status}">
                    <span class="step-status">{step_icon}</span>
                    <strong>{step.step_type}</strong> {step.step_text}
                    <small style="color:#999">({step.duration_ms:.0f}ms)</small>
                </div>
"""
                    if step.error_message:
                        html += f'                <div class="error-msg">{step.error_message}</div>\n'

                html += "            </div>\n"
            html += "        </div>\n"

        html += f"""
        <div class="footer">
            Generated by Jira-Selenium-Gherkin Agent | {report.timestamp}
        </div>
    </div>
</body>
</html>"""

        path = self.output_dir / f"report-{report.run_id}.html"
        path.write_text(html, encoding="utf-8")
        return path

    def _generate_junit_xml(self, report: TestExecutionReport) -> Path:
        """Generate JUnit XML report for CI/CD integration."""
        testsuites = ET.Element("testsuites")
        testsuites.set("name", f"BDD Test Suite - {report.run_id}")
        testsuites.set("time", str(report.total_duration_ms / 1000))
        testsuites.set("tests", str(report.total_scenarios))
        testsuites.set("failures", str(report.failed_scenarios))
        testsuites.set("skipped", str(report.skipped_scenarios))

        for feature in report.features:
            testsuite = ET.SubElement(testsuites, "testsuite")
            testsuite.set("name", feature.name)
            testsuite.set("tests", str(len(feature.scenarios)))
            testsuite.set("time", str(feature.duration_ms / 1000))
            testsuite.set(
                "failures",
                str(sum(1 for s in feature.scenarios if s.status == "failed")),
            )
            testsuite.set(
                "skipped",
                str(sum(1 for s in feature.scenarios if s.status == "skipped")),
            )

            properties = ET.SubElement(testsuite, "properties")
            prop = ET.SubElement(properties, "property")
            prop.set("name", "story_key")
            prop.set("value", feature.story_key)
            prop = ET.SubElement(properties, "property")
            prop.set("name", "feature_file")
            prop.set("value", feature.file_path)

            for scenario in feature.scenarios:
                testcase = ET.SubElement(testsuite, "testcase")
                testcase.set("name", scenario.name)
                testcase.set("classname", f"{feature.story_key}.{feature.name}")
                testcase.set("time", str(scenario.duration_ms / 1000))

                if scenario.status == "failed":
                    for step in scenario.steps:
                        if step.status == "failed":
                            failure = ET.SubElement(testcase, "failure")
                            failure.set("message", step.error_message or "Step failed")
                            failure.set("type", "AssertionError")
                            failure.text = (
                                f"{step.step_type} {step.step_text}\n"
                                f"Error: {step.error_message}"
                            )
                            break

                elif scenario.status == "skipped":
                    skipped = ET.SubElement(testcase, "skipped")
                    skipped.set("message", "Scenario skipped")

        tree = ET.ElementTree(testsuites)
        path = self.output_dir / f"report-{report.run_id}.xml"
        tree.write(str(path), encoding="unicode", xml_declaration=True)
        return path

    def _generate_summary(self, report: TestExecutionReport) -> Path:
        """Generate a plain text summary report."""
        lines = [
            "=" * 70,
            "  TEST EXECUTION SUMMARY",
            "=" * 70,
            "",
            f"  Run ID:       {report.run_id}",
            f"  Timestamp:    {report.timestamp}",
            f"  Environment:  {report.environment}",
            f"  App URL:      {report.app_url}",
            f"  Duration:     {report.total_duration_ms:.0f}ms",
            "",
            "-" * 70,
            f"  RESULTS: {report.passed_scenarios} passed | "
            f"{report.failed_scenarios} failed | "
            f"{report.skipped_scenarios} skipped | "
            f"{report.total_scenarios} total",
            f"  PASS RATE: {report.pass_rate:.1f}%",
            "-" * 70,
            "",
        ]

        for feature in report.features:
            status_icon = {"passed": "[PASS]", "failed": "[FAIL]", "skipped": "[SKIP]"}.get(
                feature.status, "[????]"
            )
            lines.append(
                f"  {status_icon} {feature.name} ({feature.story_key})"
            )
            for scenario in feature.scenarios:
                s_icon = {"passed": "  +", "failed": "  X", "skipped": "  -"}.get(
                    scenario.status, "  ?"
                )
                lines.append(f"    {s_icon} {scenario.name}")

                for step in scenario.steps:
                    if step.status == "failed":
                        lines.append(
                            f"        FAILED: {step.step_type} {step.step_text}"
                        )
                        if step.error_message:
                            lines.append(f"        Error: {step.error_message}")
            lines.append("")

        lines.extend([
            "=" * 70,
            f"  Report generated at {report.timestamp}",
            "=" * 70,
        ])

        content = "\n".join(lines)
        path = self.output_dir / f"report-{report.run_id}.txt"
        path.write_text(content, encoding="utf-8")
        return path

    @staticmethod
    def create_report_from_results(
        run_id: str,
        features_data: list[dict],
        environment: str = "test",
        app_url: str = "",
    ) -> TestExecutionReport:
        """Create a TestExecutionReport from raw results data.

        Args:
            run_id: Unique run identifier.
            features_data: List of feature result dicts.
            environment: Test environment name.
            app_url: Application URL tested.

        Returns:
            TestExecutionReport object.
        """
        report = TestExecutionReport(
            run_id=run_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            environment=environment,
            app_url=app_url,
        )

        total_duration = 0.0

        for fd in features_data:
            feature = FeatureResult(
                name=fd.get("name", "Unknown Feature"),
                story_key=fd.get("story_key", ""),
                file_path=fd.get("file_path", ""),
                status="passed",
            )

            feature_duration = 0.0
            for sd in fd.get("scenarios", []):
                scenario = ScenarioResult(
                    name=sd.get("name", "Unknown Scenario"),
                    status="passed",
                    tags=sd.get("tags", []),
                )

                scenario_duration = 0.0
                for step_d in sd.get("steps", []):
                    step = StepResult(
                        step_type=step_d.get("type", "Given"),
                        step_text=step_d.get("text", ""),
                        status=step_d.get("status", "passed"),
                        duration_ms=step_d.get("duration_ms", 0.0),
                        error_message=step_d.get("error", ""),
                        screenshot_path=step_d.get("screenshot", ""),
                    )
                    scenario.steps.append(step)
                    scenario_duration += step.duration_ms

                    if step.status == "failed":
                        scenario.status = "failed"

                scenario.duration_ms = scenario_duration
                feature.scenarios.append(scenario)
                feature_duration += scenario_duration

                if scenario.status == "failed":
                    feature.status = "failed"

            feature.duration_ms = feature_duration
            report.features.append(feature)
            total_duration += feature_duration

        report.total_duration_ms = total_duration
        return report
