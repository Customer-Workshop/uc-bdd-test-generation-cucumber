# Agentic AI Flow — BDD Test Automation Pipeline

## Overview

This framework implements a **fully autonomous Agentic AI pipeline** for end-to-end BDD test automation. Nine specialized agents collaborate through a central orchestrator, each making independent decisions at key points in the pipeline.

```
                          AGENTIC AI ORCHESTRATOR
                                  |
     ┌────────┬────────┬────────┬─┴──────┬────────┬────────┬────────┬────────┐
     v        v        v        v        v        v        v        v        v
  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐
  │Story │ │Analy-│ │Feature│ │Test  │ │Page  │ │Execu-│ │Report│ │Deploy│ │Feed- │
  │Ingest│→│sis   │→│Gen   │→│Data  │→│Object│→│tion  │→│ing   │→│ment  │→│back  │
  │Agent │ │Agent │ │Agent │ │Agent │ │Agent │ │Agent │ │Agent │ │Agent │ │Agent │
  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘ └──────┘ └──────┘ └──────┘ └──────┘
```

---

## Pipeline Steps

### Step 1: Story Ingestion Agent

**Purpose:** Fetch or create user stories from Jira or demo/sample data.

**Inputs:**
- Mode: `demo` | `jira` | `car-parts` | `commit`
- Jira credentials (if jira mode)
- Story keys (optional filter)

**Decision Points:**
| Condition | Decision | Action |
|-----------|----------|--------|
| Mode = demo | PROCEED | Generate sample user stories |
| Mode = jira | PROCEED | Connect to Jira REST API, fetch assigned stories |
| Mode = car-parts | PROCEED | Create 10 Car Parts Salesforce sample stories (CAR-1001 to CAR-1010) |
| Jira connection fails | RETRY (3x) | Retry connection, then ABORT |
| No stories found | ABORT | Stop pipeline, log error |

**Outputs:**
- `context.stories`: List of `UserStory` objects with keys, summaries, acceptance criteria
- Message to AnalysisAgent: `stories_ready`

**Code:** `agentic_orchestrator.py → StoryIngestionAgent`

---

### Step 2: Analysis Agent

**Purpose:** Analyze each story to determine test type, UI framework, and complexity.

**Inputs:**
- User stories from Step 1
- UI framework hint (salesforce / react / angular)

**Decision Points:**
| Condition | Decision | Action |
|-----------|----------|--------|
| Story contains UI keywords (click, button, form, dropdown) | UI test | Route to Selenium POM execution |
| Story contains API keywords (endpoint, request, http) | API test | Route to REST API test execution |
| Framework = salesforce | PROCEED | Use LWC shadow DOM traversal, lightning selectors |
| Framework = react | PROCEED | Use data-testid selectors, SPA routing |
| Framework = angular | PROCEED | Use formControlName, Material components |
| Story has > 3 acceptance criteria | Complex | Allocate more execution time |

**Analysis Per Story:**
```
{
  "key": "CAR-1001",
  "type": "ui",
  "complexity": "medium",
  "has_dropdowns": true,
  "has_crud": true
}
```

**Outputs:**
- `context.ui_framework`: Detected/selected framework
- `context.metadata.story_analysis`: Per-story analysis dict
- Message to FeatureGenerationAgent: `analysis_complete`

**Code:** `agentic_orchestrator.py → AnalysisAgent`

---

### Step 3: Feature Generation Agent

**Purpose:** Convert analyzed user stories into Gherkin BDD `.feature` files.

**Inputs:**
- Analyzed user stories from Step 2
- Output directory configuration

**Decision Points:**
| Condition | Decision | Action |
|-----------|----------|--------|
| Story has Given/When/Then criteria | PROCEED | Map directly to Gherkin scenarios |
| Story has bullet-point criteria | PROCEED | Parse and convert to Given/When/Then |
| Story is UI type | PROCEED | Add `Background: Given the browser is open` |
| Story is API type | PROCEED | Add `Background: Given the API base URL is configured` |
| Feature file already exists | DELEGATE | Send to FeedbackAgent for LLM diff update |

**Generated Feature File Structure:**
```gherkin
@CAR-1001 @salesforce @lwc
Feature: Create Engine Component Car Part in Salesforce LWC

  Background:
    Given the user is logged in to Salesforce

  Scenario: Create engine component with all dropdown fields
    Given the user is on the Car Parts list view
    When the user clicks the "New" button
    And the user selects "Engine Components" from the "Part Category" dropdown
    ...
    Then a success toast message "was created" should be displayed
```

**Outputs:**
- `context.feature_files`: List of generated `.feature` file paths
- Files written to `src/test/resources/features/generated/`
- Message to TestDataAgent: `features_generated`

