# Jira-Selenium Agentic AI Framework

BDD test automation framework powered by 9 autonomous AI agents. Connects to Jira, generates Gherkin feature files, executes Selenium tests against any UI (Salesforce LWC, React, Angular), and deploys results to Copado CI/CD.

## Architecture

```
                         Agentic AI Pipeline (9 Agents)
  +------------------+------------------+------------------+
  | 1. StoryIngest   | 2. Analysis      | 3. FeatureGen    |
  | Jira API fetch   | Framework detect | Gherkin .feature |
  | parse criteria   | complexity class | Given/When/Then  |
  +------------------+------------------+------------------+
  | 4. TestDataPrep  | 5. PageObject    | 6. Execution     |
  | Bundle per story | POM generation   | Selenium WebDrvr |
  | dropdown values  | LWC/React/Ng     | step mapping     |
  +------------------+------------------+------------------+
  | 7. Reporting     | 8. Deployment    | 9. Feedback      |
  | Chart.js + Jira  | Copado CI/CD     | Git diff + LLM   |
  | HTML/XML/JSON    | Test_Run records | auto-update tests|
  +------------------+------------------+------------------+
```

Each agent follows the `decide() -> act() -> report()` lifecycle defined in `BaseAgent`.

## Two Applications

| App | Port | Purpose |
|-----|------|---------|
| **Mock Salesforce Lightning UI** | `5555` | Car Parts CRUD application (the system under test) |
| **Automation Configuration Portal** | `5556` | Framework config, workflow visualization, AI model settings |

### Mock Salesforce App (port 5555)

- Login page (`admin@carparts.demo` / `demo1234`)
- Car Parts list view with search and filters
- Create/Edit forms with 12 dropdown fields and dependent picklists (Part Category -> Sub-Category)
- Record detail page, delete modal, toast notifications
- Test Data page (`/test-data`) showing Selenium execution data
- Dropdown Fields page (`/dropdown-fields`) showing all 12 picklist fields with values

### Configuration Portal (port 5556)

| Page | Route | Description |
|------|-------|-------------|
| Dashboard | `/` | Integration status, quick actions, full config summary |
| Workflow | `/workflow` | Visual 9-step agent pipeline with Copado CI/CD stages |
| Traceability | `/traceability` | Jira Story → Test Case → Steps → Test Data matrix |
| Execute | `/execute` | Scan app for changes, run full 9-agent pipeline live |
| AI Model | `/ai-model` | LLM provider, model, API key, 6 auto-detection toggles |
| Upload | `/upload` | Upload JSON test data, shows file path on disk |
| App URL | `/app-config` | Target application URL + UI framework selector |
| Selenium | `/selenium-config` | Browser, CDP URL, timeouts, headless, screenshots |
| Jira | `/jira-config` | Server URL, credentials, project key, status filter |
| GitHub | `/github-config` | Repo URL, branch, workflow file, auto-trigger |
| Copado | `/copado-config` | Instance URL, API token, pipeline ID, environment |
| Reports | `/report-config` | Inline HTML report with Chart.js charts + Copado deploy status |
| SelectorsHub | `/selectorshub-config` | Auto-scan settings, shadow DOM, XPath, selector priority |
| MCP Servers | `/mcp-servers` | Enable/configure 5 MCP servers (Jira, Selenium, Copado, GitHub, SelectorsHub) |
| Flow Diagram | `/flow-diagram` | SVG architecture diagram with agent pipeline, data flow, MCP comparison |
| API | `/api/config` | JSON endpoint for current config (tokens masked) |

## Quick Start (Local)

### Prerequisites

- Python 3.10+
- Google Chrome (for Selenium)
- Git

### 1. Clone and install dependencies

```bash
git clone https://github.com/Cognition-Partner-Workshops/uc-bdd-test-generation-cucumber.git
cd uc-bdd-test-generation-cucumber/jira-selenium-agent
pip install -r requirements.txt
pip install flask werkzeug
```

### 2. Start the Mock Salesforce App

```bash
python sample-automation/mock_salesforce_app.py
```

This starts the Car Parts application at **http://localhost:5555**

Login: `admin@carparts.demo` / `demo1234`

### 3. Start the Configuration Portal

Open a second terminal:

```bash
python sample-automation/config_portal.py
```

This starts the configuration portal at **http://localhost:5556**

### 4. Run the Selenium E2E Tests

Open a third terminal:

```bash
python sample-automation/car_parts_runner.py
```

Runs 11 BDD scenarios (142 steps) against the mock Salesforce app. Generates reports in `test-reports/`.

### 5. Run the Agentic Orchestrator

```bash
python agentic_orchestrator.py --mode car-parts --ui-framework salesforce
```

Runs the full 9-agent pipeline: ingest stories -> analyze -> generate features -> prepare data -> select POM -> execute tests -> generate reports -> deploy to Copado -> feedback loop.

## Agent Modes

```bash
# Demo mode (no Jira needed, uses sample stories)
python agent.py --mode demo

# Fetch stories from Jira
python agent.py --mode jira --status "To Do"

# Fetch specific stories
python agent.py --mode jira --stories PROJ-101 PROJ-102

# Run Selenium tests with POM
python agent.py --mode selenium

# Watch Git for story-key commits, auto-update features via LLM
python agent.py --mode watcher

# Listen for GitHub webhook push events
python agent.py --mode webhook

# Process a single commit SHA
python agent.py --mode commit --sha abc1234

# Full agentic pipeline
python agentic_orchestrator.py --mode car-parts --ui-framework salesforce
```

## Configuration

### Environment Variables (.env)

Copy `.env.example` to `.env` and fill in the values:

```bash
cp .env.example .env
```

| Variable | Description | Required |
|----------|-------------|----------|
| `JIRA_SERVER_URL` | Jira Cloud/Server URL | For Jira mode |
| `JIRA_USERNAME` | Jira email/username | For Jira mode |
| `JIRA_API_TOKEN` | Jira API token | For Jira mode |
| `JIRA_PROJECT_KEY` | Project key (e.g. CAR) | For Jira mode |
| `LLM_API_KEY` | OpenAI/Anthropic/Google API key | For AI features |
| `LLM_MODEL` | Model name (e.g. gpt-4o) | For AI features |
| `COPADO_INSTANCE_URL` | Salesforce org URL | For Copado deploy |
| `COPADO_API_TOKEN` | Copado session/OAuth token | For Copado deploy |
| `COPADO_PIPELINE_ID` | Pipeline record ID | For Copado deploy |
| `APP_BASE_URL` | Target application URL | Default: localhost:5555 |

### Portal Configuration (automation_config.json)

All settings from the Configuration Portal are persisted to `sample-automation/automation_config.json`. This file is auto-created on first portal run. Settings can also be configured via the portal UI at `http://localhost:5556`.

## Multi-UI Framework Support

The framework auto-detects and supports three UI frameworks:

| Framework | POM Class | Selector Strategy |
|-----------|-----------|-------------------|
| Salesforce LWC | `SalesforcePage` | Shadow DOM traversal, `lightning-input` by label |
| React | `ReactPage` | `data-testid` attributes, component hierarchy |
| Angular | `AngularPage` | `formControlName`, `ng-model`, Angular Material |

Detection is automatic via `UIAgent` which checks for `$A` (Aura), `lightning-app` (LWC), `_reactRootContainer` (React), or `app-root` (Angular).

## Test Data

### Default Test Data

6 test scenarios pre-loaded in `sample-automation/car_parts_test_data.json`:

| Scenario | Jira ID | Fields |
|----------|---------|--------|
| Create Engine Component (Turbocharger) | CAR-1001 | 17 fields |
| Create Braking System (Brake Kit) | CAR-1002 | 16 fields |
| Create Suspension (Coilover Kit) | CAR-1003 | 16 fields |
| Create Electrical (LED Headlight) | CAR-1004 | 16 fields |
| Edit Existing Car Part | CAR-1005 | 4 fields |
| Delete Car Part | CAR-1006 | 1 field |

### 12 Dropdown Fields

Part Category (12), Part Sub-Category (42 dependent), Manufacturer (23), Condition (6), Vehicle Make (21), Availability (7), Year Range, Warehouse (6), Quality Grade (6), Shipping Class (6), Warranty Type (7), Currency (10) -- **153+ total picklist values**.

### Custom Test Data

Upload your own JSON via the portal at `http://localhost:5556/upload` or place a file at:

```
jira-selenium-agent/sample-automation/car_parts_test_data.json
```

Expected format:

```json
{
  "test_records": [
    {
      "scenario": "Create Engine Component",
      "data": {
        "Part Name": "Turbocharger Assembly",
        "Part Category": "Engine Components",
        "Part Sub-Category": "Turbocharger",
        "Manufacturer": "BorgWarner"
      }
    }
  ]
}
```

