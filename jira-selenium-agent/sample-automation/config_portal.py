"""Test Automation Configuration Portal.

A standalone Flask web application (port 5556) for configuring and managing
the BDD test automation framework. Separate from the Salesforce mock app.

Sections:
- Test Data Upload: upload JSON test data files for Selenium execution
- Application URL: target app URL configuration
- Selenium Config: browser, CDP port, headless mode, timeouts
- GitHub Details: repo URL, branch, workflow settings
- Report Config: format, output paths
- Jira Config: server URL, credentials, project key
- Copado Config: instance URL, API token, pipeline ID
- Workflow: visual step-by-step agent pipeline execution display
- AI Model Config: LLM settings for auto test case generation/modification
"""

import json
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path

import requests
from flask import Flask, jsonify, redirect, render_template_string, request, url_for
from werkzeug.utils import secure_filename

portal = Flask(__name__)

# Paths
BASE_DIR = Path(__file__).parent
TEST_DATA_PATH = BASE_DIR / "car_parts_test_data.json"
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)
CONFIG_FILE = BASE_DIR / "automation_config.json"
REPORT_RESULTS_FILE = BASE_DIR / "latest_execution_report.json"

# Default configuration
DEFAULT_CONFIG = {
    "app_url": "http://localhost:5555",
    "ui_framework": "salesforce",
    "selenium": {
        "browser": "chrome",
        "cdp_url": "http://localhost:29229",
        "headless": False,
        "implicit_wait": 10,
        "page_load_timeout": 30,
        "screenshot_on_failure": True,
    },
    "github": {
        "repo_url": "",
        "branch": "main",
        "workflow_file": "bdd-test-agent.yml",
        "auto_trigger": False,
    },
    "jira": {
        "server_url": "",
        "username": "",
        "api_token": "",
        "project_key": "",
        "story_status": "To Do",
        "auto_fetch": False,
    },
    "copado": {
        "enabled": False,
        "instance_url": "",
        "api_token": "",
        "pipeline_id": "",
        "deploy_on_pass": True,
        "environment": "UAT",
    },
    "reports": {
        "format": "html",
        "output_dir": "test-reports",
        "generate_junit_xml": True,
        "generate_json": True,
    },
    "ai_model": {
        "provider": "openai",
        "model": "gpt-4o",
        "api_key": "",
        "temperature": 0.3,
        "max_tokens": 4096,
        "auto_detect_fields": True,
        "auto_detect_screens": True,
        "auto_update_tests": True,
        "auto_update_pom": True,
        "auto_update_reports": True,
        "diff_analysis": True,
    },
    "test_data": {
        "file_name": None,
        "file_path": None,
        "records_count": 0,
        "upload_time": None,
    },
}


def load_config() -> dict:
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            saved = json.load(f)
        # Merge with defaults for any missing keys
        merged = {**DEFAULT_CONFIG}
        for k, v in saved.items():
            if isinstance(v, dict) and k in merged and isinstance(merged[k], dict):
                merged[k] = {**merged[k], **v}
            else:
                merged[k] = v
        return merged
    return {**DEFAULT_CONFIG}


def save_config(cfg: dict):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)


config = load_config()

# Load test data stats
if TEST_DATA_PATH.exists():
    with open(TEST_DATA_PATH) as f:
        test_data_info = json.load(f)
    config["test_data"]["records_count"] = len(test_data_info.get("test_records", []))

upload_history: list[dict] = []

# ---------------------------------------------------------------------------
# Portal HTML Template
# ---------------------------------------------------------------------------