**Code:** `agentic_orchestrator.py → FeatureGenerationAgent`, `gherkin_generator.py`

---

### Step 4: Test Data Preparation Agent

**Purpose:** Prepare, bundle, and upload test data for each user story.

**Inputs:**
- User stories from Step 1
- Feature files from Step 3
- Application URL configuration

**Decision Points:**
| Condition | Decision | Action |
|-----------|----------|--------|
| External test data JSON provided | PROCEED | Load and validate external data |
| No external data | PROCEED | Generate sample test data from story |
| Test data already exists for story | PROCEED | Overwrite with fresh data |

**Test Data Bundle (per story):**
```
src/test/test-data/CAR-1001/
├── test-data.json          # Field values, dropdown options
├── test-manifest.json      # Story metadata, feature path, app URL
└── selenium-config.json    # Browser config, timeouts, base URL
```

**Outputs:**
- `context.test_data`: Dict of story_key → TestDataSet
- Files written to `src/test/test-data/{story_key}/`
- Message to PageObjectAgent: `test_data_ready`

**Code:** `agentic_orchestrator.py → TestDataPreparationAgent`, `test_data_agent.py`

---

### Step 5: Page Object Agent

**Purpose:** Select or generate POM (Page Object Model) classes for the detected UI framework.

**Inputs:**
- UI framework from Step 2
- Story analysis (has_dropdowns, has_crud, etc.)

**Decision Points:**
| Condition | Decision | Action |
|-----------|----------|--------|
| Framework = salesforce-lwc | PROCEED | Load CarParts LWC page objects with shadow DOM |
| Framework = react | PROCEED | Load React page objects with data-testid |
| Framework = angular | PROCEED | Load Angular page objects with formControlName |
| Story has dropdowns | PROCEED | Include picklist traversal methods |
| Story has CRUD | PROCEED | Include create/edit/delete page methods |

**Salesforce LWC Page Objects:**
```
CarPartsBasePage          (shadow DOM traversal, spinner waits)
├── CarPartsLoginPage     (Salesforce login flow)
├── CarPartsNavigationPage (App Launcher, tabs, global search)
├── CarPartsListPage      (list views, sort, filter, search)
├── CarPartsFormPage      (text fields, picklists, lookups, save)
│   └── 12 Dropdown Fields:
│       ├── Part Category (12 values)
│       ├── Part Sub-Category (38 values, dependent on Category)
│       ├── Manufacturer (23 values)
│       ├── Condition (6 values)
│       ├── Vehicle Make (21 values)
│       ├── Model Year Range (9 values)
│       ├── Availability Status (7 values)
│       ├── Warehouse Location (7 values)
│       ├── Quality Grade (5 values)
│       ├── Shipping Class (7 values)
│       ├── Warranty Type (7 values)
│       └── Currency (7 values)
└── CarPartsRecordPage    (field values, edit, delete, toast)
```

**Outputs:**
- `context.page_objects`: Framework + page class registry
- Message to ExecutionAgent: `page_objects_ready`

**Code:** `agentic_orchestrator.py → PageObjectAgent`, `car_parts_page_objects.py`, `ui_framework_pages.py`

---

### Step 6: Execution Agent

**Purpose:** Execute Selenium tests using POM page objects against the target application.

**Inputs:**
- User stories with acceptance criteria
- Page objects from Step 5
- Test data from Step 4
- Selenium/WebDriver configuration

**Decision Points:**
| Condition | Decision | Action |
|-----------|----------|--------|
| WebDriver available | PROCEED | Launch browser, run tests |
| WebDriver not available | PROCEED | Simulate execution (demo mode) |
| Step passes | PROCEED | Record pass, move to next step |
| Step fails | RETRY (1x) | Retry step, then mark failed |
| Application unresponsive | WAIT (30s) | Wait for spinner, then retry |
| All steps timeout | ABORT | Mark scenario failed, continue next |

**Execution Flow Per Scenario:**
```
1. Navigate to application URL
2. Login (if required)
3. For each Gherkin step:
   a. Map step text to POM method (e.g., "clicks New button" → ListPage.click_new_button())
   b. Execute POM method via Selenium WebDriver
   c. Wait for Lightning framework ready
   d. Record step result (pass/fail/duration)
   e. Take screenshot on failure
4. Record scenario result
```

**Outputs:**
- `context.test_results`: Dict of story_key → ScenarioResult
- Message to ReportingAgent: `execution_complete`

**Code:** `agentic_orchestrator.py → ExecutionAgent`, `selenium_runner.py`, `ui_agent.py`

---

### Step 7: Reporting Agent

**Purpose:** Generate graphical HTML reports with Chart.js charts and Jira ID per test case.