## Reports

### Inline Report on Portal (Reports Tab)

When report format is set to **HTML**, the Reports page at `/report-config` displays the full test execution report inline:

- **KPI Cards**: Total Scenarios, Passed, Failed, Skipped, Pass Rate, Total Steps
- **Chart.js Charts**: Pie (pass/fail), Bar (duration per Jira ID), Doughnut (pass rate), Polar Area (steps per scenario)
- **Scenario Results Table**: Jira ID, Test Case, Scenario, Priority, Steps, Duration, Status
- **Execution Steps Detail**: Numbered step pipeline per scenario

The report **auto-updates** every time you run the pipeline from the Execute tab — no manual refresh needed.

### Copado Report Deployment

When Copado is configured and enabled (`/copado-config`), the same report is:
- Attached to `copado__Test_Run__c` as HTML Dashboard + JUnit XML + JSON
- Viewable in Copado after deployment
- Status shown on the Reports tab (Deployed / Ready to Deploy / Not Configured)

### Generated Report Files

Also output to `test-reports/` directory:

- **HTML Dashboard** (`car_parts_e2e_report.html`) -- Chart.js pie/bar/doughnut/polar charts with Jira ID traceability
- **JUnit XML** (`car_parts_e2e_report.xml`) -- CI integration
- **JSON** (`car_parts_e2e_report.json`) -- Programmatic access
- **Text Summary** (`car_parts_e2e_report.txt`) -- Console-friendly
- **Copado Format** (`car_parts_copado_results.json`) -- Copado CI/CD integration

## AI Auto-Update Flow

When the application changes (new fields, new screens, modified forms), the AI model automatically:

1. **Detects changes** -- Scans UI diff for added/modified/removed elements
2. **Updates POM** -- Adds new locators and action methods to Page Object classes
3. **Modifies tests** -- Updates Gherkin feature files and test data with new scenarios
4. **Reflects in reports** -- Execution reports include all new/modified test cases

Configure the AI model at `http://localhost:5556/ai-model`.

## Execute Pipeline

The Execute tab (`/execute`) provides a one-click end-to-end flow:

1. **Scans the target application** for field/screen changes
2. **Runs all 9 agents** in sequence with live progress tracking
3. **Persists results** to `latest_execution_report.json` — automatically reflected on the Reports tab
4. **Deploys to Copado** if enabled (6-stage pipeline: Create Test Run → Upload Results → Attach Reports → Validate Pipeline → Trigger Deployment → Verify Promotion)

Re-running the pipeline always generates fresh report data.

## Copado CI/CD Pipeline

The DeploymentAgent (Step 8) executes a 6-stage Copado promotion flow:

| Stage | Copado Object | Action |
|-------|---------------|--------|
| 1. Create Test Run | `copado__Test_Run__c` | Create record with run metadata |
| 2. Upload Results | `copado__Test_Result__c` | One record per scenario (pass/fail/duration) |
| 3. Attach Reports | `ContentDocument` | Upload HTML, JUnit XML, JSON as attachments |
| 4. Validate Pipeline | `copado__Pipeline__c` | Check pipeline and environment readiness |
| 5. Trigger Deployment | `copado__Deployment__c` | Trigger promotion to target environment |
| 6. Verify Promotion | `copado__Deployment__c` | Poll deployment until complete |

Environment promotion path: **DEV → SIT → UAT → STAGING → PRODUCTION**

Configure at `/copado-config`. The pipeline stages are visible on both the Workflow page and during Execute runs.

## SelectorsHub Integration