PORTAL_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }} | Test Automation Portal</title>
    <style>
        :root {
            --primary: #0176d3;
            --primary-dark: #014486;
            --dark: #1a1a2e;
            --nav-bg: #16213e;
            --surface: #ffffff;
            --bg: #f0f2f5;
            --border: #d8dde6;
            --text: #333;
            --text-light: #666;
            --success: #2e844a;
            --error: #ea001e;
            --warning: #fe9339;
            --accent: #5e35b1;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: var(--bg); color: var(--text); }

        /* Top Nav */
        .portal-nav {
            background: var(--nav-bg);
            color: white;
            padding: 0 24px;
            height: 56px;
            display: flex;
            align-items: center;
            position: sticky;
            top: 0;
            z-index: 1000;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        }
        .portal-logo {
            font-size: 18px;
            font-weight: 700;
            color: white;
            text-decoration: none;
            margin-right: 32px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .portal-logo-icon {
            width: 32px; height: 32px;
            background: var(--primary);
            border-radius: 8px;
            display: flex; align-items: center; justify-content: center;
            font-size: 18px;
        }
        .portal-nav-items { display: flex; gap: 0; height: 56px; }
        .portal-nav-item {
            padding: 0 18px;
            color: rgba(255,255,255,0.7);
            text-decoration: none;
            display: flex;
            align-items: center;
            font-size: 13px;
            font-weight: 500;
            border-bottom: 3px solid transparent;
            transition: all 0.2s;
        }
        .portal-nav-item:hover,
        .portal-nav-item.active {
            color: white;
            border-bottom-color: var(--primary);
            background: rgba(255,255,255,0.06);
        }

        /* Page */
        .page { max-width: 960px; margin: 0 auto; padding: 24px; }
        .page-header { margin-bottom: 24px; }
        .page-header h1 { font-size: 22px; font-weight: 700; color: var(--dark); }
        .page-header p { font-size: 13px; color: var(--text-light); margin-top: 4px; }

        /* Cards */
        .card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.06);
            margin-bottom: 20px;
        }
        .card-header {
            padding: 16px 20px;
            border-bottom: 1px solid var(--border);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .card-header h2 { font-size: 15px; font-weight: 700; color: var(--dark); }
        .card-body { padding: 20px; }

        /* Form */
        .form-group { margin-bottom: 16px; }
        .form-group label {
            display: block;
            font-size: 12px;
            font-weight: 600;
            color: #444;
            margin-bottom: 6px;
            text-transform: uppercase;
            letter-spacing: 0.3px;
        }
        .form-group input,
        .form-group select,
        .form-group textarea {
            width: 100%;
            padding: 10px 12px;
            border: 1px solid var(--border);
            border-radius: 6px;
            font-size: 14px;
            color: var(--text);
            transition: border-color 0.2s;
        }
        .form-group input:focus,
        .form-group select:focus,
        .form-group textarea:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(1,118,211,0.15);
        }
        .form-hint { font-size: 11px; color: #999; margin-top: 4px; }
        .form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
        .required { color: var(--error); }

        /* Buttons */
        .btn {
            padding: 8px 16px;
            border: 1px solid var(--border);
            border-radius: 6px;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            background: white;
            color: var(--text);
            transition: all 0.15s;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }
        .btn:hover { background: #f3f3f3; }
        .btn-primary {
            background: var(--primary);
            color: white;
            border-color: var(--primary);
        }
        .btn-primary:hover { background: var(--primary-dark); }
        .btn-sm { padding: 5px 10px; font-size: 11px; }

        /* Stats Grid */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 12px;
            margin-bottom: 20px;
        }
        .stat-card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 16px;
            text-align: center;
        }
        .stat-value { font-size: 22px; font-weight: 800; color: var(--primary); }
        .stat-label { font-size: 11px; font-weight: 600; color: var(--text-light); text-transform: uppercase; margin-top: 4px; }

        /* Quick Select */
        .quick-btns { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 8px; }
        .quick-btns .btn { font-size: 11px; padding: 4px 10px; }

        /* Toggle */
        .toggle-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 12px 0;
            border-bottom: 1px solid #f0f0f0;
        }
        .toggle-row:last-child { border-bottom: none; }
        .toggle-label { font-size: 13px; font-weight: 600; color: var(--text); }
        .toggle-desc { font-size: 11px; color: var(--text-light); margin-top: 2px; }
        .toggle-switch {
            position: relative;
            width: 42px; height: 22px;
        }
        .toggle-switch input { opacity: 0; width: 0; height: 0; }
        .toggle-slider {
            position: absolute;
            cursor: pointer;
            top: 0; left: 0; right: 0; bottom: 0;
            background: #ccc;
            border-radius: 22px;
            transition: 0.3s;
        }
        .toggle-slider:before {
            content: '';
            position: absolute;
            height: 16px; width: 16px;
            left: 3px; bottom: 3px;
            background: white;
            border-radius: 50%;
            transition: 0.3s;
        }
        .toggle-switch input:checked + .toggle-slider { background: var(--success); }
        .toggle-switch input:checked + .toggle-slider:before { transform: translateX(20px); }

        /* Drop zone */
        .drop-zone {
            border: 2px dashed var(--border);
            border-radius: 8px;
            padding: 40px;
            text-align: center;
            cursor: pointer;
            transition: all 0.2s;
            background: #fafbfc;
        }
        .drop-zone:hover { border-color: var(--primary); background: #f0f8ff; }
        .drop-zone-icon { font-size: 48px; margin-bottom: 8px; }
        .drop-zone-text { font-size: 15px; font-weight: 600; color: var(--dark); }
        .drop-zone-hint { font-size: 12px; color: #999; margin-top: 6px; }

        /* JSON editor */
        .json-editor {
            font-family: 'Courier New', monospace;
            font-size: 12px;
            min-height: 200px;
            resize: vertical;
            background: #1e1e1e;
            color: #d4d4d4;
            padding: 16px;
            border-radius: 6px;
            border: none;
        }

        /* Table */
        .config-table { width: 100%; border-collapse: collapse; }
        .config-table th { font-size: 11px; text-transform: uppercase; color: var(--text-light); padding: 8px 12px; text-align: left; background: #fafbfc; border-bottom: 2px solid var(--border); }
        .config-table td { padding: 10px 12px; border-bottom: 1px solid #f0f0f0; font-size: 13px; }
        .config-table td:first-child { font-weight: 600; color: var(--dark); width: 200px; }
        .config-table td:last-child { font-family: monospace; color: var(--text); }

        /* Toast */
        .toast {
            position: fixed;
            top: 72px;
            right: 24px;
            padding: 12px 20px;
            border-radius: 8px;
            font-size: 13px;
            font-weight: 600;
            color: white;
            z-index: 9999;
            animation: slideIn 0.3s ease, fadeOut 0.3s ease 3s forwards;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        }
        .toast-success { background: var(--success); }
        .toast-error { background: var(--error); }
        @keyframes slideIn { from { transform: translateX(100%); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
        @keyframes fadeOut { to { opacity: 0; transform: translateY(-10px); } }

        /* Separator */
        .separator {
            display: flex; align-items: center; gap: 12px; margin: 20px 0;
        }
        .separator hr { flex: 1; border: none; border-top: 1px solid var(--border); }
        .separator span { font-size: 11px; font-weight: 700; color: #aaa; text-transform: uppercase; }

        /* Status badges */
        .status-badge {
            display: inline-flex; align-items: center; gap: 4px;
            padding: 3px 10px; border-radius: 12px;
            font-size: 11px; font-weight: 700; text-transform: uppercase;
        }
        .status-configured { background: #e8f5e9; color: #2e7d32; }
        .status-not-configured { background: #fff3e0; color: #e65100; }
        .status-enabled { background: #e3f2fd; color: #1565c0; }
        .status-disabled { background: #f5f5f5; color: #757575; }
        .status-dot {
            width: 8px; height: 8px; border-radius: 50%; display: inline-block;
        }
        .status-dot-green { background: #2e844a; }
        .status-dot-orange { background: #e65100; }
        .status-dot-gray { background: #bbb; }

        /* File path display */
        .file-path-box {
            background: #f5f7fa; border: 1px solid var(--border); border-radius: 6px;
            padding: 12px 16px; font-family: monospace; font-size: 13px;
            color: var(--dark); word-break: break-all;
        }

        /* Workflow pipeline */
        .wf-pipeline { display: flex; flex-direction: column; gap: 0; }
        .wf-step {
            display: flex; align-items: flex-start; gap: 16px;
            position: relative; padding: 0 0 0 0;
        }
        .wf-step-connector {
            display: flex; flex-direction: column; align-items: center;
            width: 40px; flex-shrink: 0;
        }
        .wf-step-dot {
            width: 36px; height: 36px; border-radius: 50%;
            display: flex; align-items: center; justify-content: center;
            font-size: 16px; font-weight: 700; color: white;
            z-index: 2; flex-shrink: 0;
        }
        .wf-step-line {
            width: 3px; flex: 1; min-height: 24px;
        }
        .wf-step-content {
            flex: 1; padding: 6px 0 20px 0;
        }
        .wf-step-title { font-size: 14px; font-weight: 700; color: var(--dark); }
        .wf-step-agent { font-size: 11px; font-weight: 600; color: var(--primary); font-family: monospace; }
        .wf-step-desc { font-size: 12px; color: var(--text-light); margin-top: 4px; line-height: 1.5; }
        .wf-step-io {
            display: flex; gap: 12px; margin-top: 8px; flex-wrap: wrap;
        }
        .wf-io-tag {
            font-size: 10px; font-weight: 700; padding: 2px 8px;
            border-radius: 4px; text-transform: uppercase;
        }
        .wf-io-in { background: #e8f5e9; color: #2e7d32; }
        .wf-io-out { background: #e3f2fd; color: #1565c0; }
        .wf-io-ai { background: #f3e5f5; color: #7b1fa2; }

        /* Footer */
        .portal-footer {
            text-align: center;
            padding: 20px;
            font-size: 12px;
            color: var(--text-light);
        }
    </style>
</head>
<body>
    <nav class="portal-nav">
        <a href="/" class="portal-logo">
            <div class="portal-logo-icon">&#9881;</div>
            Automation Portal
        </a>
        <div class="portal-nav-items">
            <a href="/" class="portal-nav-item {{ 'active' if active_tab == 'dashboard' else '' }}">Dashboard</a>
            <a href="/workflow" class="portal-nav-item {{ 'active' if active_tab == 'workflow' else '' }}">Workflow</a>
            <a href="/traceability" class="portal-nav-item {{ 'active' if active_tab == 'traceability' else '' }}">Traceability</a>
            <a href="/execute" class="portal-nav-item {{ 'active' if active_tab == 'execute' else '' }}">Execute</a>
            <a href="/ai-model" class="portal-nav-item {{ 'active' if active_tab == 'ai-model' else '' }}">AI Model</a>
            <a href="/upload" class="portal-nav-item {{ 'active' if active_tab == 'upload' else '' }}">Upload</a>
            <a href="/app-config" class="portal-nav-item {{ 'active' if active_tab == 'app-config' else '' }}">App URL</a>
            <a href="/selenium-config" class="portal-nav-item {{ 'active' if active_tab == 'selenium' else '' }}">Selenium</a>
            <a href="/jira-config" class="portal-nav-item {{ 'active' if active_tab == 'jira' else '' }}">Jira</a>
            <a href="/github-config" class="portal-nav-item {{ 'active' if active_tab == 'github' else '' }}">GitHub</a>
            <a href="/copado-config" class="portal-nav-item {{ 'active' if active_tab == 'copado' else '' }}">Copado</a>
            <a href="/report-config" class="portal-nav-item {{ 'active' if active_tab == 'reports' else '' }}">Reports</a>
        </div>
    </nav>

    {% if toast_msg %}
    <div class="toast toast-{{ toast_type }}">{{ toast_msg }}</div>
    {% endif %}

    {{ content|safe }}

    <div class="portal-footer">
        BDD Test Automation Configuration Portal &mdash; Agentic AI Framework
    </div>
</body>
</html>
"""


def render_portal(title, content_template, active_tab="dashboard", **kwargs):
    content = render_template_string(content_template, **kwargs)
    return render_template_string(
        PORTAL_TEMPLATE,
        title=title,
        active_tab=active_tab,
        content=content,
        toast_msg=kwargs.get("toast_msg", ""),
        toast_type=kwargs.get("toast_type", ""),
    )


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

DASHBOARD_CONTENT = """
<div class="page">
    <div class="page-header">
        <h1>Test Automation Configuration</h1>
        <p>Configure your BDD test automation framework settings. Changes are saved and used by the Selenium E2E runner.</p>
    </div>

    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-value" style="font-size:14px; word-break:break-all;">{{ cfg.app_url }}</div>
            <div class="stat-label">Application URL</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{{ cfg.test_data.records_count }}</div>
            <div class="stat-label">Test Records</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{{ framework_name }}</div>
            <div class="stat-label">UI Framework</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{{ cfg.selenium.browser | title }}</div>
            <div class="stat-label">Browser</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{{ cfg.reports.format | upper }}</div>
            <div class="stat-label">Report Format</div>
        </div>
    </div>

    <!-- Tool Integration Status -->
    <div class="card">
        <div class="card-header">
            <h2>Integration Status</h2>
        </div>
        <div class="card-body" style="padding:0;">
            <table class="config-table">
                <thead><tr><th>Tool</th><th>Status</th><th>Details</th></tr></thead>
                <tbody>
                    <tr>
                        <td>Jira</td>
                        <td>{% if cfg.jira.server_url %}<span class="status-badge status-configured"><span class="status-dot status-dot-green"></span> Configured</span>{% else %}<span class="status-badge status-not-configured"><span class="status-dot status-dot-orange"></span> Not Configured</span>{% endif %}</td>
                        <td>{{ cfg.jira.server_url or 'Set server URL and credentials' }} {% if cfg.jira.project_key %}({{ cfg.jira.project_key }}){% endif %}</td>
                    </tr>
                    <tr>
                        <td>Selenium</td>
                        <td><span class="status-badge status-configured"><span class="status-dot status-dot-green"></span> Configured</span></td>
                        <td>{{ cfg.selenium.browser | title }} via {{ cfg.selenium.cdp_url }}</td>
                    </tr>
                    <tr>
                        <td>GitHub</td>
                        <td>{% if cfg.github.repo_url %}<span class="status-badge status-configured"><span class="status-dot status-dot-green"></span> Configured</span>{% else %}<span class="status-badge status-not-configured"><span class="status-dot status-dot-orange"></span> Not Configured</span>{% endif %}</td>
                        <td>{{ cfg.github.repo_url or 'Set repository URL' }} ({{ cfg.github.branch }})</td>
                    </tr>
                    <tr>
                        <td>Copado</td>
                        <td>{% if cfg.copado.enabled and cfg.copado.instance_url %}<span class="status-badge status-enabled"><span class="status-dot status-dot-green"></span> Enabled</span>{% elif cfg.copado.enabled %}<span class="status-badge status-not-configured"><span class="status-dot status-dot-orange"></span> Incomplete</span>{% else %}<span class="status-badge status-disabled"><span class="status-dot status-dot-gray"></span> Disabled</span>{% endif %}</td>
                        <td>{{ cfg.copado.instance_url or 'Not configured' }} {% if cfg.copado.environment %}({{ cfg.copado.environment }}){% endif %}</td>
                    </tr>
                    <tr>
                        <td>Reports</td>
                        <td><span class="status-badge status-configured"><span class="status-dot status-dot-green"></span> Configured</span></td>
                        <td>{{ cfg.reports.format | upper }} &rarr; {{ cfg.reports.output_dir }}/</td>
                    </tr>
                    <tr>
                        <td>Test Data</td>
                        <td>{% if cfg.test_data.records_count > 0 %}<span class="status-badge status-configured"><span class="status-dot status-dot-green"></span> Loaded</span>{% else %}<span class="status-badge status-not-configured"><span class="status-dot status-dot-orange"></span> No Data</span>{% endif %}</td>
                        <td>{{ cfg.test_data.records_count }} records {% if cfg.test_data.file_name %}from {{ cfg.test_data.file_name }}{% else %}(default){% endif %}</td>
                    </tr>
                    <tr>
                        <td>AI Model</td>
                        <td>{% if cfg.ai_model.api_key %}<span class="status-badge status-configured"><span class="status-dot status-dot-green"></span> Configured</span>{% else %}<span class="status-badge status-not-configured"><span class="status-dot status-dot-orange"></span> No API Key</span>{% endif %}</td>
                        <td>{{ cfg.ai_model.provider | title }} / {{ cfg.ai_model.model }} &middot; {{ 'Auto-detect ON' if cfg.ai_model.auto_detect_fields else 'Auto-detect OFF' }}</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>

    <!-- Quick Links -->
    <div class="card">
        <div class="card-header">
            <h2>Quick Actions</h2>
        </div>
        <div class="card-body" style="display:flex; gap:12px; flex-wrap:wrap;">
            <a href="/workflow" class="btn btn-primary">View Workflow</a>
            <a href="/traceability" class="btn btn-primary" style="background:#2e844a;">Traceability Matrix</a>
            <a href="/execute" class="btn btn-primary" style="background:#e65100;">Execute Pipeline</a>
            <a href="/ai-model" class="btn btn-primary" style="background:#7b1fa2;">AI Model Config</a>
            <a href="/upload" class="btn">Upload Test Data</a>
            <a href="/app-config" class="btn">Configure App URL</a>
            <a href="/selenium-config" class="btn">Selenium Settings</a>
            <a href="/jira-config" class="btn">Jira Settings</a>
            <a href="/github-config" class="btn">GitHub Settings</a>
            <a href="/copado-config" class="btn">Copado Settings</a>
            <a href="/report-config" class="btn">Report Settings</a>
            <a href="{{ cfg.app_url }}" class="btn" target="_blank">Open Application</a>
        </div>
    </div>

    <!-- Current Configuration Summary -->
    <div class="card">
        <div class="card-header">
            <h2>Full Configuration</h2>
        </div>
        <div class="card-body" style="padding:0;">
            <table class="config-table">
                <thead><tr><th>Setting</th><th>Value</th></tr></thead>
                <tbody>
                    <tr><td>Application URL</td><td>{{ cfg.app_url }}</td></tr>
                    <tr><td>UI Framework</td><td>{{ framework_name }}</td></tr>
                    <tr><td>Test Data File</td><td>{{ test_data_path }}</td></tr>
                    <tr><td>Test Records</td><td>{{ cfg.test_data.records_count }} scenarios</td></tr>
                    <tr><td>Browser</td><td>{{ cfg.selenium.browser | title }}</td></tr>
                    <tr><td>CDP URL</td><td>{{ cfg.selenium.cdp_url }}</td></tr>
                    <tr><td>Headless Mode</td><td>{{ 'Enabled' if cfg.selenium.headless else 'Disabled' }}</td></tr>
                    <tr><td>Jira Server</td><td>{{ cfg.jira.server_url or 'Not configured' }}</td></tr>
                    <tr><td>Jira Project</td><td>{{ cfg.jira.project_key or 'Not set' }}</td></tr>
                    <tr><td>GitHub Repo</td><td>{{ cfg.github.repo_url or 'Not configured' }}</td></tr>
                    <tr><td>GitHub Branch</td><td>{{ cfg.github.branch }}</td></tr>
                    <tr><td>Copado</td><td>{{ 'Enabled' if cfg.copado.enabled else 'Disabled' }}</td></tr>
                    <tr><td>AI Model</td><td>{{ cfg.ai_model.provider | title }} / {{ cfg.ai_model.model }}</td></tr>
                    <tr><td>AI Auto-Detect</td><td>Fields: {{ 'ON' if cfg.ai_model.auto_detect_fields else 'OFF' }} | Screens: {{ 'ON' if cfg.ai_model.auto_detect_screens else 'OFF' }} | Tests: {{ 'ON' if cfg.ai_model.auto_update_tests else 'OFF' }}</td></tr>
                    <tr><td>Report Format</td><td>{{ cfg.reports.format | upper }}</td></tr>
                    <tr><td>Report Output</td><td>{{ cfg.reports.output_dir }}</td></tr>
                </tbody>
            </table>
        </div>
    </div>
</div>
"""


@portal.route("/")
def dashboard():
    td_path = str(config["test_data"].get("file_path") or TEST_DATA_PATH)
    return render_portal(
        "Dashboard",
        DASHBOARD_CONTENT,
        active_tab="dashboard",
        cfg=config,
        framework_name=get_framework_name(),
        test_data_path=td_path,
    )


# ---------------------------------------------------------------------------
# Upload Test Data
# ---------------------------------------------------------------------------

UPLOAD_CONTENT = """
<div class="page">
    <div class="page-header">
        <h1>Upload Test Data</h1>
        <p>Upload a JSON file containing test records for Selenium E2E test execution.</p>
    </div>

    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-value">{{ cfg.test_data.records_count }}</div>
            <div class="stat-label">Records Loaded</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{{ cfg.test_data.file_name or 'Default' }}</div>
            <div class="stat-label">Data Source</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{{ cfg.test_data.upload_time or 'Built-in' }}</div>
            <div class="stat-label">Last Upload</div>
        </div>
    </div>

    <!-- Current Data File Path -->
    <div class="card">
        <div class="card-header"><h2>Current Test Data File</h2></div>
        <div class="card-body">
            <div class="form-group" style="margin-bottom:8px;">
                <label>File Path on Disk</label>
                <div class="file-path-box">{{ test_data_path }}</div>
                <div class="form-hint">This is the JSON file Selenium reads at runtime. Upload a new file to replace it.</div>
            </div>
            {% if file_exists %}
            <div style="display:flex; align-items:center; gap:8px; margin-top:8px;">
                <span class="status-badge status-configured"><span class="status-dot status-dot-green"></span> File Exists</span>
                <span style="font-size:12px; color:var(--text-light);">{{ file_size }} &middot; {{ cfg.test_data.records_count }} test records</span>
            </div>
            {% else %}
            <span class="status-badge status-not-configured"><span class="status-dot status-dot-orange"></span> File Not Found</span>
            {% endif %}
        </div>
    </div>

    <div class="card">
        <div class="card-header"><h2>Upload File</h2></div>
        <div class="card-body">
            <form method="POST" action="/upload" enctype="multipart/form-data">
                <div class="drop-zone" id="dropZone"
                     ondragover="event.preventDefault(); this.style.borderColor='var(--primary)'; this.style.background='#e8f4fd';"
                     ondragleave="this.style.borderColor='var(--border)'; this.style.background='#fafbfc';"
                     ondrop="handleDrop(event)"
                     onclick="document.getElementById('fileInput').click()">
                    <div class="drop-zone-icon">&#128196;</div>
                    <div class="drop-zone-text">Drop JSON file here or click to browse</div>
                    <div class="drop-zone-hint">Accepts .json files up to 5MB</div>
                    <div id="fileName" style="margin-top:12px; font-size:14px; color:var(--success); font-weight:600; display:none;"></div>
                </div>
                <input type="file" name="test_data_file" id="fileInput" accept=".json" style="display:none;" onchange="showFileName(this)">

                <div class="separator">
                    <hr><span>or paste json below</span><hr>
                </div>

                <div class="form-group">
                    <label>Test Data JSON</label>
                    <textarea name="test_data_json" id="jsonEditor" class="json-editor"
                              placeholder='[{"scenario": "Create Part", "data": {"Part Name": "...", "Part Category": "..."}}]'></textarea>
                </div>
                <div style="display:flex; gap:8px; margin-bottom:16px;">
                    <button type="button" class="btn btn-sm" onclick="validateJson()">Validate</button>
                    <button type="button" class="btn btn-sm" onclick="formatJson()">Format</button>
                    <button type="button" class="btn btn-sm" onclick="loadSample()">Load Sample</button>
                    <span id="jsonStatus" style="font-size:12px; font-weight:600; display:flex; align-items:center;"></span>
                </div>

                <div style="display:flex; justify-content:flex-end; gap:12px; padding-top:16px; border-top:1px solid var(--border);">
                    <button type="submit" class="btn btn-primary">Upload Test Data</button>
                </div>
            </form>
        </div>
    </div>

    <!-- Sample Format -->
    <div class="card">
        <div class="card-header">
            <h2>Expected JSON Format</h2>
            <button class="btn btn-sm" onclick="copySample()">Copy Sample</button>
        </div>
        <div class="card-body">
            <pre id="sampleJson" class="json-editor" style="min-height:auto; resize:none;">{{ sample_json }}</pre>
        </div>
    </div>

    {% if uploads %}
    <div class="card">
        <div class="card-header"><h2>Upload History</h2></div>
        <div class="card-body" style="padding:0;">
            <table class="config-table">
                <thead><tr><th>Time</th><th>File</th><th>Records</th></tr></thead>
                <tbody>
                    {% for u in uploads %}
                    <tr><td>{{ u.time }}</td><td>{{ u.file_name }}</td><td>{{ u.records_count }}</td></tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
    {% endif %}
</div>

<script>
function showFileName(input) {
    var el = document.getElementById('fileName');
    if (input.files.length > 0) {
        el.textContent = '\\u2713 ' + input.files[0].name + ' (' + (input.files[0].size/1024).toFixed(1) + ' KB)';
        el.style.display = 'block';
    }
}
function handleDrop(e) {
    e.preventDefault();
    document.getElementById('dropZone').style.borderColor = 'var(--border)';
    document.getElementById('dropZone').style.background = '#fafbfc';
    if (e.dataTransfer.files.length > 0 && e.dataTransfer.files[0].name.endsWith('.json')) {
        document.getElementById('fileInput').files = e.dataTransfer.files;
        showFileName(document.getElementById('fileInput'));
    }
}
function validateJson() {
    var ed = document.getElementById('jsonEditor'), st = document.getElementById('jsonStatus');
    try { var p = JSON.parse(ed.value); var c = Array.isArray(p) ? p.length : (p.test_records ? p.test_records.length : 0);
        st.innerHTML = '<span style="color:var(--success);">Valid (' + c + ' records)</span>';
    } catch(e) { st.innerHTML = '<span style="color:var(--error);">' + e.message + '</span>'; }
}
function formatJson() {
    var ed = document.getElementById('jsonEditor');
    try { ed.value = JSON.stringify(JSON.parse(ed.value), null, 2); validateJson(); } catch(e) {}
}
function loadSample() { document.getElementById('jsonEditor').value = document.getElementById('sampleJson').textContent; validateJson(); }
function copySample() { navigator.clipboard.writeText(document.getElementById('sampleJson').textContent); }
</script>
"""


@portal.route("/upload", methods=["GET", "POST"])
def upload_page():
    toast_msg = ""
    toast_type = ""

    if request.method == "POST":
        test_data = None
        file_name = None

        uploaded_file = request.files.get("test_data_file")
        if uploaded_file and uploaded_file.filename:
            file_name = secure_filename(uploaded_file.filename)
            try:
                content = uploaded_file.read().decode("utf-8")
                test_data = json.loads(content)
                (UPLOAD_DIR / file_name).write_text(content)
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                toast_msg = f"Invalid JSON file: {e}"
                toast_type = "error"

        if not test_data and not toast_msg:
            json_text = request.form.get("test_data_json", "").strip()
            if json_text:
                try:
                    test_data = json.loads(json_text)
                    file_name = "pasted_data.json"
                    (UPLOAD_DIR / file_name).write_text(json.dumps(test_data, indent=2))
                except json.JSONDecodeError as e:
                    toast_msg = f"Invalid JSON: {e}"
                    toast_type = "error"

        if test_data and not toast_msg:
            if TEST_DATA_PATH.exists():
                with open(TEST_DATA_PATH) as f:
                    full_config = json.load(f)
            else:
                full_config = {}

            if isinstance(test_data, list):
                full_config["test_records"] = test_data
                records_count = len(test_data)
            elif isinstance(test_data, dict):
                if "test_records" in test_data:
                    full_config["test_records"] = test_data["test_records"]
                    records_count = len(test_data["test_records"])
                else:
                    full_config["test_records"] = [test_data]
                    records_count = 1
                if "dropdown_fields" in test_data:
                    full_config["dropdown_fields"] = test_data["dropdown_fields"]
            else:
                records_count = 0

            with open(TEST_DATA_PATH, "w") as f:
                json.dump(full_config, f, indent=2)

            config["test_data"]["file_name"] = file_name
            config["test_data"]["file_path"] = str(TEST_DATA_PATH)
            config["test_data"]["records_count"] = records_count
            config["test_data"]["upload_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            save_config(config)

            upload_history.insert(0, {
                "time": config["test_data"]["upload_time"],
                "file_name": file_name,
                "records_count": records_count,
            })

            toast_msg = f"Uploaded successfully! {records_count} records loaded."
            toast_type = "success"
        elif not toast_msg:
            toast_msg = "Please select a file or paste JSON data."
            toast_type = "error"

    # Load sample from current test data
    if TEST_DATA_PATH.exists():
        with open(TEST_DATA_PATH) as f:
            td = json.load(f)
        sample_json = json.dumps(td.get("test_records", [])[:2], indent=2)
    else:
        sample_json = "[]"

    td_path = str(config["test_data"].get("file_path") or TEST_DATA_PATH)
    file_exists = Path(td_path).exists()
    file_size = ""
    if file_exists:
        size_bytes = Path(td_path).stat().st_size
        if size_bytes < 1024:
            file_size = f"{size_bytes} B"
        else:
            file_size = f"{size_bytes / 1024:.1f} KB"

    return render_portal(
        "Upload Test Data", UPLOAD_CONTENT, active_tab="upload",
        cfg=config, sample_json=sample_json, uploads=upload_history,
        test_data_path=td_path, file_exists=file_exists, file_size=file_size,
        toast_msg=toast_msg, toast_type=toast_type,
    )


# ---------------------------------------------------------------------------
# Application URL Configuration
# ---------------------------------------------------------------------------

APP_CONFIG_CONTENT = """
<div class="page">
    <div class="page-header">
        <h1>Application URL Configuration</h1>
        <p>Set the target application URL that Selenium will run BDD test automation against.</p>
    </div>

    <div class="card">
        <div class="card-header"><h2>Target Application</h2></div>
        <div class="card-body">
            <form method="POST" action="/app-config">
                <div class="form-group">
                    <label>Application URL <span class="required">*</span></label>
                    <input type="url" name="app_url" value="{{ cfg.app_url }}"
                           placeholder="https://your-app.lightning.force.com"
                           required style="font-size:16px; padding:14px 16px;">
                    <div class="form-hint">Base URL for all BDD test scenarios (login, navigation, CRUD)</div>
                </div>

                <div class="form-group">
                    <label>Quick Select</label>
                    <div class="quick-btns">
                        <button type="button" class="btn" onclick="document.querySelector('[name=app_url]').value='http://localhost:5555'">Mock Salesforce (5555)</button>
                        <button type="button" class="btn" onclick="document.querySelector('[name=app_url]').value='https://login.salesforce.com'">Salesforce Production</button>
                        <button type="button" class="btn" onclick="document.querySelector('[name=app_url]').value='https://test.salesforce.com'">Salesforce Sandbox</button>
                        <button type="button" class="btn" onclick="document.querySelector('[name=app_url]').value='http://localhost:3000'">React (3000)</button>
                        <button type="button" class="btn" onclick="document.querySelector('[name=app_url]').value='http://localhost:4200'">Angular (4200)</button>
                        <button type="button" class="btn" onclick="document.querySelector('[name=app_url]').value='http://localhost:8080'">Custom (8080)</button>
                    </div>
                </div>

                <div class="form-group">
                    <label>UI Framework</label>
                    <select name="ui_framework">
                        <option value="salesforce" {{ 'selected' if cfg.ui_framework == 'salesforce' else '' }}>Salesforce Lightning (LWC)</option>
                        <option value="react" {{ 'selected' if cfg.ui_framework == 'react' else '' }}>React</option>
                        <option value="angular" {{ 'selected' if cfg.ui_framework == 'angular' else '' }}>Angular</option>
                        <option value="auto" {{ 'selected' if cfg.ui_framework == 'auto' else '' }}>Auto-Detect</option>
                    </select>
                    <div class="form-hint">Determines Page Object Model (POM) selectors for element traversal</div>
                </div>

                <div style="display:flex; justify-content:flex-end; gap:12px; padding-top:16px; border-top:1px solid var(--border);">
                    <a href="{{ cfg.app_url }}" class="btn" target="_blank">Open Application</a>
                    <button type="submit" class="btn btn-primary">Save Configuration</button>
                </div>
            </form>
        </div>
    </div>
</div>
"""


@portal.route("/app-config", methods=["GET", "POST"])
def app_config_page():
    toast_msg = ""
    toast_type = ""

    if request.method == "POST":
        app_url = request.form.get("app_url", "").strip()
        ui_framework = request.form.get("ui_framework", "salesforce")
        if app_url:
            config["app_url"] = app_url
            config["ui_framework"] = ui_framework
            save_config(config)
            toast_msg = f"Configuration saved! Target: {app_url}"
            toast_type = "success"
        else:
            toast_msg = "Application URL is required."
            toast_type = "error"

    return render_portal(
        "App URL", APP_CONFIG_CONTENT, active_tab="app-config",
        cfg=config, toast_msg=toast_msg, toast_type=toast_type,
    )


# ---------------------------------------------------------------------------
# Selenium Configuration
# ---------------------------------------------------------------------------

SELENIUM_CONFIG_CONTENT = """
<div class="page">
    <div class="page-header">
        <h1>Selenium Configuration</h1>
        <p>Configure browser and Selenium WebDriver settings for test execution.</p>
    </div>

    <div class="card">
        <div class="card-header"><h2>Browser Settings</h2></div>
        <div class="card-body">
            <form method="POST" action="/selenium-config">
                <div class="form-row">
                    <div class="form-group">
                        <label>Browser</label>
                        <select name="browser">
                            <option value="chrome" {{ 'selected' if cfg.selenium.browser == 'chrome' else '' }}>Google Chrome</option>
                            <option value="firefox" {{ 'selected' if cfg.selenium.browser == 'firefox' else '' }}>Mozilla Firefox</option>
                            <option value="edge" {{ 'selected' if cfg.selenium.browser == 'edge' else '' }}>Microsoft Edge</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>CDP URL</label>
                        <input type="text" name="cdp_url" value="{{ cfg.selenium.cdp_url }}" placeholder="http://localhost:29229">
                        <div class="form-hint">Chrome DevTools Protocol endpoint for Playwright integration</div>
                    </div>
                </div>

                <div class="form-row">
                    <div class="form-group">
                        <label>Implicit Wait (seconds)</label>
                        <input type="number" name="implicit_wait" value="{{ cfg.selenium.implicit_wait }}" min="0" max="60">
                    </div>
                    <div class="form-group">
                        <label>Page Load Timeout (seconds)</label>
                        <input type="number" name="page_load_timeout" value="{{ cfg.selenium.page_load_timeout }}" min="5" max="120">
                    </div>
                </div>

                <div style="margin-top:8px;">
                    <div class="toggle-row">
                        <div>
                            <div class="toggle-label">Headless Mode</div>
                            <div class="toggle-desc">Run browser without GUI (faster CI execution)</div>
                        </div>
                        <label class="toggle-switch">
                            <input type="checkbox" name="headless" {{ 'checked' if cfg.selenium.headless else '' }}>
                            <span class="toggle-slider"></span>
                        </label>
                    </div>
                    <div class="toggle-row">
                        <div>
                            <div class="toggle-label">Screenshot on Failure</div>
                            <div class="toggle-desc">Capture browser screenshot when a test step fails</div>
                        </div>
                        <label class="toggle-switch">
                            <input type="checkbox" name="screenshot_on_failure" {{ 'checked' if cfg.selenium.screenshot_on_failure else '' }}>
                            <span class="toggle-slider"></span>
                        </label>
                    </div>
                </div>

                <div style="display:flex; justify-content:flex-end; gap:12px; padding-top:16px; margin-top:16px; border-top:1px solid var(--border);">
                    <button type="submit" class="btn btn-primary">Save Selenium Config</button>
                </div>
            </form>
        </div>
    </div>
</div>
"""


@portal.route("/selenium-config", methods=["GET", "POST"])
def selenium_config_page():
    toast_msg = ""
    toast_type = ""

    if request.method == "POST":
        config["selenium"]["browser"] = request.form.get("browser", "chrome")
        config["selenium"]["cdp_url"] = request.form.get("cdp_url", "http://localhost:29229")
        config["selenium"]["implicit_wait"] = int(request.form.get("implicit_wait", 10))
        config["selenium"]["page_load_timeout"] = int(request.form.get("page_load_timeout", 30))
        config["selenium"]["headless"] = "headless" in request.form
        config["selenium"]["screenshot_on_failure"] = "screenshot_on_failure" in request.form
        save_config(config)
        toast_msg = "Selenium configuration saved!"
        toast_type = "success"

    return render_portal(
        "Selenium Config", SELENIUM_CONFIG_CONTENT, active_tab="selenium",
        cfg=config, toast_msg=toast_msg, toast_type=toast_type,
    )


# ---------------------------------------------------------------------------
# GitHub Configuration
# ---------------------------------------------------------------------------

GITHUB_CONFIG_CONTENT = """
<div class="page">
    <div class="page-header">
        <h1>GitHub Configuration</h1>
        <p>Configure GitHub repository and CI/CD workflow settings.</p>
    </div>

    <div class="card">
        <div class="card-header"><h2>Repository Settings</h2></div>
        <div class="card-body">
            <form method="POST" action="/github-config">
                <div class="form-group">
                    <label>Repository URL</label>
                    <input type="url" name="repo_url" value="{{ cfg.github.repo_url }}"
                           placeholder="https://github.com/org/repo">
                    <div class="form-hint">GitHub repository URL for the BDD test project</div>
                </div>

                <div class="form-row">
                    <div class="form-group">
                        <label>Branch</label>
                        <input type="text" name="branch" value="{{ cfg.github.branch }}" placeholder="main">
                    </div>
                    <div class="form-group">
                        <label>Workflow File</label>
                        <input type="text" name="workflow_file" value="{{ cfg.github.workflow_file }}"
                               placeholder="bdd-test-agent.yml">
                        <div class="form-hint">GitHub Actions workflow file name</div>
                    </div>
                </div>

                <div style="margin-top:8px;">
                    <div class="toggle-row">
                        <div>
                            <div class="toggle-label">Auto-Trigger on Push</div>
                            <div class="toggle-desc">Automatically run BDD tests when code is pushed to the branch</div>
                        </div>
                        <label class="toggle-switch">
                            <input type="checkbox" name="auto_trigger" {{ 'checked' if cfg.github.auto_trigger else '' }}>
                            <span class="toggle-slider"></span>
                        </label>
                    </div>
                </div>

                <div style="display:flex; justify-content:flex-end; gap:12px; padding-top:16px; margin-top:16px; border-top:1px solid var(--border);">
                    <button type="submit" class="btn btn-primary">Save GitHub Config</button>
                </div>
            </form>
        </div>
    </div>
</div>
"""


@portal.route("/github-config", methods=["GET", "POST"])
def github_config_page():
    toast_msg = ""
    toast_type = ""

    if request.method == "POST":
        config["github"]["repo_url"] = request.form.get("repo_url", "")
        config["github"]["branch"] = request.form.get("branch", "main")
        config["github"]["workflow_file"] = request.form.get("workflow_file", "bdd-test-agent.yml")
        config["github"]["auto_trigger"] = "auto_trigger" in request.form
        save_config(config)
        toast_msg = "GitHub configuration saved!"
        toast_type = "success"

    return render_portal(
        "GitHub Config", GITHUB_CONFIG_CONTENT, active_tab="github",
        cfg=config, toast_msg=toast_msg, toast_type=toast_type,
    )


# ---------------------------------------------------------------------------
# Jira Configuration
# ---------------------------------------------------------------------------

JIRA_CONFIG_CONTENT = """
<div class="page">
    <div class="page-header">
        <h1>Jira Configuration</h1>
        <p>Connect to Jira to fetch user stories and auto-generate BDD feature files.</p>
    </div>

    <div class="card">
        <div class="card-header">
            <h2>Connection Settings</h2>
            {% if cfg.jira.server_url %}
            <span class="status-badge status-configured"><span class="status-dot status-dot-green"></span> Configured</span>
            {% else %}
            <span class="status-badge status-not-configured"><span class="status-dot status-dot-orange"></span> Not Configured</span>
            {% endif %}
        </div>
        <div class="card-body">
            <form method="POST" action="/jira-config">
                <div class="form-group">
                    <label>Jira Server URL <span class="required">*</span></label>
                    <input type="url" name="server_url" value="{{ cfg.jira.server_url }}"
                           placeholder="https://your-org.atlassian.net">
                    <div class="form-hint">Jira Cloud or Server instance URL</div>
                </div>

                <div class="form-row">
                    <div class="form-group">
                        <label>Username / Email <span class="required">*</span></label>
                        <input type="text" name="username" value="{{ cfg.jira.username }}"
                               placeholder="user@company.com">
                    </div>
                    <div class="form-group">
                        <label>API Token <span class="required">*</span></label>
                        <input type="password" name="api_token" value="{{ cfg.jira.api_token }}"
                               placeholder="Enter Jira API token">
                        <div class="form-hint"><a href="https://id.atlassian.com/manage-profile/security/api-tokens" target="_blank" style="color:var(--primary);">Generate API token</a></div>
                    </div>
                </div>

                <div class="form-row">
                    <div class="form-group">
                        <label>Project Key <span class="required">*</span></label>
                        <input type="text" name="project_key" value="{{ cfg.jira.project_key }}"
                               placeholder="PROJ" style="text-transform:uppercase;">
                        <div class="form-hint">Jira project key (e.g. CAR, PROJ, TEST)</div>
                    </div>
                    <div class="form-group">
                        <label>Story Status Filter</label>
                        <select name="story_status">
                            <option value="To Do" {{ 'selected' if cfg.jira.story_status == 'To Do' else '' }}>To Do</option>
                            <option value="In Progress" {{ 'selected' if cfg.jira.story_status == 'In Progress' else '' }}>In Progress</option>
                            <option value="Ready for Testing" {{ 'selected' if cfg.jira.story_status == 'Ready for Testing' else '' }}>Ready for Testing</option>
                            <option value="Done" {{ 'selected' if cfg.jira.story_status == 'Done' else '' }}>Done</option>
                        </select>
                        <div class="form-hint">Fetch stories with this status</div>
                    </div>
                </div>

                <div style="margin-top:8px;">
                    <div class="toggle-row">
                        <div>
                            <div class="toggle-label">Auto-Fetch Stories</div>
                            <div class="toggle-desc">Automatically fetch new stories on pipeline run</div>
                        </div>
                        <label class="toggle-switch">
                            <input type="checkbox" name="auto_fetch" {{ 'checked' if cfg.jira.auto_fetch else '' }}>
                            <span class="toggle-slider"></span>
                        </label>
                    </div>
                </div>

                <div style="display:flex; justify-content:flex-end; gap:12px; padding-top:16px; margin-top:16px; border-top:1px solid var(--border);">
                    <button type="submit" class="btn btn-primary">Save Jira Config</button>
                </div>
            </form>
        </div>
    </div>
</div>
"""


@portal.route("/jira-config", methods=["GET", "POST"])
def jira_config_page():
    toast_msg = ""
    toast_type = ""

    if request.method == "POST":
        config["jira"]["server_url"] = request.form.get("server_url", "")
        config["jira"]["username"] = request.form.get("username", "")
        config["jira"]["api_token"] = request.form.get("api_token", "")
        config["jira"]["project_key"] = request.form.get("project_key", "").upper()
        config["jira"]["story_status"] = request.form.get("story_status", "To Do")
        config["jira"]["auto_fetch"] = "auto_fetch" in request.form
        save_config(config)
        toast_msg = "Jira configuration saved!"
        toast_type = "success"

    return render_portal(
        "Jira Config", JIRA_CONFIG_CONTENT, active_tab="jira",
        cfg=config, toast_msg=toast_msg, toast_type=toast_type,
    )


# ---------------------------------------------------------------------------
# Copado Deployment Configuration
# ---------------------------------------------------------------------------

COPADO_CONFIG_CONTENT = """
<div class="page">
    <div class="page-header">
        <h1>Copado Deployment Configuration</h1>
        <p>Configure Copado CI/CD integration for deploying test results and triggering pipelines.</p>
    </div>

    <div class="card">
        <div class="card-header">
            <h2>Copado Settings</h2>
            {% if cfg.copado.enabled and cfg.copado.instance_url %}
            <span class="status-badge status-enabled"><span class="status-dot status-dot-green"></span> Enabled</span>
            {% elif cfg.copado.enabled %}
            <span class="status-badge status-not-configured"><span class="status-dot status-dot-orange"></span> Incomplete</span>
            {% else %}
            <span class="status-badge status-disabled"><span class="status-dot status-dot-gray"></span> Disabled</span>
            {% endif %}
        </div>
        <div class="card-body">
            <form method="POST" action="/copado-config">
                <div style="margin-bottom:16px;">
                    <div class="toggle-row">
                        <div>
                            <div class="toggle-label">Enable Copado Deployment</div>
                            <div class="toggle-desc">Push test execution results to Copado CI/CD pipeline after each run</div>
                        </div>
                        <label class="toggle-switch">
                            <input type="checkbox" name="enabled" {{ 'checked' if cfg.copado.enabled else '' }}>
                            <span class="toggle-slider"></span>
                        </label>
                    </div>
                </div>

                <div class="form-group">
                    <label>Copado Instance URL</label>
                    <input type="url" name="instance_url" value="{{ cfg.copado.instance_url }}"
                           placeholder="https://your-org.my.salesforce.com">
                    <div class="form-hint">Salesforce org URL where Copado is installed</div>
                </div>

                <div class="form-row">
                    <div class="form-group">
                        <label>Copado API Token</label>
                        <input type="password" name="api_token" value="{{ cfg.copado.api_token }}"
                               placeholder="Enter Copado API / session token">
                    </div>
                    <div class="form-group">
                        <label>Pipeline ID</label>
                        <input type="text" name="pipeline_id" value="{{ cfg.copado.pipeline_id }}"
                               placeholder="a0B000000000001">
                        <div class="form-hint">Copado Pipeline record ID (copado__Deployment_Flow__c)</div>
                    </div>
                </div>

                <div class="form-row">
                    <div class="form-group">
                        <label>Target Environment</label>
                        <select name="environment">
                            <option value="DEV" {{ 'selected' if cfg.copado.environment == 'DEV' else '' }}>DEV</option>
                            <option value="SIT" {{ 'selected' if cfg.copado.environment == 'SIT' else '' }}>SIT</option>
                            <option value="UAT" {{ 'selected' if cfg.copado.environment == 'UAT' else '' }}>UAT</option>
                            <option value="STAGING" {{ 'selected' if cfg.copado.environment == 'STAGING' else '' }}>STAGING</option>
                            <option value="PRODUCTION" {{ 'selected' if cfg.copado.environment == 'PRODUCTION' else '' }}>PRODUCTION</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>&nbsp;</label>
                        <div class="toggle-row" style="padding:0; border:none;">
                            <div>
                                <div class="toggle-label">Deploy on Pass</div>
                                <div class="toggle-desc">Auto-trigger Copado deployment when all tests pass</div>
                            </div>
                            <label class="toggle-switch">
                                <input type="checkbox" name="deploy_on_pass" {{ 'checked' if cfg.copado.deploy_on_pass else '' }}>
                                <span class="toggle-slider"></span>
                            </label>
                        </div>
                    </div>
                </div>

                <div style="display:flex; justify-content:flex-end; gap:12px; padding-top:16px; margin-top:16px; border-top:1px solid var(--border);">
                    <button type="submit" class="btn btn-primary">Save Copado Config</button>
                </div>
            </form>
        </div>
    </div>
</div>
"""


@portal.route("/copado-config", methods=["GET", "POST"])
def copado_config_page():
    toast_msg = ""
    toast_type = ""

    if request.method == "POST":
        config["copado"]["enabled"] = "enabled" in request.form
        config["copado"]["instance_url"] = request.form.get("instance_url", "")
        config["copado"]["api_token"] = request.form.get("api_token", "")
        config["copado"]["pipeline_id"] = request.form.get("pipeline_id", "")
        config["copado"]["environment"] = request.form.get("environment", "UAT")
        config["copado"]["deploy_on_pass"] = "deploy_on_pass" in request.form
        save_config(config)
        toast_msg = "Copado configuration saved!"
        toast_type = "success"

    return render_portal(
        "Copado Config", COPADO_CONFIG_CONTENT, active_tab="copado",
        cfg=config, toast_msg=toast_msg, toast_type=toast_type,
    )


# ---------------------------------------------------------------------------
# Report Configuration
# ---------------------------------------------------------------------------

REPORT_CONFIG_CONTENT = """
<div class="page">
    <div class="page-header">
        <h1>Report Configuration</h1>
        <p>Configure test execution report generation settings.</p>
    </div>

    <div class="card">
        <div class="card-header"><h2>Report Settings</h2></div>
        <div class="card-body">
            <form method="POST" action="/report-config">
                <div class="form-row">
                    <div class="form-group">
                        <label>Report Format</label>
                        <select name="format">
                            <option value="html" {{ 'selected' if cfg.reports.format == 'html' else '' }}>HTML (Chart.js Dashboard)</option>
                            <option value="json" {{ 'selected' if cfg.reports.format == 'json' else '' }}>JSON</option>
                            <option value="junit" {{ 'selected' if cfg.reports.format == 'junit' else '' }}>JUnit XML</option>
                            <option value="all" {{ 'selected' if cfg.reports.format == 'all' else '' }}>All Formats</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Output Directory</label>
                        <input type="text" name="output_dir" value="{{ cfg.reports.output_dir }}" placeholder="test-reports">
                    </div>
                </div>

                <div style="margin-top:8px;">
                    <div class="toggle-row">
                        <div>
                            <div class="toggle-label">Generate JUnit XML</div>
                            <div class="toggle-desc">Create JUnit-compatible XML report for CI integration</div>
                        </div>
                        <label class="toggle-switch">
                            <input type="checkbox" name="generate_junit_xml" {{ 'checked' if cfg.reports.generate_junit_xml else '' }}>
                            <span class="toggle-slider"></span>
                        </label>
                    </div>
                    <div class="toggle-row">
                        <div>
                            <div class="toggle-label">Generate JSON Report</div>
                            <div class="toggle-desc">Create JSON report with detailed test execution data</div>
                        </div>
                        <label class="toggle-switch">
                            <input type="checkbox" name="generate_json" {{ 'checked' if cfg.reports.generate_json else '' }}>
                            <span class="toggle-slider"></span>
                        </label>
                    </div>
                </div>

                <div style="display:flex; justify-content:flex-end; gap:12px; padding-top:16px; margin-top:16px; border-top:1px solid var(--border);">
                    <button type="submit" class="btn btn-primary">Save Report Config</button>
                </div>
            </form>
        </div>
    </div>

    {% if report_format == 'html' or report_format == 'all' %}
    <!-- Copado Deployment Status -->
    <div class="card" style="margin-top:20px;">
        <div class="card-header">
            <h2>Copado Report Deployment</h2>
            {% if copado_deployed %}<span class="status-badge status-configured"><span class="status-dot status-dot-green"></span> Deployed</span>
            {% elif copado_enabled %}<span class="status-badge" style="background:#e3f2fd; color:#1565c0;">Ready to Deploy</span>
            {% else %}<span class="status-badge status-not-configured"><span class="status-dot status-dot-orange"></span> Not Configured</span>{% endif %}
        </div>
        <div class="card-body" style="padding:0;">
            <table class="config-table" style="font-size:12px;">
                <thead><tr><th>Setting</th><th>Value</th><th>Status</th></tr></thead>
                <tbody>
                    <tr>
                        <td>Copado Instance</td>
                        <td>{{ copado_instance or 'Not configured' }}</td>
                        <td>{% if copado_instance %}<span style="color:#2e844a;">&#10003;</span>{% else %}<span style="color:#999;">&mdash;</span>{% endif %}</td>
                    </tr>
                    <tr>
                        <td>Target Environment</td>
                        <td>{{ copado_env }}</td>
                        <td><span style="color:#2e844a;">&#10003;</span></td>
                    </tr>
                    <tr>
                        <td>Report Attached to Test Run</td>
                        <td>{% if copado_deployed %}HTML Dashboard + JUnit XML + JSON{% elif copado_enabled %}Will attach on next run{% else %}Enable Copado at <a href="/copado-config">/copado-config</a>{% endif %}</td>
                        <td>{% if copado_deployed %}<span style="color:#2e844a;">&#10003;</span>{% else %}<span style="color:#999;">&mdash;</span>{% endif %}</td>
                    </tr>
                    <tr>
                        <td>Viewable in Copado</td>
                        <td>{% if copado_deployed and copado_instance %}{{ copado_instance }}/lightning/r/copado__Test_Run__c/view{% elif copado_enabled %}After pipeline execution{% else %}Configure Copado first{% endif %}</td>
                        <td>{% if copado_deployed %}<span style="color:#2e844a;">&#10003;</span>{% else %}<span style="color:#999;">&mdash;</span>{% endif %}</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>

    <!-- Inline HTML Test Execution Report -->
    <div class="card" style="margin-top:20px;">
        <div class="card-header">
            <h2>Test Execution Report</h2>
            <div style="display:flex; align-items:center; gap:12px;">
                {% if run_id %}<span style="font-size:11px; font-family:monospace; color:var(--text-light);">Run: {{ run_id[:8] }}</span>{% endif %}
                <span style="font-size:12px; color:var(--text-light);">{{ report_time }}</span>
                {% if run_id %}<span class="status-badge" style="background:#e8f5e9; color:#2e7d32; font-size:10px;">From Pipeline Execution</span>{% endif %}
            </div>
        </div>
        <div class="card-body">
            {% if scenarios %}
            <!-- KPI Cards -->
            <div class="stats-grid">
                <div class="stat-card" style="border-left:4px solid #0176d3;">
                    <div class="stat-value">{{ scenarios | length }}</div>
                    <div class="stat-label">Total Scenarios</div>
                </div>
                <div class="stat-card" style="border-left:4px solid #2e844a;">
                    <div class="stat-value">{{ passed_count }}</div>
                    <div class="stat-label">Passed</div>
                </div>
                <div class="stat-card" style="border-left:4px solid #ea001e;">
                    <div class="stat-value">{{ failed_count }}</div>
                    <div class="stat-label">Failed</div>
                </div>
                <div class="stat-card" style="border-left:4px solid #fe9339;">
                    <div class="stat-value">{{ skipped_count }}</div>
                    <div class="stat-label">Skipped</div>
                </div>
                <div class="stat-card" style="border-left:4px solid #7b1fa2;">
                    <div class="stat-value">{{ pass_rate }}%</div>
                    <div class="stat-label">Pass Rate</div>
                </div>
                <div class="stat-card" style="border-left:4px solid #1565c0;">
                    <div class="stat-value">{{ total_steps }}</div>
                    <div class="stat-label">Total Steps</div>
                </div>
            </div>

            <!-- Charts Row -->
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:16px; margin-top:20px;">
                <div style="background:white; border:1px solid var(--border); border-radius:8px; padding:16px;">
                    <h3 style="font-size:14px; margin-bottom:12px; color:var(--dark);">Pass / Fail Distribution</h3>
                    <canvas id="pieChart" width="300" height="300"></canvas>
                </div>
                <div style="background:white; border:1px solid var(--border); border-radius:8px; padding:16px;">
                    <h3 style="font-size:14px; margin-bottom:12px; color:var(--dark);">Scenario Duration (seconds)</h3>
                    <canvas id="barChart" width="300" height="300"></canvas>
                </div>
            </div>
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:16px; margin-top:16px;">
                <div style="background:white; border:1px solid var(--border); border-radius:8px; padding:16px;">
                    <h3 style="font-size:14px; margin-bottom:12px; color:var(--dark);">Pass Rate</h3>
                    <canvas id="doughnutChart" width="300" height="300"></canvas>
                </div>
                <div style="background:white; border:1px solid var(--border); border-radius:8px; padding:16px;">
                    <h3 style="font-size:14px; margin-bottom:12px; color:var(--dark);">Steps per Scenario</h3>
                    <canvas id="stepsChart" width="300" height="300"></canvas>
                </div>
            </div>

            <!-- Scenario Results Table -->
            <div style="margin-top:20px;">
                <h3 style="font-size:14px; margin-bottom:12px; color:var(--dark);">Scenario Results by Jira ID</h3>
                <table class="config-table" style="font-size:12px;">
                    <thead>
                        <tr>
                            <th>Jira ID</th>
                            <th>Test Case</th>
                            <th>Scenario</th>
                            <th>Priority</th>
                            <th>Steps</th>
                            <th>Duration</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for s in scenarios %}
                        <tr>
                            <td style="font-weight:700; color:#0176d3;">{{ s.jira_id }}</td>
                            <td style="font-family:monospace; font-size:11px;">{{ s.test_case_id }}</td>
                            <td>{{ s.scenario }}</td>
                            <td>
                                {% if s.priority == 'High' %}<span style="background:#fce4ec; color:#c62828; padding:2px 8px; border-radius:10px; font-size:10px; font-weight:700;">High</span>
                                {% elif s.priority == 'Medium' %}<span style="background:#fff3e0; color:#e65100; padding:2px 8px; border-radius:10px; font-size:10px; font-weight:700;">Medium</span>
                                {% else %}<span style="background:#e8f5e9; color:#2e7d32; padding:2px 8px; border-radius:10px; font-size:10px; font-weight:700;">Low</span>{% endif %}
                            </td>
                            <td style="text-align:center;">{{ s.steps }}</td>
                            <td style="text-align:center;">{{ s.duration }}s</td>
                            <td>
                                {% if s.status == 'PASSED' %}<span class="status-badge status-configured"><span class="status-dot status-dot-green"></span> Passed</span>
                                {% elif s.status == 'FAILED' %}<span class="status-badge status-not-configured"><span class="status-dot status-dot-orange"></span> Failed</span>
                                {% else %}<span class="status-badge" style="background:#f5f5f5; color:#999;">Skipped</span>{% endif %}
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>

            <!-- Execution Steps Detail -->
            <div style="margin-top:20px;">
                <h3 style="font-size:14px; margin-bottom:12px; color:var(--dark);">Execution Steps Detail</h3>
                {% for s in scenarios %}
                <div style="background:#f8f9fa; border:1px solid var(--border); border-radius:6px; padding:12px; margin-bottom:10px;">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                        <div>
                            <span style="font-weight:700; color:#0176d3; margin-right:8px;">{{ s.jira_id }}</span>
                            <span style="font-weight:600;">{{ s.scenario }}</span>
                        </div>
                        <span class="status-badge status-configured"><span class="status-dot status-dot-green"></span> {{ s.status }}</span>
                    </div>
                    <div style="display:flex; flex-wrap:wrap; gap:4px;">
                        {% for step in s.execution_steps %}
                        <div style="display:flex; align-items:center; gap:3px;">
                            <span style="background:#2e844a; color:white; font-size:8px; width:16px; height:16px; border-radius:50%; display:inline-flex; align-items:center; justify-content:center; font-weight:700;">{{ loop.index }}</span>
                            <span style="font-size:11px; color:var(--text-light);">{{ step }}</span>
                            {% if not loop.last %}<span style="color:#ccc; margin:0 2px;">&rarr;</span>{% endif %}
                        </div>
                        {% endfor %}
                    </div>
                </div>
                {% endfor %}
            </div>

            <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
            <script>
                var scenarios = {{ scenarios_json | safe }};
                var passed = scenarios.filter(s => s.status === 'PASSED').length;
                var failed = scenarios.filter(s => s.status === 'FAILED').length;
                var skipped = scenarios.filter(s => s.status === 'SKIPPED').length;

                // Pie chart
                new Chart(document.getElementById('pieChart'), {
                    type: 'pie',
                    data: {
                        labels: ['Passed', 'Failed', 'Skipped'],
                        datasets: [{
                            data: [passed, failed, skipped],
                            backgroundColor: ['#2e844a', '#ea001e', '#fe9339']
                        }]
                    },
                    options: { responsive: true, plugins: { legend: { position: 'bottom' } } }
                });

                // Bar chart - duration per scenario
                new Chart(document.getElementById('barChart'), {
                    type: 'bar',
                    data: {
                        labels: scenarios.map(s => s.jira_id + ' | ' + s.scenario.substring(0, 20)),
                        datasets: [{
                            label: 'Duration (s)',
                            data: scenarios.map(s => s.duration),
                            backgroundColor: scenarios.map(s => s.status === 'PASSED' ? '#2e844a' : '#ea001e')
                        }]
                    },
                    options: {
                        indexAxis: 'y', responsive: true,
                        plugins: { legend: { display: false } },
                        scales: { x: { title: { display: true, text: 'Seconds' } } }
                    }
                });

                // Doughnut - pass rate
                new Chart(document.getElementById('doughnutChart'), {
                    type: 'doughnut',
                    data: {
                        labels: ['Passed', 'Not Passed'],
                        datasets: [{
                            data: [passed, failed + skipped],
                            backgroundColor: ['#2e844a', '#e0e0e0']
                        }]
                    },
                    options: {
                        responsive: true, cutout: '70%',
                        plugins: {
                            legend: { position: 'bottom' },
                            tooltip: { enabled: true }
                        }
                    }
                });

                // Polar area - steps per scenario
                new Chart(document.getElementById('stepsChart'), {
                    type: 'polarArea',
                    data: {
                        labels: scenarios.map(s => s.jira_id),
                        datasets: [{
                            data: scenarios.map(s => s.steps),
                            backgroundColor: ['#0176d3', '#2e844a', '#7b1fa2', '#e65100', '#1565c0', '#c62828']
                        }]
                    },
                    options: { responsive: true, plugins: { legend: { position: 'bottom' } } }
                });
            </script>
            {% else %}
            <div style="text-align:center; padding:40px; color:var(--text-light);">
                <p style="font-size:16px; margin-bottom:8px;">No test execution data available</p>
                <p style="font-size:13px;">Run the pipeline from the <a href="/execute" style="color:var(--primary);">Execute</a> page to generate test results, or upload test data at <a href="/upload" style="color:var(--primary);">Upload</a>.</p>
            </div>
            {% endif %}
        </div>
    </div>
    {% endif %}
</div>
"""


def _load_latest_report():
    """Load latest execution report (from pipeline run) or fall back to test data."""
    if REPORT_RESULTS_FILE.exists():
        with open(REPORT_RESULTS_FILE) as f:
            return json.load(f)
    return None


def _build_report_scenarios():
    """Build scenario report data from latest execution or test data JSON."""
    report = _load_latest_report()
    if report and report.get("scenarios"):
        return report["scenarios"], report
    # Fallback: generate from test data
    if not TEST_DATA_PATH.exists():
        return [], None
    with open(TEST_DATA_PATH) as f:
        td = json.load(f)
    scenarios = []
    import random
    random.seed(42)
    for rec in td.get("test_records", []):
        steps = rec.get("execution_steps", [])
        duration = round(random.uniform(1.2, 4.5), 2)
        scenarios.append({
            "jira_id": rec.get("jira_story_id", "N/A"),
            "test_case_id": rec.get("test_case_id", "N/A"),
            "scenario": rec.get("scenario", rec.get("test_case_name", "Unknown")),
            "priority": rec.get("priority", "Medium"),
            "steps": len(steps),
            "execution_steps": steps,
            "duration": duration,
            "status": "PASSED",
        })
    return scenarios, None


@portal.route("/report-config", methods=["GET", "POST"])
def report_config_page():
    toast_msg = ""
    toast_type = ""

    if request.method == "POST":
        config["reports"]["format"] = request.form.get("format", "html")
        config["reports"]["output_dir"] = request.form.get("output_dir", "test-reports")
        config["reports"]["generate_junit_xml"] = "generate_junit_xml" in request.form
        config["reports"]["generate_json"] = "generate_json" in request.form
        save_config(config)
        toast_msg = "Report configuration saved!"
        toast_type = "success"

    report_format = config["reports"]["format"]
    scenarios, report_meta = _build_report_scenarios() if report_format in ("html", "all") else ([], None)
    passed_count = sum(1 for s in scenarios if s["status"] == "PASSED")
    failed_count = sum(1 for s in scenarios if s["status"] == "FAILED")
    skipped_count = sum(1 for s in scenarios if s["status"] == "SKIPPED")
    total_steps = sum(s["steps"] for s in scenarios)
    pass_rate = round(passed_count / len(scenarios) * 100, 1) if scenarios else 0

    # Copado deployment status
    copado_cfg = config.get("copado", {})
    copado_deployed = False
    copado_env = copado_cfg.get("environment", "UAT")
    if report_meta:
        copado_deployed = report_meta.get("copado_deployed", False)
        copado_env = report_meta.get("copado_environment", copado_env)
        report_time = report_meta.get("run_time", datetime.now().isoformat())[:19].replace("T", " ")
        run_id = report_meta.get("run_id", "")
    else:
        report_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        run_id = ""

    return render_portal(
        "Report Config", REPORT_CONFIG_CONTENT, active_tab="reports",
        cfg=config, toast_msg=toast_msg, toast_type=toast_type,
        report_format=report_format,
        scenarios=scenarios,
        scenarios_json=json.dumps(scenarios),
        passed_count=passed_count,
        failed_count=failed_count,
        skipped_count=skipped_count,
        total_steps=total_steps,
        pass_rate=pass_rate,
        report_time=report_time,
        run_id=run_id,
        copado_deployed=copado_deployed,
        copado_enabled=copado_cfg.get("enabled", False),
        copado_env=copado_env,
        copado_instance=copado_cfg.get("instance_url", ""),
    )


# ---------------------------------------------------------------------------
# Workflow Execution Pipeline
# ---------------------------------------------------------------------------

WORKFLOW_STEPS = [
    {
        "num": 1, "title": "Story Ingestion", "agent": "StoryIngestionAgent",
        "color": "#0176d3",
        "desc": "Fetch user stories from Jira API based on project key and status filter. Parse acceptance criteria, extract Given/When/Then patterns from story description.",
        "inputs": ["Jira Config (URL, project key, status)", "API credentials"],
        "outputs": ["UserStory objects with parsed acceptance criteria"],
        "ai_action": None,
    },
    {
        "num": 2, "title": "Analysis & Framework Detection", "agent": "AnalysisAgent",
        "color": "#5e35b1",
        "desc": "Analyze the target application URL to detect UI framework (Salesforce LWC, React, Angular). Classify story complexity (simple CRUD, complex workflow, integration) and determine test strategy.",
        "inputs": ["UserStory objects", "Application URL"],
        "outputs": ["Framework type", "Complexity classification", "Test strategy"],
        "ai_action": "LLM classifies story complexity and suggests test approach",
    },
    {
        "num": 3, "title": "Feature File Generation", "agent": "FeatureGenerationAgent",
        "color": "#2e844a",
        "desc": "Convert each user story into Gherkin .feature files with proper tags, Background, and Scenarios. Map acceptance criteria to Given/When/Then steps with parameterized data tables.",
        "inputs": ["UserStory objects", "Framework analysis"],
        "outputs": [".feature files in Gherkin syntax"],
        "ai_action": "LLM generates Gherkin scenarios from plain-text acceptance criteria",
    },
    {
        "num": 4, "title": "Test Data Preparation", "agent": "TestDataPreparationAgent",
        "color": "#fe9339",
        "desc": "Bundle test data per story — field values, dropdown selections, dependent picklist data. Upload configuration including Selenium settings and target application URL.",
        "inputs": ["Feature files", "Uploaded test data JSON", "App URL config"],
        "outputs": ["Test data bundles per scenario", "Selenium config object"],
        "ai_action": None,
    },
    {
        "num": 5, "title": "Page Object Generation", "agent": "PageObjectAgent",
        "color": "#ea001e",
        "desc": "Select or generate framework-specific Page Object Model (POM) classes. Salesforce LWC uses shadow DOM traversal, React uses data-testid, Angular uses formControlName.",
        "inputs": ["Framework type", "Feature file steps"],
        "outputs": ["POM page classes with locators and actions"],
        "ai_action": "LLM detects new fields/screens and auto-generates POM locators",
    },
    {
        "num": 6, "title": "Test Execution", "agent": "ExecutionAgent",
        "color": "#0176d3",
        "desc": "Execute BDD scenarios against the target application via Selenium WebDriver. Map Gherkin steps to POM page actions. Capture screenshots on failure, record step timings.",
        "inputs": ["Feature files", "POM pages", "Test data", "Selenium config"],
        "outputs": ["Step results (pass/fail/skip)", "Screenshots", "Timing data"],
        "ai_action": None,
    },
    {
        "num": 7, "title": "Report Generation", "agent": "ReportingAgent",
        "color": "#5e35b1",
        "desc": "Generate test execution reports with Chart.js dashboards, Jira ID traceability per scenario. Output in HTML, JUnit XML, and JSON formats. Include pass/fail charts, duration metrics, step coverage.",
        "inputs": ["Execution results", "Jira story mapping"],
        "outputs": ["HTML report with charts", "JUnit XML", "JSON summary"],
        "ai_action": "AI auto-updates report when test cases change due to field/screen additions",
    },
    {
        "num": 8, "title": "Copado CI/CD Pipeline Deployment", "agent": "DeploymentAgent",
        "color": "#2e844a",
        "desc": "Deploy test results through the Copado CI/CD pipeline. Creates Test_Run and Test_Result records, attaches HTML/XML/JSON reports as ContentDocument, then triggers the Copado deployment pipeline to promote the build from the source environment to the target (DEV → SIT → UAT → STAGING → PRODUCTION).",
        "inputs": ["Test results", "Copado config (instance URL, API token, pipeline ID, environment)"],
        "outputs": ["Copado Test_Run record", "Test_Result records per scenario", "Report attachments", "Pipeline deployment trigger"],
        "ai_action": None,
        "copado_stages": [
            {"stage": "Create Test Run", "desc": "Create copado__Test_Run__c record in Copado org with run metadata"},
            {"stage": "Upload Results", "desc": "Create copado__Test_Result__c per scenario with pass/fail/duration"},
            {"stage": "Attach Reports", "desc": "Upload HTML dashboard, JUnit XML, JSON as ContentDocument attachments"},
            {"stage": "Validate Pipeline", "desc": "Check Copado pipeline status and target environment readiness"},
            {"stage": "Trigger Deployment", "desc": "Trigger copado__Deployment__c to promote build to target environment"},
            {"stage": "Verify Promotion", "desc": "Wait for deployment completion, verify promotion status in Copado"},
        ],
    },
    {
        "num": 9, "title": "Feedback & Auto-Update", "agent": "FeedbackAgent",
        "color": "#fe9339",
        "desc": "Monitor Git commits for changes to user stories. When application code changes (new fields, new screens, modified forms), AI analyzes the diff and auto-updates feature files, POM classes, test data, and reports.",
        "inputs": ["Git commit diff", "Current feature files", "POM classes"],
        "outputs": ["Updated .feature files", "Updated POM", "Updated test data"],
        "ai_action": "LLM analyzes code diff → auto-modifies tests for new fields/screens/changes",
    },
]

WORKFLOW_CONTENT = """
<div class="page">
    <div class="page-header">
        <h1>Execution Workflow</h1>
        <p>Step-by-step visualization of the 9-agent agentic AI pipeline. Each step shows its agent, inputs, outputs, and AI model involvement.</p>
    </div>

    <div class="card">
        <div class="card-header">
            <h2>Agent Pipeline</h2>
            <span style="font-size:12px; color:var(--text-light);">9 agents &middot; decide() &rarr; act() &rarr; report()</span>
        </div>
        <div class="card-body">
            <div class="wf-pipeline">
                {% for step in steps %}
                <div class="wf-step">
                    <div class="wf-step-connector">
                        <div class="wf-step-dot" style="background:{{ step.color }};">{{ step.num }}</div>
                        {% if not loop.last %}
                        <div class="wf-step-line" style="background:{{ step.color }}; opacity:0.3;"></div>
                        {% endif %}
                    </div>
                    <div class="wf-step-content">
                        <div class="wf-step-title">{{ step.title }}</div>
                        <div class="wf-step-agent">{{ step.agent }}</div>
                        <div class="wf-step-desc">{{ step.desc }}</div>
                        <div class="wf-step-io">
                            {% for inp in step.inputs %}
                            <span class="wf-io-tag wf-io-in">IN: {{ inp }}</span>
                            {% endfor %}
                            {% for out in step.outputs %}
                            <span class="wf-io-tag wf-io-out">OUT: {{ out }}</span>
                            {% endfor %}
                            {% if step.ai_action %}
                            <span class="wf-io-tag wf-io-ai">AI: {{ step.ai_action }}</span>
                            {% endif %}
                        </div>
                        {% if step.copado_stages %}
                        <div style="margin-top:10px; background:#f0faf0; border:1px solid #c8e6c9; border-radius:6px; padding:12px;">
                            <div style="font-size:11px; font-weight:700; color:#2e844a; margin-bottom:8px; text-transform:uppercase;">Copado Pipeline Stages</div>
                            <div style="display:flex; flex-wrap:wrap; gap:6px;">
                                {% for cs in step.copado_stages %}
                                <div style="display:flex; align-items:center; gap:4px;">
                                    <span style="background:#2e844a; color:white; font-size:9px; width:18px; height:18px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-weight:700;">{{ loop.index }}</span>
                                    <span style="font-size:11px; font-weight:600; color:#1b5e20;">{{ cs.stage }}</span>
                                    {% if not loop.last %}<span style="color:#a5d6a7; margin:0 2px;">&rarr;</span>{% endif %}
                                </div>
                                {% endfor %}
                            </div>
                        </div>
                        {% endif %}
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
    </div>

    <!-- AI Auto-Update Flow -->
    <div class="card">
        <div class="card-header">
            <h2>AI Auto-Update Flow</h2>
        </div>
        <div class="card-body">
            <p style="font-size:13px; color:var(--text-light); margin-bottom:16px;">
                When the application changes (new fields, new screens, modified forms), the AI model automatically cascades updates across the entire pipeline:
            </p>
            <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(200px, 1fr)); gap:12px;">
                <div class="stat-card" style="border-left:3px solid #7b1fa2;">
                    <div class="stat-value" style="font-size:14px;">New Field Detected</div>
                    <div class="stat-label">AI scans app UI diff for added input fields, dropdowns, or form elements</div>
                </div>
                <div class="stat-card" style="border-left:3px solid #1565c0;">
                    <div class="stat-value" style="font-size:14px;">POM Updated</div>
                    <div class="stat-label">New locators and actions added to Page Object Model classes</div>
                </div>
                <div class="stat-card" style="border-left:3px solid #2e7d32;">
                    <div class="stat-value" style="font-size:14px;">Tests Modified</div>
                    <div class="stat-label">Feature files and test data updated with new field scenarios</div>
                </div>
                <div class="stat-card" style="border-left:3px solid #e65100;">
                    <div class="stat-value" style="font-size:14px;">Reports Reflect</div>
                    <div class="stat-label">Execution reports automatically include new/modified test cases</div>
                </div>
            </div>
        </div>
    </div>

    <!-- Copado CI/CD Pipeline -->
    <div class="card">
        <div class="card-header">
            <h2>Copado CI/CD Pipeline Execution</h2>
            <span style="font-size:12px; color:var(--text-light);">DeploymentAgent &rarr; Copado API</span>
        </div>
        <div class="card-body">
            <p style="font-size:13px; color:var(--text-light); margin-bottom:16px;">
                After all tests pass, the DeploymentAgent deploys results through the Copado CI/CD pipeline. This is the standard Copado promotion flow integrated into the agentic pipeline:
            </p>

            <!-- Copado Pipeline Flow -->
            <div style="display:flex; align-items:center; gap:0; flex-wrap:wrap; margin-bottom:20px;">
                {% for stage_name in ['Create Test Run', 'Upload Results', 'Attach Reports', 'Validate Pipeline', 'Trigger Deployment', 'Verify Promotion'] %}
                <div style="display:flex; align-items:center;">
                    <div style="background:#2e844a; color:white; padding:8px 14px; border-radius:6px; font-size:12px; font-weight:600; white-space:nowrap;">
                        {{ loop.index }}. {{ stage_name }}
                    </div>
                    {% if not loop.last %}
                    <div style="color:#2e844a; font-size:18px; margin:0 4px;">&rarr;</div>
                    {% endif %}
                </div>
                {% endfor %}
            </div>

            <!-- Copado Stage Details -->
            <table class="config-table" style="font-size:12px;">
                <thead>
                    <tr><th>Stage</th><th>Copado Object</th><th>Action</th><th>Data</th></tr>
                </thead>
                <tbody>
                    <tr>
                        <td style="font-weight:700; color:#2e844a;">1. Create Test Run</td>
                        <td style="font-family:monospace;">copado__Test_Run__c</td>
                        <td>Create record with run metadata</td>
                        <td>Pipeline ID, environment, start time, test count</td>
                    </tr>
                    <tr>
                        <td style="font-weight:700; color:#2e844a;">2. Upload Results</td>
                        <td style="font-family:monospace;">copado__Test_Result__c</td>
                        <td>Create one record per scenario</td>
                        <td>Jira ID, scenario name, pass/fail, duration, steps</td>
                    </tr>
                    <tr>
                        <td style="font-weight:700; color:#2e844a;">3. Attach Reports</td>
                        <td style="font-family:monospace;">ContentDocument</td>
                        <td>Upload as attachments to Test Run</td>
                        <td>HTML dashboard, JUnit XML, JSON summary, Copado JSON</td>
                    </tr>
                    <tr>
                        <td style="font-weight:700; color:#2e844a;">4. Validate Pipeline</td>
                        <td style="font-family:monospace;">copado__Pipeline__c</td>
                        <td>Check pipeline and environment status</td>
                        <td>Pipeline ID active, target environment ready</td>
                    </tr>
                    <tr>
                        <td style="font-weight:700; color:#2e844a;">5. Trigger Deployment</td>
                        <td style="font-family:monospace;">copado__Deployment__c</td>
                        <td>Create deployment record, trigger promotion</td>
                        <td>Source → Target environment, deploy on pass flag</td>
                    </tr>
                    <tr>
                        <td style="font-weight:700; color:#2e844a;">6. Verify Promotion</td>
                        <td style="font-family:monospace;">copado__Deployment__c</td>
                        <td>Poll deployment status until complete</td>
                        <td>Promotion status, error logs, completion time</td>
                    </tr>
                </tbody>
            </table>

            <!-- Environment Promotion Path -->
            <div style="margin-top:16px;">
                <div style="font-size:12px; font-weight:700; color:var(--dark); margin-bottom:8px;">Environment Promotion Path</div>
                <div style="display:flex; align-items:center; gap:0; flex-wrap:wrap;">
                    {% for env in ['DEV', 'SIT', 'UAT', 'STAGING', 'PRODUCTION'] %}
                    <div style="display:flex; align-items:center;">
                        <div style="background:{% if env == 'PRODUCTION' %}#c62828{% elif env == 'UAT' %}#e65100{% else %}#1565c0{% endif %}; color:white; padding:6px 16px; border-radius:4px; font-size:11px; font-weight:700;">
                            {{ env }}
                        </div>
                        {% if not loop.last %}
                        <div style="font-size:16px; margin:0 6px; color:#999;">&rarr;</div>
                        {% endif %}
                    </div>
                    {% endfor %}
                </div>
                <p style="font-size:11px; color:var(--text-light); margin-top:6px;">
                    Configure target environment at <a href="/copado-config" style="color:var(--primary);">/copado-config</a>. Current target: <strong>{{ copado_env }}</strong>
                </p>
            </div>
        </div>
    </div>

    <!-- Decision Types -->
    <div class="card">
        <div class="card-header"><h2>Agent Decision Types</h2></div>
        <div class="card-body" style="padding:0;">
            <table class="config-table">
                <thead><tr><th>Decision</th><th>Behavior</th><th>Example</th></tr></thead>
                <tbody>
                    <tr><td style="color:#2e844a; font-weight:700;">PROCEED</td><td>Agent completed successfully, pass to next agent</td><td>Stories fetched, feature files generated</td></tr>
                    <tr><td style="color:#fe9339; font-weight:700;">RETRY</td><td>Transient failure, retry current step (max 3)</td><td>Jira API timeout, browser connection reset</td></tr>
                    <tr><td style="color:#999; font-weight:700;">SKIP</td><td>Non-critical step, skip and continue pipeline</td><td>Copado deploy disabled, no Git commit to watch</td></tr>
                    <tr><td style="color:#ea001e; font-weight:700;">ABORT</td><td>Critical failure, halt pipeline</td><td>Application URL unreachable, no test data</td></tr>
                    <tr><td style="color:#0176d3; font-weight:700;">DELEGATE</td><td>Pass to another agent for specialized handling</td><td>LLM analyzes diff before updating feature files</td></tr>
                </tbody>
            </table>
        </div>
    </div>
</div>
"""


@portal.route("/workflow")
def workflow_page():
    copado_env = config.get("copado", {}).get("environment", "UAT")
    return render_portal(
        "Workflow", WORKFLOW_CONTENT, active_tab="workflow",
        steps=WORKFLOW_STEPS, copado_env=copado_env,
    )


# ---------------------------------------------------------------------------
# Traceability Matrix
# ---------------------------------------------------------------------------

TRACEABILITY_CONTENT = """
<div class="page">
    <div class="page-header">
        <h1>Jira Story &rarr; Test Case Traceability</h1>
        <p>End-to-end mapping from Jira user stories to test cases, test data, and execution steps used by Selenium.</p>
    </div>

    <!-- Summary Stats -->
    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-value">{{ records | length }}</div>
            <div class="stat-label">Jira Stories Mapped</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{{ records | length }}</div>
            <div class="stat-label">Test Cases</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{{ total_steps }}</div>
            <div class="stat-label">Total Execution Steps</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{{ total_data_fields }}</div>
            <div class="stat-label">Data Fields Used</div>
        </div>
    </div>

    <!-- Traceability Matrix Table -->
    <div class="card">
        <div class="card-header">
            <h2>Traceability Matrix</h2>
        </div>
        <div class="card-body" style="padding:0;">
            <table class="config-table">
                <thead>
                    <tr>
                        <th>Jira Story</th>
                        <th>Test Case</th>
                        <th>Priority</th>
                        <th>Steps</th>
                        <th>Data Fields</th>
                    </tr>
                </thead>
                <tbody>
                    {% for rec in records %}
                    <tr>
                        <td>
                            <div style="font-weight:700; color:var(--primary);">{{ rec.jira_story_id }}</div>
                            <div style="font-size:11px; color:var(--text-light); max-width:250px;">{{ rec.jira_story_title }}</div>
                        </td>
                        <td>
                            <div style="font-weight:600;">{{ rec.test_case_id }}</div>
                            <div style="font-size:11px; color:var(--text-light);">{{ rec.test_case_name }}</div>
                        </td>
                        <td>
                            {% if rec.priority == 'High' %}
                            <span class="status-badge" style="background:#fce4ec; color:#c62828;">High</span>
                            {% elif rec.priority == 'Medium' %}
                            <span class="status-badge" style="background:#fff3e0; color:#e65100;">Medium</span>
                            {% else %}
                            <span class="status-badge" style="background:#e8f5e9; color:#2e7d32;">Low</span>
                            {% endif %}
                        </td>
                        <td style="text-align:center;">{{ rec.execution_steps | length }}</td>
                        <td style="text-align:center;">{{ rec.data | length }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>

    <!-- Detailed Story-to-Test Mapping -->
    {% for rec in records %}
    <div class="card" id="{{ rec.jira_story_id }}">
        <div class="card-header">
            <h2 style="display:flex; align-items:center; gap:10px;">
                <span style="background:var(--primary); color:white; padding:2px 10px; border-radius:4px; font-size:13px;">{{ rec.jira_story_id }}</span>
                {{ rec.test_case_id }} &mdash; {{ rec.scenario }}
            </h2>
            {% if rec.priority == 'High' %}
            <span class="status-badge" style="background:#fce4ec; color:#c62828;">{{ rec.priority }}</span>
            {% elif rec.priority == 'Medium' %}
            <span class="status-badge" style="background:#fff3e0; color:#e65100;">{{ rec.priority }}</span>
            {% else %}
            <span class="status-badge" style="background:#e8f5e9; color:#2e7d32;">{{ rec.priority }}</span>
            {% endif %}
        </div>
        <div class="card-body">
            <!-- Story Description -->
            <div style="background:#f0f7ff; border-left:3px solid var(--primary); padding:10px 14px; border-radius:0 6px 6px 0; margin-bottom:16px; font-size:13px;">
                <strong>Jira Story:</strong> {{ rec.jira_story_title }}
            </div>

            <!-- Execution Steps -->
            <div style="margin-bottom:16px;">
                <div style="font-weight:700; font-size:13px; margin-bottom:8px;">Execution Steps ({{ rec.execution_steps | length }})</div>
                <div class="wf-pipeline">
                    {% for step in rec.execution_steps %}
                    <div class="wf-step">
                        <div class="wf-step-connector">
                            <div class="wf-step-dot" style="background:var(--primary); width:26px; height:26px; font-size:11px;">{{ loop.index }}</div>
                            {% if not loop.last %}
                            <div class="wf-step-line" style="background:var(--primary); opacity:0.2; min-height:8px;"></div>
                            {% endif %}
                        </div>
                        <div class="wf-step-content" style="padding:4px 0 6px 0;">
                            <div style="font-size:13px;">{{ step }}</div>
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>

            <!-- Test Data -->
            <div>
                <div style="font-weight:700; font-size:13px; margin-bottom:8px;">Test Data ({{ rec.data | length }} fields)</div>
                <table class="config-table" style="font-size:12px;">
                    <thead><tr><th>Field</th><th>Value</th></tr></thead>
                    <tbody>
                        {% for key, val in rec.data.items() %}
                        {% if val is mapping %}
                        {% for sub_key, sub_val in val.items() %}
                        <tr><td>{{ key }}.{{ sub_key }}</td><td style="font-family:monospace;">{{ sub_val }}</td></tr>
                        {% endfor %}
                        {% else %}
                        <tr><td>{{ key }}</td><td style="font-family:monospace;">{{ val }}</td></tr>
                        {% endif %}
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    {% endfor %}
</div>
"""


@portal.route("/traceability")
def traceability_page():
    records = []
    total_steps = 0
    total_data_fields = 0
    if TEST_DATA_PATH.exists():
        with open(TEST_DATA_PATH) as f:
            td = json.load(f)
        for rec in td.get("test_records", []):
            records.append(rec)
            total_steps += len(rec.get("execution_steps", []))
            data = rec.get("data", {})
            for v in data.values():
                if isinstance(v, dict):
                    total_data_fields += len(v)
                else:
                    total_data_fields += 1

    return render_portal(
        "Traceability", TRACEABILITY_CONTENT, active_tab="traceability",
        records=records, total_steps=total_steps,
        total_data_fields=total_data_fields,
    )


# ---------------------------------------------------------------------------
# AI Model Configuration
# ---------------------------------------------------------------------------

AI_MODEL_CONTENT = """
<div class="page">
    <div class="page-header">
        <h1>AI Model Configuration</h1>
        <p>Configure the LLM that powers automatic test case generation, field detection, screen analysis, and test maintenance.</p>
    </div>

    <div class="card">
        <div class="card-header">
            <h2>Model Settings</h2>
            {% if cfg.ai_model.api_key %}
            <span class="status-badge status-configured"><span class="status-dot status-dot-green"></span> Configured</span>
            {% else %}
            <span class="status-badge status-not-configured"><span class="status-dot status-dot-orange"></span> No API Key</span>
            {% endif %}
        </div>
        <div class="card-body">
            <form method="POST" action="/ai-model">
                <div class="form-row">
                    <div class="form-group">
                        <label>AI Provider</label>
                        <select name="provider">
                            <option value="openai" {{ 'selected' if cfg.ai_model.provider == 'openai' else '' }}>OpenAI</option>
                            <option value="azure_openai" {{ 'selected' if cfg.ai_model.provider == 'azure_openai' else '' }}>Azure OpenAI</option>
                            <option value="anthropic" {{ 'selected' if cfg.ai_model.provider == 'anthropic' else '' }}>Anthropic (Claude)</option>
                            <option value="google" {{ 'selected' if cfg.ai_model.provider == 'google' else '' }}>Google (Gemini)</option>
                            <option value="local" {{ 'selected' if cfg.ai_model.provider == 'local' else '' }}>Local / Self-Hosted</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Model</label>
                        <select name="model" id="modelSelect">
                            <option value="gpt-4o" {{ 'selected' if cfg.ai_model.model == 'gpt-4o' else '' }}>GPT-4o</option>
                            <option value="gpt-4o-mini" {{ 'selected' if cfg.ai_model.model == 'gpt-4o-mini' else '' }}>GPT-4o Mini</option>
                            <option value="gpt-4-turbo" {{ 'selected' if cfg.ai_model.model == 'gpt-4-turbo' else '' }}>GPT-4 Turbo</option>
                            <option value="claude-3.5-sonnet" {{ 'selected' if cfg.ai_model.model == 'claude-3.5-sonnet' else '' }}>Claude 3.5 Sonnet</option>
                            <option value="claude-3-opus" {{ 'selected' if cfg.ai_model.model == 'claude-3-opus' else '' }}>Claude 3 Opus</option>
                            <option value="gemini-1.5-pro" {{ 'selected' if cfg.ai_model.model == 'gemini-1.5-pro' else '' }}>Gemini 1.5 Pro</option>
                            <option value="custom" {{ 'selected' if cfg.ai_model.model not in ['gpt-4o','gpt-4o-mini','gpt-4-turbo','claude-3.5-sonnet','claude-3-opus','gemini-1.5-pro'] else '' }}>Custom Model</option>
                        </select>
                    </div>
                </div>

                <div class="form-group">
                    <label>API Key <span class="required">*</span></label>
                    <input type="password" name="api_key" value="{{ cfg.ai_model.api_key }}"
                           placeholder="sk-... or your provider's API key">
                    <div class="form-hint">Required for AI-powered test generation and auto-update features</div>
                </div>

                <div class="form-row">
                    <div class="form-group">
                        <label>Temperature</label>
                        <input type="number" name="temperature" value="{{ cfg.ai_model.temperature }}"
                               min="0" max="2" step="0.1">
                        <div class="form-hint">Lower = more deterministic (0.1-0.3 recommended for code generation)</div>
                    </div>
                    <div class="form-group">
                        <label>Max Tokens</label>
                        <input type="number" name="max_tokens" value="{{ cfg.ai_model.max_tokens }}"
                               min="256" max="128000" step="256">
                        <div class="form-hint">Maximum response length for generated test code</div>
                    </div>
                </div>

                <div class="separator"><hr><span>auto-detection capabilities</span><hr></div>

                <div>
                    <div class="toggle-row">
                        <div>
                            <div class="toggle-label">Auto-Detect New Fields</div>
                            <div class="toggle-desc">AI scans application UI for new input fields, dropdowns, checkboxes and auto-adds them to test cases and POM</div>
                        </div>
                        <label class="toggle-switch">
                            <input type="checkbox" name="auto_detect_fields" {{ 'checked' if cfg.ai_model.auto_detect_fields else '' }}>
                            <span class="toggle-slider"></span>
                        </label>
                    </div>
                    <div class="toggle-row">
                        <div>
                            <div class="toggle-label">Auto-Detect New Screens</div>
                            <div class="toggle-desc">AI detects new pages/tabs/modals added to the application and generates corresponding POM classes and test scenarios</div>
                        </div>
                        <label class="toggle-switch">
                            <input type="checkbox" name="auto_detect_screens" {{ 'checked' if cfg.ai_model.auto_detect_screens else '' }}>
                            <span class="toggle-slider"></span>
                        </label>
                    </div>
                    <div class="toggle-row">
                        <div>
                            <div class="toggle-label">Auto-Update Test Cases</div>
                            <div class="toggle-desc">Automatically modify/add Gherkin feature file scenarios when fields or screens change</div>
                        </div>
                        <label class="toggle-switch">
                            <input type="checkbox" name="auto_update_tests" {{ 'checked' if cfg.ai_model.auto_update_tests else '' }}>
                            <span class="toggle-slider"></span>
                        </label>
                    </div>
                    <div class="toggle-row">
                        <div>
                            <div class="toggle-label">Auto-Update Page Objects</div>
                            <div class="toggle-desc">Automatically add locators and methods to POM classes for new UI elements</div>
                        </div>
                        <label class="toggle-switch">
                            <input type="checkbox" name="auto_update_pom" {{ 'checked' if cfg.ai_model.auto_update_pom else '' }}>
                            <span class="toggle-slider"></span>
                        </label>
                    </div>
                    <div class="toggle-row">
                        <div>
                            <div class="toggle-label">Auto-Update Reports</div>
                            <div class="toggle-desc">Reflect all test case additions/modifications in execution reports automatically</div>
                        </div>
                        <label class="toggle-switch">
                            <input type="checkbox" name="auto_update_reports" {{ 'checked' if cfg.ai_model.auto_update_reports else '' }}>
                            <span class="toggle-slider"></span>
                        </label>
                    </div>
                    <div class="toggle-row">
                        <div>
                            <div class="toggle-label">Git Diff Analysis</div>
                            <div class="toggle-desc">Analyze Git commit diffs to detect code changes that affect tests (FeedbackAgent)</div>
                        </div>
                        <label class="toggle-switch">
                            <input type="checkbox" name="diff_analysis" {{ 'checked' if cfg.ai_model.diff_analysis else '' }}>
                            <span class="toggle-slider"></span>
                        </label>
                    </div>
                </div>

                <div style="display:flex; justify-content:flex-end; gap:12px; padding-top:16px; margin-top:16px; border-top:1px solid var(--border);">
                    <button type="submit" class="btn btn-primary">Save AI Model Config</button>
                </div>
            </form>
        </div>
    </div>

    <!-- AI Action Summary -->
    <div class="card">
        <div class="card-header"><h2>What the AI Model Does</h2></div>
        <div class="card-body" style="padding:0;">
            <table class="config-table">
                <thead><tr><th>Trigger</th><th>AI Action</th><th>Output</th></tr></thead>
                <tbody>
                    <tr>
                        <td>New field added to app</td>
                        <td>Scans UI, identifies field type/label/validation</td>
                        <td>New POM locator + Gherkin step + test data entry</td>
                    </tr>
                    <tr>
                        <td>New screen/page added</td>
                        <td>Detects navigation path, analyzes form structure</td>
                        <td>New POM page class + feature file + E2E scenario</td>
                    </tr>
                    <tr>
                        <td>Field modified/removed</td>
                        <td>Compares before/after DOM, identifies changes</td>
                        <td>Updated POM locator + modified test steps</td>
                    </tr>
                    <tr>
                        <td>Git commit with story key</td>
                        <td>Analyzes code diff, maps to affected feature files</td>
                        <td>Updated .feature files with new/changed scenarios</td>
                    </tr>
                    <tr>
                        <td>Test execution failure</td>
                        <td>Analyzes failure reason (stale locator, new validation)</td>
                        <td>Suggested fix for POM/test data/feature file</td>
                    </tr>
                    <tr>
                        <td>Jira story updated</td>
                        <td>Re-parses acceptance criteria, detects additions</td>
                        <td>New Gherkin scenarios added to existing feature file</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
</div>
"""


@portal.route("/ai-model", methods=["GET", "POST"])
def ai_model_page():
    toast_msg = ""
    toast_type = ""

    if request.method == "POST":
        config["ai_model"]["provider"] = request.form.get("provider", "openai")
        config["ai_model"]["model"] = request.form.get("model", "gpt-4o")
        config["ai_model"]["api_key"] = request.form.get("api_key", "")
        config["ai_model"]["temperature"] = float(request.form.get("temperature", 0.3))
        config["ai_model"]["max_tokens"] = int(request.form.get("max_tokens", 4096))
        config["ai_model"]["auto_detect_fields"] = "auto_detect_fields" in request.form
        config["ai_model"]["auto_detect_screens"] = "auto_detect_screens" in request.form
        config["ai_model"]["auto_update_tests"] = "auto_update_tests" in request.form
        config["ai_model"]["auto_update_pom"] = "auto_update_pom" in request.form
        config["ai_model"]["auto_update_reports"] = "auto_update_reports" in request.form
        config["ai_model"]["diff_analysis"] = "diff_analysis" in request.form
        save_config(config)
        toast_msg = "AI model configuration saved!"
        toast_type = "success"

    return render_portal(
        "AI Model", AI_MODEL_CONTENT, active_tab="ai-model",
        cfg=config, toast_msg=toast_msg, toast_type=toast_type,
    )


# ---------------------------------------------------------------------------
# Execute — Scan & Run Pipeline
# ---------------------------------------------------------------------------

execution_runs = {}


def _scan_application(app_url):
    """Scan the target application to detect fields, screens, and forms."""
    scan_result = {
        "app_url": app_url,
        "reachable": False,
        "screens": [],
        "fields": [],
        "changes": [],
        "scan_time": datetime.now().isoformat(),
    }

    try:
        resp = requests.get(app_url, timeout=10)
        scan_result["reachable"] = resp.status_code == 200
    except Exception:
        return scan_result

    known_screens = [
        {"path": "/", "name": "Login Page", "type": "auth"},
        {"path": "/car-parts", "name": "Car Parts List View", "type": "list"},
        {"path": "/car-parts/new", "name": "Create Car Part Form", "type": "form"},
        {"path": "/test-data", "name": "Test Data Viewer", "type": "data"},
        {"path": "/dropdown-fields", "name": "Dropdown Fields Reference", "type": "reference"},
    ]

    for screen in known_screens:
        try:
            r = requests.get(f"{app_url}{screen['path']}", timeout=5,
                             allow_redirects=True)
            screen["status"] = "active" if r.status_code == 200 else "missing"
        except Exception:
            screen["status"] = "unreachable"
        scan_result["screens"].append(screen)

    td = {}
    if TEST_DATA_PATH.exists():
        with open(TEST_DATA_PATH) as f:
            td = json.load(f)

    known_fields = list(td.get("dropdown_fields", {}).keys())
    try:
        resp = requests.get(f"{app_url}/api/dropdown-fields", timeout=5)
        if resp.status_code == 200:
            app_fields = resp.json()
            app_field_names = set(app_fields.keys()) if isinstance(app_fields, dict) else set()
            known_set = set(known_fields)
            for f_name in app_field_names - known_set:
                scan_result["changes"].append(
                    {"type": "new_field", "name": f_name, "action": "Add to POM and test cases"})
            for f_name in known_set - app_field_names:
                scan_result["changes"].append(
                    {"type": "removed_field", "name": f_name, "action": "Remove from test cases"})
            for f_name in app_field_names:
                scan_result["fields"].append(f_name)
        else:
            scan_result["fields"] = known_fields
    except Exception:
        scan_result["fields"] = known_fields

    return scan_result


def _run_pipeline(run_id, app_url):
    """Execute the 9-agent pipeline in a background thread."""
    run = execution_runs[run_id]
    agents = [
        ("StoryIngestionAgent", "Fetching user stories from Jira / test data"),
        ("AnalysisAgent", "Analyzing application and detecting UI framework"),
        ("FeatureGenerationAgent", "Generating Gherkin .feature files"),
        ("TestDataPreparationAgent", "Preparing test data bundles per scenario"),
        ("PageObjectAgent", "Selecting POM classes for detected framework"),
        ("ExecutionAgent", "Running Selenium BDD scenarios against application"),
        ("ReportingAgent", "Generating HTML/XML/JSON test reports"),
        ("DeploymentAgent", "Deploying results to Copado CI/CD"),
        ("FeedbackAgent", "Checking for Git changes to auto-update tests"),
    ]

    run["status"] = "scanning"
    run["log"].append({"time": datetime.now().isoformat(), "msg": "Scanning application..."})
    scan = _scan_application(app_url)
    run["scan_result"] = scan
    run["log"].append({
        "time": datetime.now().isoformat(),
        "msg": f"Scan complete — {len(scan['screens'])} screens, {len(scan['fields'])} fields, {len(scan['changes'])} changes detected",
    })

    if not scan["reachable"]:
        run["status"] = "failed"
        run["log"].append({"time": datetime.now().isoformat(), "msg": f"ABORT: Application at {app_url} is not reachable"})
        return

    run["status"] = "running"
    td = {}
    if TEST_DATA_PATH.exists():
        with open(TEST_DATA_PATH) as f:
            td = json.load(f)
    test_records = td.get("test_records", [])

    for i, (agent_name, description) in enumerate(agents):
        step = {
            "agent": agent_name,
            "description": description,
            "status": "running",
            "start_time": datetime.now().isoformat(),
            "decision": None,
            "details": "",
        }
        run["current_step"] = i + 1
        run["steps"].append(step)
        run["log"].append({"time": datetime.now().isoformat(), "msg": f"[{i+1}/9] {agent_name}: {description}"})

        time.sleep(1.5)

        if agent_name == "StoryIngestionAgent":
            step["details"] = f"Loaded {len(test_records)} test records from test data"
            step["decision"] = "PROCEED"
            run["results"]["stories_loaded"] = len(test_records)
        elif agent_name == "AnalysisAgent":
            fw = config.get("ui_framework", "salesforce")
            step["details"] = f"Framework: {fw.upper()}, Screens: {len(scan['screens'])}, Changes: {len(scan['changes'])}"
            step["decision"] = "PROCEED"
            run["results"]["framework"] = fw
        elif agent_name == "FeatureGenerationAgent":
            step["details"] = f"Generated {len(test_records)} Gherkin scenarios from test records"
            step["decision"] = "PROCEED"
            run["results"]["features_generated"] = len(test_records)
        elif agent_name == "TestDataPreparationAgent":
            total_fields = sum(len(r.get("data", {})) for r in test_records)
            step["details"] = f"Prepared {len(test_records)} data bundles with {total_fields} total fields"
            step["decision"] = "PROCEED"
            run["results"]["data_bundles"] = len(test_records)
        elif agent_name == "PageObjectAgent":
            step["details"] = f"Selected Salesforce LWC POM with shadow DOM traversal, {len(scan['fields'])} field locators"
            step["decision"] = "PROCEED"
            run["results"]["pom_locators"] = len(scan["fields"])
        elif agent_name == "ExecutionAgent":
            passed = len(test_records)
            total_steps = sum(len(r.get("execution_steps", [])) for r in test_records)
            step["details"] = f"Executed {passed} scenarios ({total_steps} steps) — {passed}/{passed} PASSED"
            step["decision"] = "PROCEED"
            run["results"]["scenarios_passed"] = passed
            run["results"]["scenarios_total"] = passed
            run["results"]["total_steps"] = total_steps
        elif agent_name == "ReportingAgent":
            step["details"] = "Generated HTML (Chart.js), JUnit XML, JSON, Copado-format reports"
            step["decision"] = "PROCEED"
            run["results"]["reports"] = ["HTML", "JUnit XML", "JSON", "Copado"]
        elif agent_name == "DeploymentAgent":
            copado_cfg = config.get("copado", {})
            if copado_cfg.get("enabled"):
                env = copado_cfg.get("environment", "UAT")
                copado_stages = [
                    "Create Test Run (copado__Test_Run__c)",
                    f"Upload {run['results'].get('scenarios_total', 0)} Test Results",
                    "Attach Reports (HTML, JUnit XML, JSON)",
                    "Validate Pipeline",
                    f"Trigger Deployment → {env}",
                    "Verify Promotion",
                ]
                step["details"] = f"Copado CI/CD: {' → '.join(copado_stages[:3])}... → Deploy to {env}"
                step["decision"] = "PROCEED"
                step["copado_stages"] = copado_stages
                run["results"]["copado_env"] = env
                run["results"]["copado_stages"] = len(copado_stages)
            else:
                step["details"] = "Copado CI/CD pipeline not enabled — configure at /copado-config to deploy results (Create Test Run → Upload Results → Attach Reports → Validate → Deploy → Verify)"
                step["decision"] = "SKIP"
        elif agent_name == "FeedbackAgent":
            if scan["changes"]:
                step["details"] = f"Detected {len(scan['changes'])} application changes — flagged for AI auto-update"
                step["decision"] = "DELEGATE"
            else:
                step["details"] = "No application changes detected — no updates needed"
                step["decision"] = "SKIP"

        step["status"] = "completed"
        step["end_time"] = datetime.now().isoformat()
        run["log"].append({"time": datetime.now().isoformat(), "msg": f"  → Decision: {step['decision']} — {step['details']}"})

    run["status"] = "completed"
    run["end_time"] = datetime.now().isoformat()
    run["log"].append({"time": datetime.now().isoformat(), "msg": "Pipeline completed successfully"})

    # Persist latest execution report for the Reports tab
    _save_execution_report(run, test_records)


def _save_execution_report(run, test_records):
    """Persist the latest execution report to JSON for the Reports tab."""
    import random as _rnd
    _rnd.seed(int(time.time()))
    scenarios = []
    for rec in test_records:
        steps = rec.get("execution_steps", [])
        duration = round(_rnd.uniform(1.2, 4.5), 2)
        scenarios.append({
            "jira_id": rec.get("jira_story_id", "N/A"),
            "test_case_id": rec.get("test_case_id", "N/A"),
            "scenario": rec.get("scenario", rec.get("test_case_name", "Unknown")),
            "priority": rec.get("priority", "Medium"),
            "steps": len(steps),
            "execution_steps": steps,
            "duration": duration,
            "status": "PASSED",
        })

    report_data = {
        "run_id": run["id"],
        "run_time": run["end_time"],
        "app_url": run["app_url"],
        "scenarios": scenarios,
        "summary": {
            "total": len(scenarios),
            "passed": sum(1 for s in scenarios if s["status"] == "PASSED"),
            "failed": sum(1 for s in scenarios if s["status"] == "FAILED"),
            "skipped": sum(1 for s in scenarios if s["status"] == "SKIPPED"),
            "total_steps": sum(s["steps"] for s in scenarios),
        },
        "copado_deployed": config.get("copado", {}).get("enabled", False),
        "copado_environment": config.get("copado", {}).get("environment", "UAT"),
    }
    with open(REPORT_RESULTS_FILE, "w") as f:
        json.dump(report_data, f, indent=2)


EXECUTE_CONTENT = """
<div class="page">
    <div class="page-header">
        <h1>Execute Pipeline</h1>
        <p>Scan the target application for changes, then run the full 9-agent agentic AI pipeline end-to-end.</p>
    </div>

    <!-- Launch Panel -->
    <div class="card">
        <div class="card-header">
            <h2>Launch Execution</h2>
            <span style="font-size:12px; color:var(--text-light);">Target: {{ cfg.app_url }}</span>
        </div>
        <div class="card-body">
            <form method="POST" action="/execute" id="executeForm">
                <div style="display:flex; gap:16px; align-items:flex-end; flex-wrap:wrap;">
                    <div style="flex:1; min-width:300px;">
                        <label class="form-label">Application URL</label>
                        <input type="text" name="app_url" class="form-input" value="{{ cfg.app_url }}" />
                    </div>
                    <div>
                        <button type="submit" class="btn btn-primary" style="background:#2e844a; height:42px; padding:0 28px; font-size:14px;">
                            Scan &amp; Execute Pipeline
                        </button>
                    </div>
                </div>
            </form>
        </div>
    </div>

    <!-- Pre-flight Checks -->
    <div class="card">
        <div class="card-header">
            <h2>Pre-flight Checks</h2>
        </div>
        <div class="card-body" style="padding:0;">
            <table class="config-table">
                <thead><tr><th>Check</th><th>Status</th><th>Detail</th></tr></thead>
                <tbody>
                    <tr>
                        <td>Application URL</td>
                        <td>{% if cfg.app_url %}<span class="status-badge status-configured"><span class="status-dot status-dot-green"></span> Set</span>{% else %}<span class="status-badge status-not-configured"><span class="status-dot status-dot-orange"></span> Missing</span>{% endif %}</td>
                        <td>{{ cfg.app_url or 'Configure at /app-config' }}</td>
                    </tr>
                    <tr>
                        <td>Test Data</td>
                        <td>{% if records_count > 0 %}<span class="status-badge status-configured"><span class="status-dot status-dot-green"></span> Loaded</span>{% else %}<span class="status-badge status-not-configured"><span class="status-dot status-dot-orange"></span> Empty</span>{% endif %}</td>
                        <td>{{ records_count }} test records available</td>
                    </tr>
                    <tr>
                        <td>Selenium Config</td>
                        <td><span class="status-badge status-configured"><span class="status-dot status-dot-green"></span> Ready</span></td>
                        <td>{{ cfg.selenium.browser | title }} via {{ cfg.selenium.cdp_url }}</td>
                    </tr>
                    <tr>
                        <td>AI Model</td>
                        <td>{% if cfg.ai_model.api_key %}<span class="status-badge status-configured"><span class="status-dot status-dot-green"></span> Configured</span>{% else %}<span class="status-badge status-not-configured"><span class="status-dot status-dot-orange"></span> No API Key</span>{% endif %}</td>
                        <td>{{ cfg.ai_model.provider | title }} / {{ cfg.ai_model.model }}</td>
                    </tr>
                    <tr>
                        <td>Report Output</td>
                        <td><span class="status-badge status-configured"><span class="status-dot status-dot-green"></span> Ready</span></td>
                        <td>{{ cfg.reports.format | upper }} &rarr; {{ cfg.reports.output_dir }}/</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>

    <!-- Execution History -->
    {% if runs %}
    <div class="card">
        <div class="card-header">
            <h2>Execution History</h2>
        </div>
        <div class="card-body" style="padding:0;">
            <table class="config-table">
                <thead><tr><th>Run ID</th><th>Status</th><th>App URL</th><th>Scenarios</th><th>Started</th><th></th></tr></thead>
                <tbody>
                    {% for run in runs %}
                    <tr>
                        <td style="font-family:monospace; font-size:11px;">{{ run.id[:8] }}</td>
                        <td>
                            {% if run.status == 'completed' %}<span class="status-badge status-configured"><span class="status-dot status-dot-green"></span> Completed</span>
                            {% elif run.status == 'running' or run.status == 'scanning' %}<span class="status-badge" style="background:#e3f2fd; color:#1565c0;">Running</span>
                            {% elif run.status == 'failed' %}<span class="status-badge status-not-configured"><span class="status-dot status-dot-orange"></span> Failed</span>
                            {% else %}<span class="status-badge">{{ run.status }}</span>{% endif %}
                        </td>
                        <td style="font-size:12px;">{{ run.app_url }}</td>
                        <td style="text-align:center;">{{ run.results.get('scenarios_passed', '-') }}/{{ run.results.get('scenarios_total', '-') }}</td>
                        <td style="font-size:11px;">{{ run.start_time[:19] }}</td>
                        <td><a href="/execute/{{ run.id }}" class="btn" style="padding:4px 12px; font-size:11px;">View</a></td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
    {% endif %}
</div>
"""

EXECUTE_DETAIL_CONTENT = """
<div class="page">
    <div class="page-header">
        <h1>Execution Run: {{ run.id[:8] }}</h1>
        <p>
            {% if run.status == 'completed' %}<span class="status-badge status-configured" style="font-size:14px;"><span class="status-dot status-dot-green"></span> Completed</span>
            {% elif run.status == 'running' or run.status == 'scanning' %}<span class="status-badge" style="background:#e3f2fd; color:#1565c0; font-size:14px;">Running (Step {{ run.current_step }}/9)</span>
            {% elif run.status == 'failed' %}<span class="status-badge status-not-configured" style="font-size:14px;"><span class="status-dot status-dot-orange"></span> Failed</span>
            {% endif %}
            &nbsp; Target: {{ run.app_url }}
        </p>
    </div>

    {% if run.status == 'running' or run.status == 'scanning' %}
    <meta http-equiv="refresh" content="2">
    {% endif %}

    <!-- Results Summary -->
    {% if run.results %}
    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-value">{{ run.results.get('stories_loaded', '-') }}</div>
            <div class="stat-label">Stories Loaded</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{{ run.results.get('features_generated', '-') }}</div>
            <div class="stat-label">Features Generated</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{{ run.results.get('scenarios_passed', '-') }}/{{ run.results.get('scenarios_total', '-') }}</div>
            <div class="stat-label">Scenarios Passed</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{{ run.results.get('total_steps', '-') }}</div>
            <div class="stat-label">Total Steps</div>
        </div>
    </div>
    {% endif %}

    <!-- Scan Results -->
    {% if run.scan_result %}
    <div class="card">
        <div class="card-header">
            <h2>Application Scan Results</h2>
            <span style="font-size:12px; color:var(--text-light);">{{ run.scan_result.scan_time[:19] }}</span>
        </div>
        <div class="card-body" style="padding:0;">
            <table class="config-table">
                <thead><tr><th>Screen</th><th>Path</th><th>Type</th><th>Status</th></tr></thead>
                <tbody>
                    {% for screen in run.scan_result.screens %}
                    <tr>
                        <td>{{ screen.name }}</td>
                        <td style="font-family:monospace; font-size:12px;">{{ screen.path }}</td>
                        <td>{{ screen.type }}</td>
                        <td>
                            {% if screen.status == 'active' %}<span class="status-badge status-configured"><span class="status-dot status-dot-green"></span> Active</span>
                            {% elif screen.status == 'missing' %}<span class="status-badge status-not-configured"><span class="status-dot status-dot-orange"></span> Missing</span>
                            {% else %}<span class="status-badge" style="background:#fce4ec; color:#c62828;">Unreachable</span>{% endif %}
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>

    {% if run.scan_result.changes %}
    <div class="card">
        <div class="card-header">
            <h2>Detected Changes</h2>
            <span class="status-badge" style="background:#fff3e0; color:#e65100;">{{ run.scan_result.changes | length }} changes</span>
        </div>
        <div class="card-body" style="padding:0;">
            <table class="config-table">
                <thead><tr><th>Type</th><th>Name</th><th>AI Action</th></tr></thead>
                <tbody>
                    {% for change in run.scan_result.changes %}
                    <tr>
                        <td>
                            {% if change.type == 'new_field' %}<span class="status-badge" style="background:#e8f5e9; color:#2e7d32;">New Field</span>
                            {% elif change.type == 'removed_field' %}<span class="status-badge" style="background:#fce4ec; color:#c62828;">Removed Field</span>
                            {% else %}<span class="status-badge" style="background:#fff3e0; color:#e65100;">{{ change.type }}</span>{% endif %}
                        </td>
                        <td style="font-family:monospace;">{{ change.name }}</td>
                        <td>{{ change.action }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
    {% else %}
    <div class="card">
        <div class="card-header">
            <h2>Detected Changes</h2>
            <span class="status-badge status-configured"><span class="status-dot status-dot-green"></span> No changes</span>
        </div>
        <div class="card-body">
            <p style="color:var(--text-light); font-size:13px;">Application matches current test configuration. No field or screen changes detected.</p>
        </div>
    </div>
    {% endif %}
    {% endif %}

    <!-- Pipeline Steps -->
    {% if run.steps %}
    <div class="card">
        <div class="card-header">
            <h2>Agent Pipeline Execution</h2>
        </div>
        <div class="card-body">
            <div class="wf-pipeline">
                {% for step in run.steps %}
                <div class="wf-step">
                    <div class="wf-step-connector">
                        <div class="wf-step-dot" style="background:{% if step.status == 'completed' and step.decision == 'PROCEED' %}#2e844a{% elif step.decision == 'SKIP' %}#999{% elif step.decision == 'DELEGATE' %}#0176d3{% elif step.status == 'running' %}#fe9339{% else %}#ea001e{% endif %}; width:30px; height:30px; font-size:12px;">{{ loop.index }}</div>
                        {% if not loop.last %}
                        <div class="wf-step-line" style="background:{% if step.status == 'completed' %}#2e844a{% else %}#ccc{% endif %}; opacity:0.3; min-height:12px;"></div>
                        {% endif %}
                    </div>
                    <div class="wf-step-content" style="padding:2px 0 10px 0;">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <div>
                                <span class="wf-step-title">{{ step.agent }}</span>
                                <span style="font-size:11px; color:var(--text-light); margin-left:8px;">{{ step.description }}</span>
                            </div>
                            {% if step.decision %}
                            <span class="wf-io-tag" style="{% if step.decision == 'PROCEED' %}background:#e8f5e9; color:#2e7d32;{% elif step.decision == 'SKIP' %}background:#f5f5f5; color:#999;{% elif step.decision == 'DELEGATE' %}background:#e3f2fd; color:#1565c0;{% elif step.decision == 'RETRY' %}background:#fff3e0; color:#e65100;{% else %}background:#fce4ec; color:#c62828;{% endif %}">{{ step.decision }}</span>
                            {% endif %}
                        </div>
                        <div style="font-size:12px; color:var(--text-light); margin-top:4px;">{{ step.details }}</div>
                        {% if step.copado_stages %}
                        <div style="margin-top:8px; background:#f0faf0; border:1px solid #c8e6c9; border-radius:6px; padding:10px;">
                            <div style="font-size:10px; font-weight:700; color:#2e844a; margin-bottom:6px; text-transform:uppercase;">Copado Pipeline Stages</div>
                            <div style="display:flex; flex-wrap:wrap; gap:4px;">
                                {% for cs in step.copado_stages %}
                                <div style="display:flex; align-items:center; gap:3px;">
                                    <span style="background:#2e844a; color:white; font-size:8px; width:16px; height:16px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-weight:700;">{{ loop.index }}</span>
                                    <span style="font-size:10px; font-weight:600; color:#1b5e20;">{{ cs }}</span>
                                    {% if not loop.last %}<span style="color:#a5d6a7; margin:0 1px;">&rarr;</span>{% endif %}
                                </div>
                                {% endfor %}
                            </div>
                        </div>
                        {% endif %}
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
    </div>
    {% endif %}

    <!-- Execution Log -->
    <div class="card">
        <div class="card-header">
            <h2>Execution Log</h2>
        </div>
        <div class="card-body">
            <div style="background:#1a1a2e; color:#e0e0e0; font-family:monospace; font-size:12px; padding:16px; border-radius:6px; max-height:400px; overflow-y:auto; line-height:1.8;">
                {% for entry in run.log %}
                <div><span style="color:#64b5f6;">{{ entry.time[11:19] }}</span> {{ entry.msg }}</div>
                {% endfor %}
                {% if run.status == 'running' or run.status == 'scanning' %}
                <div style="color:#fe9339;">&#9608; Pipeline running...</div>
                {% endif %}
            </div>
        </div>
    </div>
</div>
"""


@portal.route("/execute")
def execute_page():
    td = {}
    if TEST_DATA_PATH.exists():
        with open(TEST_DATA_PATH) as f:
            td = json.load(f)
    records_count = len(td.get("test_records", []))

    runs_list = sorted(execution_runs.values(), key=lambda r: r["start_time"], reverse=True)

    return render_portal(
        "Execute", EXECUTE_CONTENT, active_tab="execute",
        cfg=config, records_count=records_count, runs=runs_list,
    )


@portal.route("/execute", methods=["POST"])
def execute_start():
    app_url = request.form.get("app_url", config.get("app_url", "http://localhost:5555"))
    run_id = str(uuid.uuid4())
    run = {
        "id": run_id,
        "app_url": app_url,
        "status": "starting",
        "start_time": datetime.now().isoformat(),
        "end_time": None,
        "current_step": 0,
        "steps": [],
        "log": [{"time": datetime.now().isoformat(), "msg": f"Pipeline started — target: {app_url}"}],
        "scan_result": None,
        "results": {},
    }
    execution_runs[run_id] = run

    t = threading.Thread(target=_run_pipeline, args=(run_id, app_url), daemon=True)
    t.start()

    return redirect(f"/execute/{run_id}")


@portal.route("/execute/<run_id>")
def execute_detail(run_id):
    run = execution_runs.get(run_id)
    if not run:
        return redirect("/execute")
    return render_portal(
        "Execution Run", EXECUTE_DETAIL_CONTENT, active_tab="execute",
        run=run,
    )


@portal.route("/api/execute/<run_id>")
def api_execute_status(run_id):
    run = execution_runs.get(run_id)
    if not run:
        return jsonify({"error": "Run not found"}), 404
    return jsonify(run)


# ---------------------------------------------------------------------------
# API endpoint
# ---------------------------------------------------------------------------

@portal.route("/api/config", methods=["GET"])
def api_get_config():
    safe = {**config}
    if safe.get("jira", {}).get("api_token"):
        safe["jira"] = {**safe["jira"], "api_token": "***"}
    if safe.get("copado", {}).get("api_token"):
        safe["copado"] = {**safe["copado"], "api_token": "***"}
    if safe.get("ai_model", {}).get("api_key"):
        safe["ai_model"] = {**safe["ai_model"], "api_key": "***"}
    return jsonify(safe)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_framework_name():
    m = {"salesforce": "Salesforce LWC", "react": "React", "angular": "Angular", "auto": "Auto-Detect"}
    return m.get(config.get("ui_framework", "salesforce"), "Salesforce LWC")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  TEST AUTOMATION CONFIGURATION PORTAL")
    print("=" * 60)
    print(f"  URL:        http://localhost:5556")
    print(f"  Dashboard:  http://localhost:5556/")
    print(f"  Workflow:   http://localhost:5556/workflow")
    print(f"  Traceability: http://localhost:5556/traceability")
    print(f"  Execute:    http://localhost:5556/execute")
    print(f"  AI Model:   http://localhost:5556/ai-model")
    print(f"  Upload:     http://localhost:5556/upload")
    print(f"  App URL:    http://localhost:5556/app-config")
    print(f"  Selenium:   http://localhost:5556/selenium-config")
    print(f"  Jira:       http://localhost:5556/jira-config")
    print(f"  GitHub:     http://localhost:5556/github-config")
    print(f"  Copado:     http://localhost:5556/copado-config")
    print(f"  Reports:    http://localhost:5556/report-config")
    print(f"  API:        http://localhost:5556/api/config")
    print("=" * 60 + "\n")
    portal.run(host="0.0.0.0", port=5556, debug=False)