**Inputs:**
- Test results from Step 6
- Story metadata (Jira IDs)

**Decision Points:**
| Condition | Decision | Action |
|-----------|----------|--------|
| All tests passed | PROCEED | Green report, success summary |
| Some tests failed | PROCEED | Include failure details, error messages, screenshots |
| Copado configured | PROCEED | Generate Copado-format JSON |

**Report Formats Generated:**
| Format | File | Purpose |
|--------|------|---------|
| HTML | `report-{run_id}.html` | Dashboard with 5 Chart.js charts + Jira ID table |
| JSON | `report-{run_id}.json` | Machine-readable full report |
| JUnit XML | `report-{run_id}.xml` | Jenkins / GitHub Actions CI integration |
| Text | `report-{run_id}.txt` | Log-friendly summary |
| Copado | `copado-report-{run_id}.json` | Copado Test Run/Result records |

**HTML Report Charts:**
1. **Pie Chart** — Pass / Fail / Skip distribution
2. **Horizontal Bar Chart** — Scenario duration with Jira ID labels
3. **Doughnut Gauge** — Pass rate percentage
4. **Stacked Bar** — Feature coverage (passed vs failed per Jira story)
5. **Polar Area** — Step type distribution (Given / When / Then / And)

**Test Case Table with Jira IDs:**
```
| #  | Jira ID   | Test Case                              | Status | Steps | Duration |
|----|-----------|----------------------------------------|--------|-------|----------|
| 1  | CAR-1001  | Create Engine Component Car Part        | PASSED | 29    | 7875ms   |
| 2  | CAR-1002  | Create Braking System Car Part          | PASSED | 23    | 7092ms   |
| 3  | CAR-1003  | Create Suspension Car Part              | PASSED | 19    | 6241ms   |
| ...| ...       | ...                                    | ...    | ...   | ...      |
| 10 | CAR-1010  | Validate Required Fields                | PASSED | 9     | 2078ms   |
```

**Outputs:**
- `context.execution_report`: TestExecutionReport object
- `context.report_files`: Dict of format → file path
- Message to DeploymentAgent: `reports_ready`

**Code:** `agentic_orchestrator.py → ReportingAgent`, `report_generator.py`

---

### Step 8: Deployment Agent

**Purpose:** Deploy test results to Copado CI/CD pipeline in Salesforce.

**Inputs:**
- Execution report from Step 7
- Report files (HTML, XML, JSON)
- Copado API credentials

**Decision Points:**
| Condition | Decision | Action |
|-----------|----------|--------|
| Copado configured | PROCEED | Create Test Run, upload Test Results |
| Copado not configured | PROCEED | Generate local Copado-format JSON |
| All tests passed | PROCEED | Trigger Copado deployment pipeline |
| Tests failed | SKIP | Block deployment, report failures |

**Copado Integration Flow:**
```
1. Authenticate to Copado (Salesforce OAuth)
2. Create copado__Test_Run__c record
3. For each scenario: create copado__Test_Result__c
4. Attach HTML/XML reports to Test Run
5. If 100% pass: trigger copado__Deployment__c pipeline
6. Return deployment status
```

**Outputs:**
- `context.copado_result`: Deployment result (status, message)

**Code:** `agentic_orchestrator.py → DeploymentAgent`, `copado_deployer.py`

---

### Step 9: Feedback Agent (Optional)

**Purpose:** Monitor Git commits and auto-update feature files using LLM analysis.

**Inputs:**
- Git commit SHA (if commit mode)
- Repository path
- LLM API credentials

**Decision Points:**
| Condition | Decision | Action |
|-----------|----------|--------|
| Commit references a story key (e.g., CAR-1001) | PROCEED | Analyze diff, update .feature |
| No story key in commit | SKIP | Ignore commit |
| LLM available | PROCEED | Send diff + current feature to LLM for update |
| LLM not available | PROCEED | Use template-based inference |
| Feature file changed meaningfully | PROCEED | Write updated feature, commit |
| No meaningful change | SKIP | Keep existing feature |

**LLM Feature Update Flow:**
```
1. Extract story keys from commit message
2. Get code diff for the commit
3. Load current .feature file for each story
4. Send to LLM: "Given this code change, update the BDD scenarios"
5. Parse LLM response as valid Gherkin
6. Write updated .feature file
7. Archive old version in feature-archive/
```

**Outputs:**
- Updated `.feature` files
- Archived old versions

**Code:** `agentic_orchestrator.py → FeedbackAgent`, `llm_feature_updater.py`, `git_commit_watcher.py`

---

## Inter-Agent Communication

Agents communicate through `AgentMessage` objects in the shared `PipelineContext`:

```python
@dataclass
class AgentMessage:
    sender: str       # e.g., "StoryIngestion"
    receiver: str     # e.g., "AnalysisAgent"
    action: str       # e.g., "stories_ready"
    payload: dict     # e.g., {"count": 10, "keys": ["CAR-1001", ...]}
    timestamp: str
```

**Message Flow:**
```
StoryIngestion  →  stories_ready       →  Analysis
Analysis        →  analysis_complete   →  FeatureGeneration
FeatureGeneration → features_generated →  TestData
TestData        →  test_data_ready     →  PageObject
PageObject      →  page_objects_ready  →  Execution
Execution       →  execution_complete  →  Reporting
Reporting       →  reports_ready       →  Deployment
```

---

## Decision Logging

Every decision point is recorded in `context.decisions`:

```python
@dataclass
class AgentDecision:
    agent_name: str        # Which agent made the decision
    decision: DecisionType # PROCEED / RETRY / SKIP / ABORT / DELEGATE
    reason: str            # Why this decision was made
    context: dict          # Additional context data
```

This allows full traceability of the pipeline's autonomous decision-making.

---

## Running the Pipeline

### Car Parts Salesforce LWC (Full E2E)
```bash
cd jira-selenium-agent
python agentic_orchestrator.py --mode car-parts --ui-framework salesforce
```

### Demo Mode (Sample Stories)
```bash
python agentic_orchestrator.py --mode demo
```

### Jira Mode (Live Stories)
```bash
export JIRA_SERVER_URL=https://your-instance.atlassian.net
export JIRA_USERNAME=user@example.com
export JIRA_API_TOKEN=your-token
python agentic_orchestrator.py --mode jira --stories PROJ-101 PROJ-102
```

### Commit Mode (LLM Feature Update)
```bash
python agentic_orchestrator.py --mode commit --commit-sha abc1234 --repo-path ..
```

---

## File Structure

```
jira-selenium-agent/
├── agentic_orchestrator.py           # Orchestrator + 9 Agent classes
├── AGENTIC_AI_FLOW.md                # This documentation
├── agent.py                          # Legacy CLI (still functional)
├── config.py                         # Environment configuration
├── jira_client.py                    # Jira REST API client
├── gherkin_generator.py              # Gherkin .feature file generation
├── selenium_runner.py                # Selenium WebDriver management
├── page_object_model.py              # Generic POM base classes
├── ui_framework_pages.py             # Salesforce/React/Angular POMs
├── ui_agent.py                       # UI framework auto-detection
├── test_data_agent.py                # Test data upload/bundling
├── report_generator.py               # HTML (Chart.js) / JSON / XML reports
├── copado_deployer.py                # Copado CI/CD deployment
├── git_commit_watcher.py             # Git commit monitoring
├── llm_feature_updater.py            # LLM-based feature updates
├── requirements.txt                  # Python dependencies
├── .env.example                      # Environment variable template
│
├── features/                         # Generated Gherkin feature files (dynamic)
│   └── car-parts/                   # Auto-created per scanned app
│       ├── create/                  # CAR-1001 to CAR-1004
│       ├── read/                    # CAR-1005, CAR-1007, CAR-1008
│       ├── update/                  # CAR-1006
│       ├── delete/                  # CAR-1009
│       └── validation/              # CAR-1010
│
├── runners/                         # Test execution code
│   ├── car_parts_runner.py          # Standalone runner with reports
│   ├── car_parts_page_objects.py    # LWC page objects (12 dropdowns)
│   └── selenium_e2e_runner.py       # Selenium execution engine
│
├── test-data/                       # Test data files
│   └── car_parts_test_data.json     # Test data + dropdown dependency map
│
├── config/                          # Configuration files
│   └── automation_config.json       # Portal config (auto-generated)
│
└── reports/                         # Generated test reports
```

---

## Agent Status Codes

| Status | Meaning |
|--------|---------|
| `IDLE` | Agent has not been activated yet |
| `RUNNING` | Agent is currently executing |
| `COMPLETED` | Agent finished successfully |
| `FAILED` | Agent encountered an error |
| `WAITING` | Agent is waiting for input/dependency |
| `SKIPPED` | Agent was skipped (condition not met) |

---

## Technology Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.12+ |
| BDD | Gherkin / Cucumber |
| Browser Automation | Selenium WebDriver |
| Design Pattern | Page Object Model (POM) |
| Charts | Chart.js 4.x (CDN) |
| CI/CD | GitHub Actions + Copado |
| Jira Integration | Jira REST API v3 |
| LLM Integration | OpenAI / Azure OpenAI / Anthropic |
| UI Frameworks | Salesforce LWC, React, Angular |
| Reports | HTML, JSON, JUnit XML, Copado JSON |
