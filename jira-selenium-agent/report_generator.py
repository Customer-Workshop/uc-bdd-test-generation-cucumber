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
        """Generate HTML report with Chart.js graphical charts and Jira IDs."""
        # Collect per-scenario chart data
        scenario_names_json = json.dumps([
            s.name[:40] + "..." if len(s.name) > 40 else s.name
            for f in report.features for s in f.scenarios
        ])
        scenario_durations_json = json.dumps([
            round(s.duration_ms / 1000, 2)
            for f in report.features for s in f.scenarios
        ])
        scenario_statuses = [s.status for f in report.features for s in f.scenarios]
        scenario_colors_json = json.dumps([
            "#27ae60" if st == "passed" else "#e74c3c" if st == "failed" else "#f39c12"
            for st in scenario_statuses
        ])
        scenario_jira_ids_json = json.dumps([
            f.story_key for f in report.features for _ in f.scenarios
        ])

        # Step type distribution
        step_types: dict[str, int] = {}
        for f in report.features:
            for s in f.scenarios:
                for st in s.steps:
                    step_types[st.step_type] = step_types.get(st.step_type, 0) + 1
        step_type_labels = json.dumps(list(step_types.keys()))
        step_type_counts = json.dumps(list(step_types.values()))

        # Feature-level summary
        feature_names_json = json.dumps([
            f.story_key + ": " + (f.name[:30] + "..." if len(f.name) > 30 else f.name)
            for f in report.features
        ])
        feature_scenario_counts = json.dumps([len(f.scenarios) for f in report.features])
        feature_passed = json.dumps([
            sum(1 for s in f.scenarios if s.status == "passed") for f in report.features
        ])
        feature_failed = json.dumps([
            sum(1 for s in f.scenarios if s.status == "failed") for f in report.features
        ])

        # Build test case table rows with Jira IDs
        tc_table_rows = ""
        tc_idx = 0
        for feature in report.features:
            for scenario in feature.scenarios:
                tc_idx += 1
                status_class = scenario.status
                status_label = scenario.status.upper()
                step_count = len(scenario.steps)
                passed_steps = sum(1 for st in scenario.steps if st.status == "passed")
                failed_steps = sum(1 for st in scenario.steps if st.status == "failed")
                tags_str = ", ".join(scenario.tags) if scenario.tags else "-"
                tc_table_rows += (
                    f'<tr class="row-{status_class}">'
                    f'<td>{tc_idx}</td>'
                    f'<td class="jira-id">{feature.story_key}</td>'
                    f'<td>{scenario.name}</td>'
                    f'<td><span class="badge badge-{status_class}">{status_label}</span></td>'
                    f'<td>{step_count}</td>'
                    f'<td class="text-pass">{passed_steps}</td>'
                    f'<td class="text-fail">{failed_steps}</td>'
                    f'<td>{scenario.duration_ms:.0f}ms</td>'
                    f'<td class="tags-cell">{tags_str}</td>'
                    f'</tr>\n'
                )

        # Build detailed scenario sections
        detail_sections = ""
        for feature in report.features:
            for scenario in feature.scenarios:
                steps_html = ""
                for step in scenario.steps:
                    s_icon = "&#10004;" if step.status == "passed" else "&#10008;" if step.status == "failed" else "&#9888;"
                    steps_html += (
                        f'<div class="step step-{step.status}">'
                        f'<span class="step-status">{s_icon}</span>'
                        f'<strong>{step.step_type}</strong> {step.step_text}'
                        f'<small>({step.duration_ms:.0f}ms)</small>'
                        f'</div>\n'
                    )
                    if step.error_message:
                        steps_html += f'<div class="error-msg">{step.error_message}</div>\n'

                tags_html = "".join(f'<span class="tag">{t}</span>' for t in scenario.tags)
                detail_sections += (
                    f'<div class="scenario-detail">'
                    f'<div class="scenario-detail-header">'
                    f'<span class="badge badge-{scenario.status}">{"&#10004;" if scenario.status == "passed" else "&#10008;"}</span>'
                    f'<span class="jira-badge">{feature.story_key}</span>'
                    f'<strong>{scenario.name}</strong>'
                    f'{tags_html}'
                    f'<small>({scenario.duration_ms:.0f}ms)</small>'
                    f'</div>'
                    f'<div class="steps-container">{steps_html}</div>'
                    f'</div>\n'
                )

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test Execution Report - {report.run_id}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f0f2f5; color: #333; }}
        .container {{ max-width: 1400px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 12px; margin-bottom: 24px; }}
        .header h1 {{ font-size: 28px; margin-bottom: 8px; }}
        .header .subtitle {{ font-size: 16px; opacity: 0.9; margin-bottom: 12px; }}
        .header .meta {{ opacity: 0.85; font-size: 13px; display: flex; flex-wrap: wrap; gap: 16px; }}
        .header .meta span {{ background: rgba(255,255,255,0.15); padding: 3px 10px; border-radius: 4px; }}
        .kpi-row {{ display: grid; grid-template-columns: repeat(6, 1fr); gap: 16px; margin-bottom: 24px; }}
        .kpi-card {{ background: white; padding: 20px 16px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); text-align: center; }}
        .kpi-card .kpi-number {{ font-size: 38px; font-weight: 700; }}
        .kpi-card .kpi-label {{ font-size: 11px; text-transform: uppercase; color: #888; margin-top: 4px; letter-spacing: 0.5px; }}
        .kpi-pass .kpi-number {{ color: #27ae60; }}
        .kpi-fail .kpi-number {{ color: #e74c3c; }}
        .kpi-skip .kpi-number {{ color: #f39c12; }}
        .kpi-rate .kpi-number {{ color: #3498db; }}
        .kpi-steps .kpi-number {{ color: #8e44ad; }}
        .charts-section {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 24px; }}
        .chart-card {{ background: white; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); padding: 20px; }}
        .chart-card h3 {{ font-size: 16px; margin-bottom: 12px; color: #444; }}
        .charts-row-3 {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; margin-bottom: 24px; }}
        .section-title {{ font-size: 20px; font-weight: 700; margin: 28px 0 16px; color: #444; border-bottom: 2px solid #667eea; padding-bottom: 8px; }}
        table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
        th {{ background: #667eea; color: white; padding: 12px 10px; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; text-align: left; }}
        td {{ padding: 10px; border-bottom: 1px solid #f0f0f0; font-size: 13px; }}
        tr:hover {{ background: #f8f9ff; }}
        .jira-id {{ font-weight: 700; color: #1a73e8; white-space: nowrap; }}
        .jira-badge {{ display: inline-block; background: #1a73e8; color: white; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 700; margin-right: 6px; }}
        .text-pass {{ color: #27ae60; font-weight: 600; }}
        .text-fail {{ color: #e74c3c; font-weight: 600; }}
        .badge {{ padding: 4px 12px; border-radius: 20px; font-size: 11px; font-weight: 700; text-transform: uppercase; display: inline-block; }}
        .badge-passed {{ background: #d4edda; color: #155724; }}
        .badge-failed {{ background: #f8d7da; color: #721c24; }}
        .badge-skipped {{ background: #fff3cd; color: #856404; }}
        .tags-cell {{ font-size: 11px; color: #888; }}
        .row-passed {{ border-left: 3px solid #27ae60; }}
        .row-failed {{ border-left: 3px solid #e74c3c; }}
        .row-skipped {{ border-left: 3px solid #f39c12; }}
        .scenario-detail {{ background: white; border-radius: 10px; margin-bottom: 12px; box-shadow: 0 2px 6px rgba(0,0,0,0.06); overflow: hidden; }}
        .scenario-detail-header {{ padding: 14px 18px; border-bottom: 1px solid #eee; display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }}
        .steps-container {{ padding: 8px 18px 12px; }}
        .step {{ padding: 4px 0 4px 24px; font-size: 13px; color: #555; }}
        .step .step-status {{ display: inline-block; width: 18px; text-align: center; }}
        .step-passed .step-status {{ color: #27ae60; }}
        .step-failed .step-status {{ color: #e74c3c; }}
        .step-skipped .step-status {{ color: #f39c12; }}
        .step small {{ color: #aaa; margin-left: 4px; }}
        .error-msg {{ color: #e74c3c; font-size: 12px; padding-left: 42px; font-style: italic; }}
        .tag {{ display: inline-block; background: #e8f0fe; color: #1a73e8; padding: 2px 8px; border-radius: 3px; font-size: 10px; margin-right: 3px; }}
        .footer {{ text-align: center; padding: 24px; color: #aaa; font-size: 12px; }}
        @media (max-width: 900px) {{
            .kpi-row {{ grid-template-columns: repeat(3, 1fr); }}
            .charts-section, .charts-row-3 {{ grid-template-columns: 1fr; }}
        }}
    </style>
</head>
<body>
<div class="container">

    <!-- Header -->
    <div class="header">
        <h1>Test Execution Report</h1>
        <div class="subtitle">BDD Test Automation - Jira-Selenium-Gherkin Agent</div>
        <div class="meta">
            <span>Run ID: {report.run_id}</span>
            <span>Timestamp: {report.timestamp}</span>
            <span>Environment: {report.environment}</span>
            <span>App URL: {report.app_url}</span>
            <span>Duration: {report.total_duration_ms:.0f}ms</span>
        </div>
    </div>

    <!-- KPI Cards -->
    <div class="kpi-row">
        <div class="kpi-card">
            <div class="kpi-number">{report.total_scenarios}</div>
            <div class="kpi-label">Total Scenarios</div>
        </div>
        <div class="kpi-card kpi-pass">
            <div class="kpi-number">{report.passed_scenarios}</div>
            <div class="kpi-label">Passed</div>
        </div>
        <div class="kpi-card kpi-fail">
            <div class="kpi-number">{report.failed_scenarios}</div>
            <div class="kpi-label">Failed</div>
        </div>
        <div class="kpi-card kpi-skip">
            <div class="kpi-number">{report.skipped_scenarios}</div>
            <div class="kpi-label">Skipped</div>
        </div>
        <div class="kpi-card kpi-rate">
            <div class="kpi-number">{report.pass_rate:.1f}%</div>
            <div class="kpi-label">Pass Rate</div>
        </div>
        <div class="kpi-card kpi-steps">
            <div class="kpi-number">{report.total_steps}</div>
            <div class="kpi-label">Total Steps</div>
        </div>
    </div>

    <!-- Charts Row 1: Pie + Bar -->
    <div class="charts-section">
        <div class="chart-card">
            <h3>Test Results Distribution</h3>
            <canvas id="pieChart" height="280"></canvas>
        </div>
        <div class="chart-card">
            <h3>Scenario Execution Duration (seconds)</h3>
            <canvas id="barChart" height="280"></canvas>
        </div>
    </div>

    <!-- Charts Row 2: Doughnut + Horizontal Bar + Step Types -->
    <div class="charts-row-3">
        <div class="chart-card">
            <h3>Pass Rate Gauge</h3>
            <canvas id="gaugeChart" height="240"></canvas>
        </div>
        <div class="chart-card">
            <h3>Feature Coverage</h3>
            <canvas id="featureChart" height="240"></canvas>
        </div>
        <div class="chart-card">
            <h3>Step Type Distribution</h3>
            <canvas id="stepTypeChart" height="240"></canvas>
        </div>
    </div>

    <!-- Test Case Table with Jira IDs -->
    <h2 class="section-title">Test Cases with Jira IDs</h2>
    <table>
        <thead>
            <tr>
                <th>#</th>
                <th>Jira ID</th>
                <th>Test Case / Scenario</th>
                <th>Status</th>
                <th>Steps</th>
                <th>Passed</th>
                <th>Failed</th>
                <th>Duration</th>
                <th>Tags</th>
            </tr>
        </thead>
        <tbody>
            {tc_table_rows}
        </tbody>
    </table>

    <!-- Detailed Scenario Results -->
    <h2 class="section-title">Detailed Execution Results</h2>
    {detail_sections}

    <div class="footer">
        Generated by Jira-Selenium-Gherkin Agent | {report.timestamp}
    </div>
</div>

<script>
// Scenario results pie chart
new Chart(document.getElementById('pieChart'), {{
    type: 'pie',
    data: {{
        labels: ['Passed', 'Failed', 'Skipped'],
        datasets: [{{
            data: [{report.passed_scenarios}, {report.failed_scenarios}, {report.skipped_scenarios}],
            backgroundColor: ['#27ae60', '#e74c3c', '#f39c12'],
            borderWidth: 2,
            borderColor: '#fff'
        }}]
    }},
    options: {{
        responsive: true,
        plugins: {{
            legend: {{ position: 'bottom', labels: {{ padding: 16, font: {{ size: 13 }} }} }},
            tooltip: {{
                callbacks: {{
                    label: function(ctx) {{
                        var total = ctx.dataset.data.reduce((a,b) => a+b, 0);
                        var pct = ((ctx.parsed / total) * 100).toFixed(1);
                        return ctx.label + ': ' + ctx.parsed + ' (' + pct + '%)';
                    }}
                }}
            }}
        }}
    }}
}});

// Scenario duration bar chart with Jira IDs
var scenarioNames = {scenario_names_json};
var scenarioDurations = {scenario_durations_json};
var scenarioColors = {scenario_colors_json};
var scenarioJiraIds = {scenario_jira_ids_json};
new Chart(document.getElementById('barChart'), {{
    type: 'bar',
    data: {{
        labels: scenarioNames.map((n, i) => scenarioJiraIds[i] + ' | ' + n),
        datasets: [{{
            label: 'Duration (s)',
            data: scenarioDurations,
            backgroundColor: scenarioColors,
            borderRadius: 4
        }}]
    }},
    options: {{
        indexAxis: 'y',
        responsive: true,
        plugins: {{
            legend: {{ display: false }},
            tooltip: {{
                callbacks: {{
                    title: function(ctx) {{ return scenarioJiraIds[ctx[0].dataIndex] + ' | ' + scenarioNames[ctx[0].dataIndex]; }},
                    label: function(ctx) {{ return ctx.parsed.x.toFixed(2) + 's'; }}
                }}
            }}
        }},
        scales: {{
            x: {{ title: {{ display: true, text: 'Seconds' }} }},
            y: {{ ticks: {{ font: {{ size: 11 }} }} }}
        }}
    }}
}});

// Pass rate doughnut gauge
new Chart(document.getElementById('gaugeChart'), {{
    type: 'doughnut',
    data: {{
        labels: ['Pass Rate', 'Remaining'],
        datasets: [{{
            data: [{report.pass_rate:.1f}, {100 - report.pass_rate:.1f}],
            backgroundColor: ['#27ae60', '#e8e8e8'],
            borderWidth: 0,
            cutout: '75%'
        }}]
    }},
    options: {{
        responsive: true,
        circumference: 270,
        rotation: -135,
        plugins: {{
            legend: {{ display: false }},
            tooltip: {{ enabled: false }}
        }}
    }},
    plugins: [{{
        id: 'gaugeText',
        afterDraw: function(chart) {{
            var ctx = chart.ctx;
            var cx = chart.chartArea.left + (chart.chartArea.right - chart.chartArea.left) / 2;
            var cy = chart.chartArea.top + (chart.chartArea.bottom - chart.chartArea.top) / 2 + 10;
            ctx.save();
            ctx.font = 'bold 36px sans-serif';
            ctx.fillStyle = '#27ae60';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText('{report.pass_rate:.1f}%', cx, cy);
            ctx.font = '12px sans-serif';
            ctx.fillStyle = '#888';
            ctx.fillText('PASS RATE', cx, cy + 24);
            ctx.restore();
        }}
    }}]
}});

// Feature coverage stacked bar
new Chart(document.getElementById('featureChart'), {{
    type: 'bar',
    data: {{
        labels: {feature_names_json},
        datasets: [
            {{ label: 'Passed', data: {feature_passed}, backgroundColor: '#27ae60', borderRadius: 4 }},
            {{ label: 'Failed', data: {feature_failed}, backgroundColor: '#e74c3c', borderRadius: 4 }}
        ]
    }},
    options: {{
        responsive: true,
        plugins: {{ legend: {{ position: 'bottom' }} }},
        scales: {{
            x: {{ stacked: true }},
            y: {{ stacked: true, title: {{ display: true, text: 'Scenarios' }}, beginAtZero: true, ticks: {{ stepSize: 1 }} }}
        }}
    }}
}});

// Step type distribution polar area chart
new Chart(document.getElementById('stepTypeChart'), {{
    type: 'polarArea',
    data: {{
        labels: {step_type_labels},
        datasets: [{{
            data: {step_type_counts},
            backgroundColor: ['#667eea', '#764ba2', '#27ae60', '#f39c12', '#e74c3c', '#3498db']
        }}]
    }},
    options: {{
        responsive: true,
        plugins: {{ legend: {{ position: 'bottom' }} }},
        scales: {{ r: {{ beginAtZero: true, ticks: {{ stepSize: 10 }} }} }}
    }}
}});
</script>
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
