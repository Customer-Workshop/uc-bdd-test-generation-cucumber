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
"""

import json
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, redirect, render_template_string, request, url_for
from werkzeug.utils import secure_filename

portal = Flask(__name__)

# Paths
BASE_DIR = Path(__file__).parent
TEST_DATA_PATH = BASE_DIR / "car_parts_test_data.json"
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)
CONFIG_FILE = BASE_DIR / "automation_config.json"

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
            <a href="/upload" class="portal-nav-item {{ 'active' if active_tab == 'upload' else '' }}">Upload Test Data</a>
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
            <a href="/upload" class="btn btn-primary">Upload Test Data</a>
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
</div>
"""


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

    return render_portal(
        "Report Config", REPORT_CONFIG_CONTENT, active_tab="reports",
        cfg=config, toast_msg=toast_msg, toast_type=toast_type,
    )


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
