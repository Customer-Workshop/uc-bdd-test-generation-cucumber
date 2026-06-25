"""
Flask server for the React-based Config Portal.
Serves the React build (Material UI) and exposes REST API endpoints
for automation configuration management.
Runs on port 5556.
"""
import json
import os
from pathlib import Path
from flask import Flask, jsonify, request, send_from_directory

BASE_DIR = Path(__file__).parent
REACT_BUILD_DIR = BASE_DIR.parent / "frontend" / "build"
CONFIG_FILE = BASE_DIR.parent.parent / "config" / "automation_config.json"

app = Flask(__name__, static_folder=str(REACT_BUILD_DIR / "static"))

# Default config
default_config = {
    "app_url": "http://localhost:5555",
    "ui_framework": "salesforce",
    "selenium": {"browser": "chrome", "cdp_url": "http://localhost:29229", "headless": False, "timeout": 30},
    "jira": {"server_url": "", "username": "", "project_key": "CAR", "auto_fetch": False},
    "github": {"repo_url": "", "branch": "main", "workflow_file": ".github/workflows/bdd-test-agent.yml"},
    "copado": {"enabled": False, "instance_url": "", "pipeline_id": "", "target_env": "UAT"},
    "ai_model": {"provider": "OpenAI", "model": "GPT-4o", "temperature": 0.3, "max_tokens": 4096},
    "selectorshub": {"enabled": True, "auto_scan": True, "shadow_dom": True, "scan_depth": 5},
    "mcp_servers": {"enabled": False, "transport": "stdio"},
    "reports": {"format": "html", "output_dir": "./reports"}
}


def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            return json.load(f)
    return default_config.copy()


def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)


# ─── Config API ───────────────────────────────────────────────────────────────

@app.route('/api/config', methods=['GET'])
def get_config():
    return jsonify(load_config())


@app.route('/api/config', methods=['PUT'])
def update_config():
    data = request.get_json()
    config = load_config()
    config.update(data)
    save_config(config)
    return jsonify(config)


@app.route('/api/config/<section>', methods=['GET'])
def get_config_section(section):
    config = load_config()
    if section in config:
        return jsonify(config[section])
    return jsonify({"error": "Section not found"}), 404


@app.route('/api/config/<section>', methods=['PUT'])
def update_config_section(section):
    data = request.get_json()
    config = load_config()
    config[section] = data
    save_config(config)
    return jsonify(config[section])


@app.route('/api/execute', methods=['POST'])
def execute_pipeline():
    """Simulate pipeline execution."""
    return jsonify({
        "run_id": "RUN-001",
        "status": "completed",
        "scenarios_passed": 6,
        "scenarios_total": 6,
        "steps": 58,
        "duration": "17.9s",
        "agents": [
            {"name": "StoryIngestionAgent", "decision": "PROCEED", "result": "Loaded 6 test records"},
            {"name": "AnalysisAgent", "decision": "PROCEED", "result": "Framework: SALESFORCE, 5 screens"},
            {"name": "FeatureGenerationAgent", "decision": "PROCEED", "result": "Generated 6 Gherkin scenarios"},
            {"name": "TestDataPreparationAgent", "decision": "PROCEED", "result": "6 data bundles, 65 fields"},
            {"name": "PageObjectAgent", "decision": "PROCEED", "result": "SelectorsHub scanned 12 fields"},
            {"name": "ExecutionAgent", "decision": "PROCEED", "result": "6/6 scenarios passed, 58 steps"},
            {"name": "ReportingAgent", "decision": "PROCEED", "result": "HTML/XML/JSON reports generated"},
            {"name": "DeploymentAgent", "decision": "SKIP", "result": "Copado not configured"},
            {"name": "FeedbackAgent", "decision": "SKIP", "result": "No changes detected"},
        ]
    })


@app.route('/api/test-data', methods=['GET'])
def get_test_data():
    td_path = BASE_DIR.parent.parent / "test-data" / "car_parts_test_data.json"
    if td_path.exists():
        with open(td_path) as f:
            return jsonify(json.load(f))
    return jsonify([])


@app.route('/api/test-data', methods=['POST'])
def upload_test_data():
    data = request.get_json()
    td_path = BASE_DIR.parent.parent / "test-data" / "car_parts_test_data.json"
    with open(td_path, 'w') as f:
        json.dump(data, f, indent=2)
    return jsonify({"message": "Test data uploaded", "records": len(data)})


# ─── Serve React App ──────────────────────────────────────────────────────────

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(str(REACT_BUILD_DIR / "static"), filename)


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_react(path):
    if path.startswith('api/'):
        return jsonify({"error": "Not found"}), 404
    file_path = REACT_BUILD_DIR / path
    if path and file_path.exists() and file_path.is_file():
        return send_from_directory(str(REACT_BUILD_DIR), path)
    return send_from_directory(str(REACT_BUILD_DIR), 'index.html')


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("  Automation Configuration Portal - React + Material UI")
    print("=" * 60)
    print(f"\n  React Build:  {REACT_BUILD_DIR}")
    print(f"  Config File:  {CONFIG_FILE}")
    print(f"  UI:           http://localhost:5556/")
    print(f"  API:          http://localhost:5556/api/")
    print("\n" + "=" * 60 + "\n")
    app.run(host='0.0.0.0', port=5556, debug=False)
