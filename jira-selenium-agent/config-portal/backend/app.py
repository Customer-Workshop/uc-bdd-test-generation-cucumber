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
        "scenarios_passed": 16,
        "scenarios_total": 16,
        "steps": 88,
        "duration": "18.2s",
        "agents": [
            {"name": "StoryIngestionAgent", "decision": "PROCEED", "result": "Loaded 6 test records"},
            {"name": "AnalysisAgent", "decision": "PROCEED", "result": "Framework: SALESFORCE, 5 screens"},
            {"name": "FeatureGenerationAgent", "decision": "PROCEED", "result": "Generated 6 Gherkin + 10 API scenarios"},
            {"name": "TestDataPreparationAgent", "decision": "PROCEED", "result": "6 data bundles, 65 fields"},
            {"name": "PageObjectAgent", "decision": "PROCEED", "result": "SelectorsHub scanned 12 fields"},
            {"name": "ExecutionAgent", "decision": "PROCEED", "result": "6/6 UI scenarios passed, 58 steps"},
            {"name": "APITestingAgent", "decision": "PROCEED", "result": "10/10 API scenarios passed, 30 steps"},
            {"name": "ReportingAgent", "decision": "PROCEED", "result": "HTML/XML/JSON reports (UI + API)"},
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


# ─── Features API ─────────────────────────────────────────────────────────────

FEATURES_DIR = BASE_DIR.parent.parent / "features"


@app.route('/api/features', methods=['GET'])
def list_features():
    """List all generated feature files, grouped by app and category."""
    result = {}
    if FEATURES_DIR.exists():
        for app_dir in sorted(FEATURES_DIR.iterdir()):
            if app_dir.is_dir():
                app_name = app_dir.name
                result[app_name] = {}
                for cat_dir in sorted(app_dir.iterdir()):
                    if cat_dir.is_dir():
                        files = sorted([
                            {"name": f.name, "path": str(f.relative_to(FEATURES_DIR))}
                            for f in cat_dir.glob("*.feature")
                        ], key=lambda x: x["name"])
                        if files:
                            result[app_name][cat_dir.name] = files
    return jsonify(result)


@app.route('/api/features/<path:feature_path>', methods=['GET'])
def get_feature_content(feature_path):
    """Read the content of a specific feature file."""
    fp = FEATURES_DIR / feature_path
    if fp.exists() and fp.suffix == '.feature':
        return jsonify({"path": feature_path, "content": fp.read_text(encoding="utf-8")})
    return jsonify({"error": "Feature file not found"}), 404


# ─── API Testing Configuration ────────────────────────────────────────────────

REPORTS_DIR = BASE_DIR.parent.parent / "reports"


@app.route('/api/api-testing-config', methods=['GET'])
def get_api_testing_config():
    """Return API testing configuration."""
    return jsonify({
        "enabled": True,
        "base_url": config_data.get("selenium", {}).get("base_url", "http://localhost:5555"),
        "timeout_seconds": 10,
        "retry_count": 1,
        "endpoints": [
            {"method": "GET", "path": "/api/car-parts", "description": "List all car parts"},
            {"method": "GET", "path": "/api/car-parts/<id>", "description": "Get car part by ID"},
            {"method": "POST", "path": "/api/car-parts", "description": "Create new car part"},
            {"method": "PUT", "path": "/api/car-parts/<id>", "description": "Update car part"},
            {"method": "DELETE", "path": "/api/car-parts/<id>", "description": "Delete car part"},
            {"method": "GET", "path": "/api/dropdown-fields", "description": "Get dropdown metadata"},
            {"method": "GET", "path": "/api/sub-categories/<cat>", "description": "Get sub-categories"},
            {"method": "GET", "path": "/api/test-data", "description": "Get test data JSON"},
        ],
        "test_scenarios": [
            {"id": "CAR-1011", "name": "API Health Check", "type": "health", "priority": "high"},
            {"id": "CAR-1012", "name": "List All Car Parts", "type": "read", "priority": "high"},
            {"id": "CAR-1013", "name": "Get Car Part by ID", "type": "read", "priority": "high"},
            {"id": "CAR-1014", "name": "Create Car Part", "type": "create", "priority": "high"},
            {"id": "CAR-1015", "name": "Update Car Part", "type": "update", "priority": "high"},
            {"id": "CAR-1016", "name": "Delete Car Part", "type": "delete", "priority": "medium"},
            {"id": "CAR-1017", "name": "Dropdown Fields Metadata", "type": "read", "priority": "medium"},
            {"id": "CAR-1018", "name": "Dependent Sub-Categories", "type": "read", "priority": "medium"},
            {"id": "CAR-1019", "name": "Nonexistent Part 404", "type": "validation", "priority": "medium"},
            {"id": "CAR-1020", "name": "Invalid Create 400", "type": "validation", "priority": "high"},
        ],
    })


@app.route('/api/api-testing-config', methods=['POST'])
def save_api_testing_config():
    """Save API testing configuration."""
    data = request.get_json()
    if data:
        config_data["api_testing"] = data
        save_config(config_data)
    return jsonify({"status": "saved"})


@app.route('/api/api-test-report', methods=['GET'])
def get_api_test_report():
    """Return the latest API test report."""
    latest_path = REPORTS_DIR / "latest_api_report.json"
    if latest_path.exists():
        with open(latest_path, encoding="utf-8") as f:
            return jsonify(json.load(f))
    return jsonify({"error": "No API test report found. Run the pipeline first."}), 404


@app.route('/api/run-api-tests', methods=['POST'])
def run_api_tests():
    """Execute API tests and return results."""
    import sys
    sys.path.insert(0, str(BASE_DIR.parent.parent))
    from runners.api_test_runner import APITestRunner

    base_url = config_data.get("selenium", {}).get("base_url", "http://localhost:5555")
    runner = APITestRunner(base_url=base_url)
    report = runner.run()

    return jsonify({
        "run_id": report.run_id,
        "total_scenarios": report.total_scenarios,
        "passed_scenarios": report.passed_scenarios,
        "failed_scenarios": report.failed_scenarios,
        "total_steps": report.total_steps,
        "passed_steps": report.passed_steps,
        "duration_seconds": round(report.duration_seconds, 2),
    })


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