[SelectorsHub](https://selectorshub.com/) is integrated into the **PageObjectAgent (Step 5)** to auto-scan target applications and generate optimal selectors for POM classes.

**How it works:**
1. **Scan** — Crawl target app pages via Selenium/CDP
2. **Discover** — Find all interactive elements (inputs, buttons, dropdowns, links)
3. **Generate** — Produce multiple selector types per element (CSS, XPath, shadow-CSS, relative XPath)
4. **Inject** — Feed selectors into POM classes for test execution

**Supported selector types:**

| Type | Example | Use Case |
|------|---------|----------|
| CSS | `lightning-input[data-field="Part_Name__c"]` | Default, fastest |
| Shadow CSS | `lightning-input >>> input.slds-input` | Salesforce LWC shadow DOM |
| XPath | `//lightning-input[@data-field]//input` | Flexible fallback |
| data-testid | `[data-testid="part-name-input"]` | React best practice |
| formControlName | `[formControlName="partName"]` | Angular Reactive Forms |

Configure at `/selectorshub-config`. Settings: auto-scan, shadow DOM support, iFrame support, scan depth, selector priority order.

## MCP Server Architecture

The framework supports optional **MCP (Model Context Protocol)** servers that expose each integration as tools for LLM hosts (Claude Desktop, GPT, Cursor).

| MCP Server | Port | Tools |
|------------|------|-------|
| Jira | 3001 | `search_stories`, `get_story`, `update_status`, `get_acceptance_criteria` |
| Selenium | 3002 | `run_scenario`, `click_element`, `fill_form`, `screenshot`, `wait_for_element` |
| Copado | 3003 | `create_test_run`, `upload_results`, `attach_reports`, `trigger_deployment` |
| GitHub | 3004 | `list_commits`, `get_diff`, `create_pr`, `trigger_workflow` |
| SelectorsHub | 3005 | `scan_page`, `get_selectors`, `generate_pom`, `scan_shadow_dom` |

**Default architecture** uses direct API calls from agents (no MCP overhead). Enable MCP at `/mcp-servers` when you need these tools callable by external LLM hosts.

**MCP config for Claude Desktop** (`mcp.json`):
```json
{
  "mcpServers": {
    "jira-bdd": { "command": "python", "args": ["-m", "mcp_servers.jira_server"] },
    "selenium-bdd": { "command": "python", "args": ["-m", "mcp_servers.selenium_server"] },
    "copado-bdd": { "command": "python", "args": ["-m", "mcp_servers.copado_server"] },
    "selectorshub-bdd": { "command": "python", "args": ["-m", "mcp_servers.selectorshub_server"] }
  }
}
```

## Flow Diagram

Visual architecture diagram available at `/flow-diagram` showing:
- 7 external systems (Jira, GitHub, Salesforce UI, LLM, Copado, Selenium, SelectorsHub)
- AgenticOrchestrator with `decide() → act() → report()` lifecycle
- 9-agent pipeline layout with I/O labels
- Copado 6-stage pipeline detail
- Environment promotion path (DEV → SIT → UAT → STAGING → PRODUCTION)
- Data flow (Jira Stories → .feature → Test Data → POM → Results → Reports)
- MCP server architecture comparison
- Agent communication sequence table

## Project Structure

```
jira-selenium-agent/
  agent.py                    # CLI orchestrator (6 modes)
  agentic_orchestrator.py     # 9-agent pipeline with BaseAgent
  jira_client.py              # Jira REST API client
  gherkin_generator.py        # User story -> Gherkin .feature
  selenium_runner.py          # Selenium WebDriver wrapper
  page_object_model.py        # Base POM framework
  ui_framework_pages.py       # SF LWC / React / Angular pages
  ui_agent.py                 # Auto-detect framework + step mapping
  test_data_agent.py          # Test data bundling per story
  report_generator.py         # Chart.js HTML + JUnit XML + JSON
  copado_deployer.py          # Copado CI/CD deployment
  git_commit_watcher.py       # Git poll/webhook for story commits
  llm_feature_updater.py      # LLM-based .feature auto-update
  config.py                   # Environment config loader
  requirements.txt            # Python dependencies
  .env.example                # Environment variable template
  AGENTIC_AI_FLOW.md          # Detailed agent pipeline documentation
  sample-automation/
    mock_salesforce_app.py    # Mock SF Lightning UI (port 5555)
    config_portal.py          # Config portal (port 5556)
    car_parts_runner.py       # E2E test runner
    car_parts_page_objects.py # Car Parts POM classes
    car_parts_e2e.feature     # Gherkin feature file (11 scenarios)
    car_parts_test_data.json  # Test data (6 scenarios, 12 dropdowns)
    latest_execution_report.json  # Persisted report from last pipeline run
    automation_config.json    # Portal config (auto-generated)
    selenium_e2e_runner.py    # Selenium execution engine
```

## CI/CD

GitHub Actions workflow at `.github/workflows/bdd-test-agent.yml`:

- Triggers on push to `main` or PR
- Installs Python dependencies + Chrome
- Runs the agentic orchestrator in `car-parts` mode
- Uploads test reports as artifacts
- Deploys to Copado if configured

## License

Part of the BDD Test Generation framework.
