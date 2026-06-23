"""Mock Salesforce Lightning UI for Car Parts Management.

A Flask web application that replicates the Salesforce Lightning Experience
interface for the Car_Part__c custom object, including:
- Lightning Design System (SLDS) styled UI
- 12 dropdown fields with dependent picklist behavior
- CRUD operations (create, read, update, delete)
- List views with search and sort
- Toast notifications
- Form validation for required fields
"""

import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from flask import Flask, jsonify, redirect, render_template_string, request, url_for
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Load dropdown field definitions from test data
TEST_DATA_PATH = Path(__file__).parent / "car_parts_test_data.json"
with open(TEST_DATA_PATH) as f:
    TEST_CONFIG = json.load(f)

DROPDOWN_FIELDS = TEST_CONFIG["dropdown_fields"]

# In-memory car parts store
car_parts_db: dict[str, dict] = {}

# Upload configuration store
UPLOAD_DIR = Path(__file__).parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

automation_config: dict = {
    "app_url": "http://localhost:5555",
    "uploaded_test_data": None,
    "uploaded_file_name": None,
    "upload_time": None,
    "test_records_count": len(TEST_CONFIG.get("test_records", [])),
}

# Pre-seed some records
SEED_RECORDS = TEST_CONFIG["test_records"][:4]
for rec in SEED_RECORDS:
    rec_id = str(uuid.uuid4())[:8]
    car_parts_db[rec_id] = {
        "id": rec_id,
        **rec["data"],
    }

# ---------------------------------------------------------------------------
# Lightning Design System HTML template
# ---------------------------------------------------------------------------

SLDS_CDN = "https://cdnjs.cloudflare.com/ajax/libs/design-system/2.24.3"

BASE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }} | Salesforce Lightning</title>
    <link rel="stylesheet" href="{{ slds }}/styles/salesforce-lightning-design-system.min.css">
    <style>
        :root {
            --sf-blue: #0176d3;
            --sf-dark: #032d60;
            --sf-nav: #0b1d34;
            --sf-white: #ffffff;
            --sf-gray: #f3f3f3;
            --sf-border: #dddbda;
            --sf-success: #2e844a;
            --sf-error: #ea001e;
            --sf-warning: #fe9339;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: 'Salesforce Sans', Arial, sans-serif; background: var(--sf-gray); }

        /* Global Navigation */
        .sf-global-nav {
            background: var(--sf-nav);
            color: white;
            padding: 0 24px;
            height: 48px;
            display: flex;
            align-items: center;
            position: sticky;
            top: 0;
            z-index: 1000;
        }
        .sf-global-nav .sf-logo {
            font-size: 20px;
            font-weight: 700;
            margin-right: 32px;
            color: white;
            text-decoration: none;
        }
        .sf-global-nav .sf-logo svg { height: 24px; fill: white; margin-right: 8px; vertical-align: middle; }
        .sf-global-nav .sf-nav-items { display: flex; gap: 0; height: 48px; }
        .sf-global-nav .sf-nav-item {
            padding: 0 16px;
            color: rgba(255,255,255,0.8);
            text-decoration: none;
            display: flex;
            align-items: center;
            font-size: 13px;
            border-bottom: 3px solid transparent;
            transition: all 0.2s;
        }
        .sf-global-nav .sf-nav-item:hover,
        .sf-global-nav .sf-nav-item.active {
            color: white;
            border-bottom-color: white;
            background: rgba(255,255,255,0.08);
        }

        /* App Launcher */
        .sf-app-header {
            background: var(--sf-blue);
            color: white;
            padding: 12px 24px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .sf-app-header h1 { font-size: 18px; font-weight: 700; }

        /* Page container */
        .sf-page { max-width: 1280px; margin: 0 auto; padding: 16px 24px; }

        /* Card */
        .sf-card {
            background: white;
            border: 1px solid var(--sf-border);
            border-radius: 4px;
            box-shadow: 0 2px 2px rgba(0,0,0,0.05);
            margin-bottom: 16px;
        }
        .sf-card-header {
            padding: 12px 16px;
            border-bottom: 1px solid var(--sf-border);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .sf-card-header h2 { font-size: 16px; font-weight: 700; color: var(--sf-dark); }
        .sf-card-body { padding: 16px; }

        /* Buttons */
        .sf-btn {
            padding: 8px 16px;
            border-radius: 4px;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            border: 1px solid var(--sf-border);
            background: white;
            color: var(--sf-dark);
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 4px;
            transition: background 0.15s;
        }
        .sf-btn:hover { background: var(--sf-gray); }
        .sf-btn-brand {
            background: var(--sf-blue);
            color: white;
            border-color: var(--sf-blue);
        }
        .sf-btn-brand:hover { background: #014486; }
        .sf-btn-destructive {
            background: var(--sf-error);
            color: white;
            border-color: var(--sf-error);
        }
        .sf-btn-destructive:hover { background: #ba0517; }
        .sf-btn-success {
            background: var(--sf-success);
            color: white;
            border-color: var(--sf-success);
        }

        /* Form */
        .sf-form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
        .sf-form-full { grid-column: 1 / -1; }
        .sf-form-group { margin-bottom: 0; }
        .sf-form-group label {
            display: block;
            font-size: 12px;
            font-weight: 600;
            color: #444;
            margin-bottom: 4px;
        }
        .sf-form-group label .required { color: var(--sf-error); margin-left: 2px; }
        .sf-form-group input,
        .sf-form-group select,
        .sf-form-group textarea {
            width: 100%;
            padding: 8px 12px;
            border: 1px solid var(--sf-border);
            border-radius: 4px;
            font-size: 14px;
            font-family: inherit;
            background: white;
            transition: border 0.15s;
        }
        .sf-form-group input:focus,
        .sf-form-group select:focus,
        .sf-form-group textarea:focus {
            outline: none;
            border-color: var(--sf-blue);
            box-shadow: 0 0 0 2px rgba(1,118,211,0.2);
        }
        .sf-form-group textarea { min-height: 80px; resize: vertical; }
        .sf-form-group .sf-error-msg {
            color: var(--sf-error);
            font-size: 12px;
            margin-top: 4px;
            display: none;
        }
        .sf-form-group.has-error input,
        .sf-form-group.has-error select {
            border-color: var(--sf-error);
        }
        .sf-form-group.has-error .sf-error-msg { display: block; }

        /* Table / List View */
        .sf-table { width: 100%; border-collapse: collapse; }
        .sf-table th {
            text-align: left;
            padding: 8px 12px;
            font-size: 12px;
            font-weight: 700;
            color: #444;
            background: var(--sf-gray);
            border-bottom: 2px solid var(--sf-border);
            cursor: pointer;
            user-select: none;
        }
        .sf-table th:hover { background: #e5e5e5; }
        .sf-table td {
            padding: 8px 12px;
            font-size: 13px;
            border-bottom: 1px solid var(--sf-border);
        }
        .sf-table tr:hover td { background: #f0f7ff; }
        .sf-table .sf-link {
            color: var(--sf-blue);
            text-decoration: none;
            font-weight: 600;
        }
        .sf-table .sf-link:hover { text-decoration: underline; }

        /* Search bar */
        .sf-search {
            display: flex;
            gap: 8px;
            margin-bottom: 12px;
            align-items: center;
        }
        .sf-search input {
            flex: 1;
            padding: 8px 12px;
            border: 1px solid var(--sf-border);
            border-radius: 4px;
            font-size: 14px;
        }
        .sf-search input:focus { outline: none; border-color: var(--sf-blue); }

        /* Toast */
        .sf-toast {
            position: fixed;
            top: 60px;
            left: 50%;
            transform: translateX(-50%);
            padding: 12px 24px;
            border-radius: 4px;
            font-size: 14px;
            font-weight: 600;
            color: white;
            z-index: 9999;
            display: none;
            animation: slideDown 0.3s ease;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            min-width: 300px;
            text-align: center;
        }
        .sf-toast.success { background: var(--sf-success); display: block; }
        .sf-toast.error { background: var(--sf-error); display: block; }
        @keyframes slideDown {
            from { opacity: 0; top: 40px; }
            to { opacity: 1; top: 60px; }
        }

        /* Record detail */
        .sf-detail-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px 32px; }
        .sf-detail-item label { font-size: 12px; color: #666; display: block; }
        .sf-detail-item .sf-detail-value { font-size: 14px; color: var(--sf-dark); font-weight: 500; padding: 4px 0; }

        /* Badge */
        .sf-badge {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 700;
        }
        .sf-badge-success { background: #e6f9ed; color: var(--sf-success); }
        .sf-badge-warning { background: #fef3e0; color: #7e5900; }
        .sf-badge-error { background: #fce4e4; color: var(--sf-error); }

        /* Spinner */
        .sf-spinner {
            display: none;
            text-align: center;
            padding: 40px;
        }
        .sf-spinner.active { display: block; }
        .sf-spinner-icon {
            width: 40px;
            height: 40px;
            border: 4px solid var(--sf-border);
            border-top: 4px solid var(--sf-blue);
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
            margin: 0 auto 12px;
        }
        @keyframes spin { to { transform: rotate(360deg); } }

        /* Modal */
        .sf-modal-overlay {
            display: none;
            position: fixed;
            inset: 0;
            background: rgba(0,0,0,0.5);
            z-index: 9000;
            justify-content: center;
            align-items: center;
        }
        .sf-modal-overlay.active { display: flex; }
        .sf-modal {
            background: white;
            border-radius: 8px;
            width: 420px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.2);
        }
        .sf-modal-header {
            padding: 16px;
            border-bottom: 1px solid var(--sf-border);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .sf-modal-header h2 { font-size: 16px; font-weight: 700; }
        .sf-modal-body { padding: 16px; }
        .sf-modal-footer {
            padding: 12px 16px;
            border-top: 1px solid var(--sf-border);
            text-align: right;
            display: flex;
            gap: 8px;
            justify-content: flex-end;
        }

        /* List view selector */
        .sf-listview-selector {
            display: flex;
            gap: 8px;
            margin-bottom: 12px;
            align-items: center;
        }
        .sf-listview-selector select {
            padding: 6px 12px;
            border: 1px solid var(--sf-border);
            border-radius: 4px;
            font-size: 13px;
        }

        /* Footer */
        .sf-footer { text-align: center; padding: 24px; color: #999; font-size: 12px; }

        /* Test Data styles */
        .td-section { margin-bottom: 24px; }
        .td-section-title {
            font-size: 15px; font-weight: 700; color: var(--sf-dark);
            margin-bottom: 12px; padding-bottom: 8px; border-bottom: 2px solid var(--sf-blue);
            display: flex; align-items: center; gap: 8px;
        }
        .td-section-title .td-icon { color: var(--sf-blue); font-size: 18px; }
        .td-scenario-card {
            background: white; border: 1px solid var(--sf-border); border-radius: 6px;
            margin-bottom: 16px; overflow: hidden;
            box-shadow: 0 1px 3px rgba(0,0,0,0.06);
        }
        .td-scenario-header {
            background: linear-gradient(135deg, #032d60, #0176d3);
            color: white; padding: 12px 16px;
            display: flex; justify-content: space-between; align-items: center;
        }
        .td-scenario-header h3 { font-size: 14px; font-weight: 700; }
        .td-scenario-header .td-jira-id {
            background: rgba(255,255,255,0.2); padding: 2px 10px;
            border-radius: 12px; font-size: 12px; font-weight: 600;
        }
        .td-data-table { width: 100%; border-collapse: collapse; }
        .td-data-table th {
            text-align: left; padding: 8px 12px; font-size: 11px;
            font-weight: 700; color: #666; background: #f7f9fb;
            border-bottom: 1px solid var(--sf-border); text-transform: uppercase;
        }
        .td-data-table td {
            padding: 8px 12px; font-size: 13px; border-bottom: 1px solid #f0f0f0;
        }
        .td-data-table tr:hover td { background: #f0f7ff; }
        .td-field-name { color: #666; font-weight: 600; white-space: nowrap; }
        .td-field-value { color: var(--sf-dark); font-weight: 500; }
        .td-dropdown-card {
            background: white; border: 1px solid var(--sf-border); border-radius: 6px;
            margin-bottom: 12px; overflow: hidden;
        }
        .td-dropdown-header {
            padding: 10px 16px; background: #f7f9fb;
            border-bottom: 1px solid var(--sf-border);
            display: flex; justify-content: space-between; align-items: center;
        }
        .td-dropdown-header h4 { font-size: 13px; font-weight: 700; color: var(--sf-dark); }
        .td-dropdown-header .td-count {
            background: var(--sf-blue); color: white; padding: 2px 8px;
            border-radius: 12px; font-size: 11px; font-weight: 700;
        }
        .td-values-grid {
            display: flex; flex-wrap: wrap; gap: 6px; padding: 12px 16px;
        }
        .td-value-chip {
            background: #e8f4fd; color: #0176d3; padding: 4px 10px;
            border-radius: 4px; font-size: 12px; font-weight: 500;
            border: 1px solid #b9ddf5;
        }
        .td-dep-section { padding: 12px 16px; border-top: 1px solid var(--sf-border); }
        .td-dep-parent {
            font-size: 12px; font-weight: 700; color: #666;
            margin-bottom: 6px;
        }
        .td-dep-children {
            display: flex; flex-wrap: wrap; gap: 4px; margin-bottom: 8px;
        }
        .td-dep-chip {
            background: #fff3e0; color: #7e5900; padding: 3px 8px;
            border-radius: 3px; font-size: 11px; font-weight: 500;
            border: 1px solid #ffe0b2;
        }
        .td-stats-grid {
            display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 12px; margin-bottom: 20px;
        }
        .td-stat-card {
            background: white; border: 1px solid var(--sf-border); border-radius: 6px;
            padding: 16px; text-align: center;
        }
        .td-stat-value { font-size: 28px; font-weight: 800; color: var(--sf-blue); }
        .td-stat-label { font-size: 11px; font-weight: 600; color: #666; text-transform: uppercase; margin-top: 4px; }
        .td-required-badge {
            background: #fce4e4; color: var(--sf-error); padding: 2px 6px;
            border-radius: 3px; font-size: 10px; font-weight: 700; margin-left: 4px;
        }
    </style>
</head>
<body>
    <!-- Global Navigation -->
    <nav class="sf-global-nav">
        <a href="/" class="sf-logo">
            <svg viewBox="0 0 24 24" width="24" height="24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.22.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z" fill="white"/></svg>
            Salesforce
        </a>
        <div class="sf-nav-items">
            <a href="/" class="sf-nav-item {{ 'active' if active_tab == 'home' else '' }}">Home</a>
            <a href="/car-parts" class="sf-nav-item {{ 'active' if active_tab == 'car-parts' else '' }}">Car Parts</a>
            <a href="/test-data" class="sf-nav-item {{ 'active' if active_tab == 'test-data' else '' }}">Test Data</a>
            <a href="/upload-test-data" class="sf-nav-item {{ 'active' if active_tab == 'upload' else '' }}">Upload</a>
            <a href="/dropdown-fields" class="sf-nav-item {{ 'active' if active_tab == 'dropdown-fields' else '' }}">Dropdown Fields</a>
        </div>
    </nav>

    <!-- App Header -->
    <div class="sf-app-header">
        <h1>Car Parts Management</h1>
        <span style="font-size:13px; opacity:0.8">Lightning Experience</span>
    </div>

    {% if toast_msg %}
    <div class="sf-toast {{ toast_type }}" id="sfToast">{{ toast_msg }}</div>
    <script>setTimeout(function(){ document.getElementById('sfToast').style.display='none'; }, 4000);</script>
    {% endif %}

    {{ content|safe }}

    <div class="sf-footer">
        Mock Salesforce Lightning &mdash; Car Parts Automation Demo &mdash; BDD Test Framework
    </div>
</body>
</html>
"""

# ---------------------------------------------------------------------------
# Page templates
# ---------------------------------------------------------------------------

LIST_VIEW_CONTENT = """
<div class="sf-page">
    <div class="sf-card">
        <div class="sf-card-header">
            <h2>Car Parts <span style="color:#999; font-weight:400; font-size:13px;">({{ parts|length }} items)</span></h2>
            <a href="/car-parts/new" class="sf-btn sf-btn-brand">+ New</a>
        </div>
        <div class="sf-card-body" style="padding:0;">
            <div style="padding: 12px 16px;">
                <div class="sf-listview-selector">
                    <label style="font-size:12px; font-weight:600; color:#444;">List View:</label>
                    <select id="listViewSelect" onchange="filterListView(this.value)">
                        <option value="all" {{ 'selected' if view == 'all' else '' }}>All Car Parts</option>
                        <option value="instock" {{ 'selected' if view == 'instock' else '' }}>In Stock Parts</option>
                        <option value="lowstock" {{ 'selected' if view == 'lowstock' else '' }}>Low Stock</option>
                    </select>
                </div>
                <div class="sf-search">
                    <input type="text" id="searchInput" placeholder="Search car parts..." value="{{ search_term }}"
                           onkeyup="if(event.key==='Enter')doSearch()">
                    <button class="sf-btn" onclick="doSearch()">Search</button>
                </div>
            </div>
            <table class="sf-table" id="partsTable">
                <thead>
                    <tr>
                        <th onclick="sortTable(0)">Part Name</th>
                        <th onclick="sortTable(1)">Part Number</th>
                        <th onclick="sortTable(2)">Part Category</th>
                        <th onclick="sortTable(3)">Manufacturer</th>
                        <th onclick="sortTable(4)">Condition</th>
                        <th onclick="sortTable(5)">Unit Price</th>
                        <th onclick="sortTable(6)">Availability</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {% for part in parts %}
                    <tr>
                        <td><a href="/car-parts/{{ part.id }}" class="sf-link">{{ part['Part Name'] }}</a></td>
                        <td>{{ part.get('Part Number', '-') }}</td>
                        <td>{{ part.get('Part Category', '-') }}</td>
                        <td>{{ part.get('Manufacturer', '-') }}</td>
                        <td>{{ part.get('Condition', '-') }}</td>
                        <td>{{ '$' + part.get('Unit Price', '0') if part.get('Unit Price') else '-' }}</td>
                        <td>
                            {% set avail = part.get('Availability Status', '') %}
                            <span class="sf-badge {{ 'sf-badge-success' if avail == 'In Stock' else 'sf-badge-warning' if avail == 'Low Stock' else 'sf-badge-error' if avail == 'Out of Stock' else '' }}">
                                {{ avail or '-' }}
                            </span>
                        </td>
                        <td>
                            <a href="/car-parts/{{ part.id }}/edit" class="sf-btn" style="padding:4px 8px; font-size:12px;">Edit</a>
                            <button class="sf-btn sf-btn-destructive" style="padding:4px 8px; font-size:12px;" onclick="showDeleteModal('{{ part.id }}', '{{ part['Part Name'] }}')">Delete</button>
                        </td>
                    </tr>
                    {% endfor %}
                    {% if not parts %}
                    <tr><td colspan="8" style="text-align:center; padding:32px; color:#999;">No car parts found.</td></tr>
                    {% endif %}
                </tbody>
            </table>
        </div>
    </div>
</div>

<!-- Delete Confirmation Modal -->
<div class="sf-modal-overlay" id="deleteModal">
    <div class="sf-modal">
        <div class="sf-modal-header">
            <h2>Delete Car Part</h2>
            <button class="sf-btn" onclick="hideDeleteModal()" style="border:none; font-size:18px;">&times;</button>
        </div>
        <div class="sf-modal-body">
            <p>Are you sure you want to delete <strong id="deletePartName"></strong>? This action cannot be undone.</p>
        </div>
        <div class="sf-modal-footer">
            <button class="sf-btn" onclick="hideDeleteModal()">Cancel</button>
            <form id="deleteForm" method="POST" style="display:inline;">
                <button type="submit" class="sf-btn sf-btn-destructive">Delete</button>
            </form>
        </div>
    </div>
</div>

<script>
function doSearch() {
    var term = document.getElementById('searchInput').value;
    window.location.href = '/car-parts?search=' + encodeURIComponent(term);
}
function filterListView(view) {
    window.location.href = '/car-parts?view=' + view;
}
function showDeleteModal(id, name) {
    document.getElementById('deletePartName').textContent = name;
    document.getElementById('deleteForm').action = '/car-parts/' + id + '/delete';
    document.getElementById('deleteModal').classList.add('active');
}
function hideDeleteModal() {
    document.getElementById('deleteModal').classList.remove('active');
}
var sortDir = {};
function sortTable(col) {
    var table = document.getElementById('partsTable');
    var rows = Array.from(table.tBodies[0].rows);
    sortDir[col] = !sortDir[col];
    rows.sort(function(a, b) {
        var va = a.cells[col].textContent.trim();
        var vb = b.cells[col].textContent.trim();
        if (col === 5) { va = parseFloat(va.replace('$','')) || 0; vb = parseFloat(vb.replace('$','')) || 0; return sortDir[col] ? va - vb : vb - va; }
        return sortDir[col] ? va.localeCompare(vb) : vb.localeCompare(va);
    });
    rows.forEach(function(r) { table.tBodies[0].appendChild(r); });
}
</script>
"""

FORM_CONTENT = """
<div class="sf-page">
    <div class="sf-card">
        <div class="sf-card-header">
            <h2>{{ 'Edit' if edit_mode else 'New' }} Car Part</h2>
        </div>
        <div class="sf-card-body">
            <form method="POST" id="carPartForm" novalidate>
                <div class="sf-form-grid">
                    <!-- Part Name -->
                    <div class="sf-form-group" data-field="Part Name">
                        <label>Part Name <span class="required">*</span></label>
                        <input type="text" name="Part Name" value="{{ part.get('Part Name', '') }}" required>
                        <div class="sf-error-msg">Complete this field.</div>
                    </div>
                    <!-- Part Number -->
                    <div class="sf-form-group" data-field="Part Number">
                        <label>Part Number <span class="required">*</span></label>
                        <input type="text" name="Part Number" value="{{ part.get('Part Number', '') }}" required>
                        <div class="sf-error-msg">Complete this field.</div>
                    </div>

                    {% for api_name, field in dropdown_fields.items() %}
                    <div class="sf-form-group" data-field="{{ field['label'] }}">
                        <label>{{ field['label'] }}{% if field.get('is_required') %} <span class="required">*</span>{% endif %}</label>
                        {% if field.get('dependent_on') %}
                        <select name="{{ field['label'] }}" id="field_{{ api_name }}" {{ 'required' if field.get('is_required') else '' }}>
                            <option value="">--None--</option>
                        </select>
                        {% else %}
                        <select name="{{ field['label'] }}" id="field_{{ api_name }}" {{ 'required' if field.get('is_required') else '' }}>
                            <option value="">--None--</option>
                            {% for val in field.get('values', []) %}
                            <option value="{{ val }}" {{ 'selected' if part.get(field['label']) == val else '' }}>{{ val }}</option>
                            {% endfor %}
                        </select>
                        {% endif %}
                        <div class="sf-error-msg">Complete this field.</div>
                    </div>
                    {% endfor %}

                    <!-- Unit Price -->
                    <div class="sf-form-group" data-field="Unit Price">
                        <label>Unit Price</label>
                        <input type="number" name="Unit Price" value="{{ part.get('Unit Price', '') }}" step="0.01" min="0">
                    </div>
                    <!-- Stock Quantity -->
                    <div class="sf-form-group" data-field="Stock Quantity">
                        <label>Stock Quantity</label>
                        <input type="number" name="Stock Quantity" value="{{ part.get('Stock Quantity', '') }}" min="0">
                    </div>
                    <!-- Description -->
                    <div class="sf-form-group sf-form-full" data-field="Description">
                        <label>Description</label>
                        <textarea name="Description">{{ part.get('Description', '') }}</textarea>
                    </div>
                </div>
                <div style="margin-top: 20px; display: flex; gap: 8px; justify-content: flex-end;">
                    <a href="/car-parts" class="sf-btn">Cancel</a>
                    <button type="submit" class="sf-btn sf-btn-brand" id="saveBtn">Save</button>
                </div>
            </form>
        </div>
    </div>
</div>

<script>
// Dependent picklist: Part Sub-Category depends on Part Category
var dependencyMap = {{ dependency_map | tojson }};
var parentSelect = document.getElementById('field_Part_Category__c');
var childSelect = document.getElementById('field_Part_Sub_Category__c');
var currentSubCat = "{{ part.get('Part Sub-Category', '') }}";

function updateSubCategory() {
    var cat = parentSelect.value;
    childSelect.innerHTML = '<option value="">--None--</option>';
    if (cat && dependencyMap[cat]) {
        dependencyMap[cat].forEach(function(val) {
            var opt = document.createElement('option');
            opt.value = val;
            opt.textContent = val;
            if (val === currentSubCat) opt.selected = true;
            childSelect.appendChild(opt);
        });
    }
}
if (parentSelect) {
    parentSelect.addEventListener('change', function() {
        currentSubCat = '';
        updateSubCategory();
    });
    // Initialize on load
    updateSubCategory();
}

// Form validation
document.getElementById('carPartForm').addEventListener('submit', function(e) {
    var valid = true;
    var required = this.querySelectorAll('[required]');
    required.forEach(function(el) {
        var group = el.closest('.sf-form-group');
        if (!el.value.trim()) {
            group.classList.add('has-error');
            valid = false;
        } else {
            group.classList.remove('has-error');
        }
    });
    if (!valid) {
        e.preventDefault();
    }
});
</script>
"""

RECORD_CONTENT = """
<div class="sf-page">
    <div class="sf-card">
        <div class="sf-card-header">
            <h2>{{ part['Part Name'] }}</h2>
            <div style="display:flex; gap:8px;">
                <a href="/car-parts/{{ part.id }}/edit" class="sf-btn">Edit</a>
                <button class="sf-btn sf-btn-destructive" onclick="showDeleteModal('{{ part.id }}', '{{ part['Part Name'] }}')">Delete</button>
                <a href="/car-parts" class="sf-btn">Back to List</a>
            </div>
        </div>
        <div class="sf-card-body">
            <div class="sf-detail-grid">
                <div class="sf-detail-item">
                    <label>Part Name</label>
                    <div class="sf-detail-value">{{ part.get('Part Name', '-') }}</div>
                </div>
                <div class="sf-detail-item">
                    <label>Part Number</label>
                    <div class="sf-detail-value">{{ part.get('Part Number', '-') }}</div>
                </div>
                <div class="sf-detail-item">
                    <label>Part Category</label>
                    <div class="sf-detail-value">{{ part.get('Part Category', '-') }}</div>
                </div>
                <div class="sf-detail-item">
                    <label>Part Sub-Category</label>
                    <div class="sf-detail-value">{{ part.get('Part Sub-Category', '-') }}</div>
                </div>
                <div class="sf-detail-item">
                    <label>Manufacturer</label>
                    <div class="sf-detail-value">{{ part.get('Manufacturer', '-') }}</div>
                </div>
                <div class="sf-detail-item">
                    <label>Condition</label>
                    <div class="sf-detail-value">{{ part.get('Condition', '-') }}</div>
                </div>
                <div class="sf-detail-item">
                    <label>Unit Price</label>
                    <div class="sf-detail-value">{{ ('$' + part.get('Unit Price', '0')) if part.get('Unit Price') else '-' }}</div>
                </div>
                <div class="sf-detail-item">
                    <label>Stock Quantity</label>
                    <div class="sf-detail-value">{{ part.get('Stock Quantity', '-') }}</div>
                </div>
                <div class="sf-detail-item">
                    <label>Vehicle Make</label>
                    <div class="sf-detail-value">{{ part.get('Vehicle Make', '-') }}</div>
                </div>
                <div class="sf-detail-item">
                    <label>Model Year Range</label>
                    <div class="sf-detail-value">{{ part.get('Model Year Range', '-') }}</div>
                </div>
                <div class="sf-detail-item">
                    <label>Availability Status</label>
                    <div class="sf-detail-value">
                        {% set avail = part.get('Availability Status', '') %}
                        <span class="sf-badge {{ 'sf-badge-success' if avail == 'In Stock' else 'sf-badge-warning' if avail == 'Low Stock' else 'sf-badge-error' }}">{{ avail or '-' }}</span>
                    </div>
                </div>
                <div class="sf-detail-item">
                    <label>Warehouse Location</label>
                    <div class="sf-detail-value">{{ part.get('Warehouse Location', '-') }}</div>
                </div>
                <div class="sf-detail-item">
                    <label>Quality Grade</label>
                    <div class="sf-detail-value">{{ part.get('Quality Grade', '-') }}</div>
                </div>
                <div class="sf-detail-item">
                    <label>Shipping Class</label>
                    <div class="sf-detail-value">{{ part.get('Shipping Class', '-') }}</div>
                </div>
                <div class="sf-detail-item">
                    <label>Warranty Type</label>
                    <div class="sf-detail-value">{{ part.get('Warranty Type', '-') }}</div>
                </div>
                <div class="sf-detail-item">
                    <label>Currency</label>
                    <div class="sf-detail-value">{{ part.get('Currency', '-') }}</div>
                </div>
                {% if part.get('Description') %}
                <div class="sf-detail-item" style="grid-column: 1/-1;">
                    <label>Description</label>
                    <div class="sf-detail-value">{{ part.get('Description', '-') }}</div>
                </div>
                {% endif %}
            </div>
        </div>
    </div>
</div>

<!-- Delete Modal -->
<div class="sf-modal-overlay" id="deleteModal">
    <div class="sf-modal">
        <div class="sf-modal-header">
            <h2>Delete Car Part</h2>
            <button class="sf-btn" onclick="hideDeleteModal()" style="border:none; font-size:18px;">&times;</button>
        </div>
        <div class="sf-modal-body">
            <p>Are you sure you want to delete <strong>{{ part['Part Name'] }}</strong>?</p>
        </div>
        <div class="sf-modal-footer">
            <button class="sf-btn" onclick="hideDeleteModal()">Cancel</button>
            <form action="/car-parts/{{ part.id }}/delete" method="POST" style="display:inline;">
                <button type="submit" class="sf-btn sf-btn-destructive">Delete</button>
            </form>
        </div>
    </div>
</div>
<script>
function showDeleteModal() { document.getElementById('deleteModal').classList.add('active'); }
function hideDeleteModal() { document.getElementById('deleteModal').classList.remove('active'); }
</script>
"""

LOGIN_CONTENT = """
<div style="min-height: 100vh; background: linear-gradient(135deg, #1b2838, #0b5394); display: flex; justify-content: center; align-items: center;">
    <div style="background: white; border-radius: 8px; padding: 48px; width: 400px; box-shadow: 0 8px 32px rgba(0,0,0,0.3);">
        <div style="text-align:center; margin-bottom: 32px;">
            <svg viewBox="0 0 24 24" width="48" height="48"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.22.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z" fill="#0176d3"/></svg>
            <h1 style="color: #032d60; font-size: 24px; margin-top: 16px;">Salesforce</h1>
            <p style="color: #666; font-size: 14px;">Log in to Car Parts Management</p>
        </div>
        <form method="POST" action="/login">
            <div class="sf-form-group" style="margin-bottom: 16px;">
                <label>Username</label>
                <input type="text" name="username" value="admin@carparts.demo" style="width:100%; padding:10px 12px; border:1px solid #ddd; border-radius:4px;">
            </div>
            <div class="sf-form-group" style="margin-bottom: 24px;">
                <label>Password</label>
                <input type="password" name="password" value="demo1234" style="width:100%; padding:10px 12px; border:1px solid #ddd; border-radius:4px;">
            </div>
            <button type="submit" class="sf-btn sf-btn-brand" style="width:100%; padding: 12px; font-size: 16px; justify-content: center;">Log In</button>
        </form>
        <p style="text-align:center; margin-top: 16px; color: #999; font-size: 12px;">Mock Salesforce Lightning &mdash; BDD Test Demo</p>
    </div>
</div>
"""


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

def render_page(title, content_template, active_tab="car-parts", toast_msg="", toast_type="", **kwargs):
    content = render_template_string(content_template, **kwargs)
    return render_template_string(
        BASE_TEMPLATE,
        title=title,
        slds=SLDS_CDN,
        active_tab=active_tab,
        toast_msg=toast_msg,
        toast_type=toast_type,
        content=content,
    )


@app.route("/")
def home():
    return redirect("/login")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        return redirect("/car-parts")
    return render_template_string(LOGIN_CONTENT)


@app.route("/car-parts")
def list_parts():
    search = request.args.get("search", "").strip()
    view = request.args.get("view", "all")

    parts = list(car_parts_db.values())

    if search:
        search_lower = search.lower()
        parts = [p for p in parts if search_lower in p.get("Part Name", "").lower()
                 or search_lower in p.get("Part Number", "").lower()
                 or search_lower in p.get("Part Category", "").lower()
                 or search_lower in p.get("Manufacturer", "").lower()]

    if view == "instock":
        parts = [p for p in parts if p.get("Availability Status") == "In Stock"]
    elif view == "lowstock":
        parts = [p for p in parts if p.get("Availability Status") == "Low Stock"]

    toast_msg = request.args.get("toast", "")
    toast_type = request.args.get("toast_type", "success")

    return render_page(
        "Car Parts",
        LIST_VIEW_CONTENT,
        parts=parts,
        search_term=search,
        view=view,
        toast_msg=toast_msg,
        toast_type=toast_type,
    )


@app.route("/car-parts/new", methods=["GET", "POST"])
def new_part():
    if request.method == "POST":
        rec_id = str(uuid.uuid4())[:8]
        data = {"id": rec_id}
        for key in request.form:
            if request.form[key].strip():
                data[key] = request.form[key].strip()
        car_parts_db[rec_id] = data
        return redirect(url_for("view_part", part_id=rec_id) + "?toast=Car+Part+was+created&toast_type=success")

    dep_map = DROPDOWN_FIELDS.get("Part_Sub_Category__c", {}).get("dependency_map", {})
    return render_page(
        "New Car Part",
        FORM_CONTENT,
        part={},
        dropdown_fields=DROPDOWN_FIELDS,
        dependency_map=dep_map,
        edit_mode=False,
    )


@app.route("/car-parts/<part_id>")
def view_part(part_id):
    part = car_parts_db.get(part_id)
    if not part:
        return redirect("/car-parts?toast=Record+not+found&toast_type=error")

    toast_msg = request.args.get("toast", "")
    toast_type = request.args.get("toast_type", "success")

    return render_page(
        part.get("Part Name", "Car Part"),
        RECORD_CONTENT,
        part=part,
        toast_msg=toast_msg,
        toast_type=toast_type,
    )


@app.route("/car-parts/<part_id>/edit", methods=["GET", "POST"])
def edit_part(part_id):
    part = car_parts_db.get(part_id)
    if not part:
        return redirect("/car-parts?toast=Record+not+found&toast_type=error")

    if request.method == "POST":
        for key in request.form:
            val = request.form[key].strip()
            if val:
                part[key] = val
        car_parts_db[part_id] = part
        return redirect(url_for("view_part", part_id=part_id) + "?toast=Car+Part+was+saved&toast_type=success")

    dep_map = DROPDOWN_FIELDS.get("Part_Sub_Category__c", {}).get("dependency_map", {})
    return render_page(
        "Edit " + part.get("Part Name", "Car Part"),
        FORM_CONTENT,
        part=part,
        dropdown_fields=DROPDOWN_FIELDS,
        dependency_map=dep_map,
        edit_mode=True,
    )


@app.route("/car-parts/<part_id>/delete", methods=["POST"])
def delete_part(part_id):
    part = car_parts_db.pop(part_id, None)
    name = part.get("Part Name", "Record") if part else "Record"
    return redirect(f"/car-parts?toast={name}+was+deleted&toast_type=success")


# ---------------------------------------------------------------------------
# Test Data page template
# ---------------------------------------------------------------------------

TEST_DATA_CONTENT = """
<div class="sf-page">
    <!-- Stats Overview -->
    <div class="td-stats-grid">
        <div class="td-stat-card">
            <div class="td-stat-value">{{ test_records|length }}</div>
            <div class="td-stat-label">Test Scenarios</div>
        </div>
        <div class="td-stat-card">
            <div class="td-stat-value">{{ dropdown_count }}</div>
            <div class="td-stat-label">Dropdown Fields</div>
        </div>
        <div class="td-stat-card">
            <div class="td-stat-value">{{ total_values }}</div>
            <div class="td-stat-label">Total Picklist Values</div>
        </div>
        <div class="td-stat-card">
            <div class="td-stat-value">{{ dep_categories }}</div>
            <div class="td-stat-label">Dependent Categories</div>
        </div>
        <div class="td-stat-card">
            <div class="td-stat-value">{{ create_records|length }}</div>
            <div class="td-stat-label">Create Records</div>
        </div>
        <div class="td-stat-card">
            <div class="td-stat-value">{{ data_source }}</div>
            <div class="td-stat-label">Data Source</div>
        </div>
    </div>

    <!-- Test Records for Selenium Execution -->
    <div class="sf-card">
        <div class="sf-card-header">
            <h2>Selenium Test Data &mdash; Records Used for E2E Execution</h2>
            <a href="/car-parts" class="sf-btn sf-btn-brand">View in Salesforce UI</a>
        </div>
        <div class="sf-card-body" style="padding:0;">
            {% for rec in test_records %}
            <div class="td-scenario-card" style="margin: 16px;">
                <div class="td-scenario-header">
                    <h3>Scenario {{ loop.index }}: {{ rec.scenario }}</h3>
                    <span class="td-jira-id">CAR-{{ 1000 + loop.index }}</span>
                </div>
                <table class="td-data-table">
                    <thead>
                        <tr>
                            <th style="width:200px;">Field Name</th>
                            <th>Test Value (used by Selenium)</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% if rec.data is mapping %}
                            {% for field_name, field_value in rec.data.items() %}
                                {% if field_value is mapping %}
                                    {% for sub_key, sub_val in field_value.items() %}
                                    <tr>
                                        <td class="td-field-name">{{ field_name }} &rarr; {{ sub_key }}</td>
                                        <td class="td-field-value">{{ sub_val }}</td>
                                    </tr>
                                    {% endfor %}
                                {% else %}
                                <tr>
                                    <td class="td-field-name">{{ field_name }}</td>
                                    <td class="td-field-value">{{ field_value }}</td>
                                </tr>
                                {% endif %}
                            {% endfor %}
                        {% endif %}
                    </tbody>
                </table>
            </div>
            {% endfor %}
        </div>
    </div>

    <!-- JSON Source -->
    <div class="sf-card">
        <div class="sf-card-header">
            <h2>Raw Test Data Source (car_parts_test_data.json)</h2>
        </div>
        <div class="sf-card-body">
            <pre style="background:#1e1e1e; color:#d4d4d4; padding:16px; border-radius:6px; overflow-x:auto; font-size:12px; max-height:500px; overflow-y:auto;">{{ raw_json }}</pre>
        </div>
    </div>
</div>
"""

# ---------------------------------------------------------------------------
# Dropdown Fields page template
# ---------------------------------------------------------------------------

DROPDOWN_FIELDS_CONTENT = """
<div class="sf-page">
    <!-- Stats -->
    <div class="td-stats-grid">
        <div class="td-stat-card">
            <div class="td-stat-value">{{ fields|length }}</div>
            <div class="td-stat-label">Dropdown Fields</div>
        </div>
        <div class="td-stat-card">
            <div class="td-stat-value">{{ total_values }}</div>
            <div class="td-stat-label">Total Values</div>
        </div>
        <div class="td-stat-card">
            <div class="td-stat-value">{{ required_count }}</div>
            <div class="td-stat-label">Required Fields</div>
        </div>
        <div class="td-stat-card">
            <div class="td-stat-value">{{ dep_count }}</div>
            <div class="td-stat-label">Dependent Fields</div>
        </div>
    </div>

    <!-- Each dropdown field -->
    {% for api_name, field in fields.items() %}
    <div class="td-dropdown-card">
        <div class="td-dropdown-header">
            <h4>
                {{ field['label'] }}
                <span style="color:#999; font-weight:400; font-size:11px; margin-left:8px;">{{ api_name }}</span>
                {% if field.get('is_required') %}<span class="td-required-badge">REQUIRED</span>{% endif %}
                {% if field.get('dependent_on') %}<span style="background:#fff3e0; color:#7e5900; padding:2px 6px; border-radius:3px; font-size:10px; font-weight:700; margin-left:4px;">DEPENDENT</span>{% endif %}
            </h4>
            {% if field.get('values') %}
            <span class="td-count">{{ field.get('values', [])|length }} values</span>
            {% endif %}
        </div>

        {% if field.get('values') %}
        <div class="td-values-grid">
            {% for val in field.get('values', []) %}
            <span class="td-value-chip">{{ val }}</span>
            {% endfor %}
        </div>
        {% endif %}

        {% if field.get('dependency_map') %}
        <div style="padding: 0 16px 12px;">
            <div style="font-size:12px; font-weight:700; color:#666; margin-bottom:8px;">
                Depends on: <span style="color:var(--sf-blue);">{{ field['dependent_on'] }}</span>
            </div>
            {% for parent_val, children in field.get('dependency_map', {}).items() %}
            <div class="td-dep-section" style="padding:8px 0; border-top: none;">
                <div class="td-dep-parent">{{ parent_val }} ({{ children|length }} sub-values):</div>
                <div class="td-dep-children">
                    {% for child in children %}
                    <span class="td-dep-chip">{{ child }}</span>
                    {% endfor %}
                </div>
            </div>
            {% endfor %}
        </div>
        {% endif %}
    </div>
    {% endfor %}

    <!-- Mapping Summary Table -->
    <div class="sf-card">
        <div class="sf-card-header">
            <h2>Dropdown Fields &rarr; Salesforce API Mapping</h2>
        </div>
        <div class="sf-card-body" style="padding:0;">
            <table class="sf-table">
                <thead>
                    <tr>
                        <th>API Name</th>
                        <th>Label</th>
                        <th>Required</th>
                        <th>Dependent</th>
                        <th>Values Count</th>
                    </tr>
                </thead>
                <tbody>
                    {% for api_name, field in fields.items() %}
                    <tr>
                        <td style="font-family:monospace; font-size:12px; color:#666;">{{ api_name }}</td>
                        <td style="font-weight:600;">{{ field['label'] }}</td>
                        <td>
                            {% if field.get('is_required') %}
                            <span class="sf-badge sf-badge-error">Yes</span>
                            {% else %}
                            <span style="color:#999;">No</span>
                            {% endif %}
                        </td>
                        <td>
                            {% if field.get('dependent_on') %}
                            <span class="sf-badge sf-badge-warning">{{ field['dependent_on'] }}</span>
                            {% else %}
                            <span style="color:#999;">-</span>
                            {% endif %}
                        </td>
                        <td>
                            {% if field.get('dependency_map') %}
                            {{ field['dependency_map'].values()|map('length')|sum }} (across {{ field['dependency_map']|length }} categories)
                            {% elif field.get('values') %}
                            {{ field['values']|length }}
                            {% else %}
                            -
                            {% endif %}
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</div>
"""


# ---------------------------------------------------------------------------
# Test Data & Dropdown Fields routes
# ---------------------------------------------------------------------------

@app.route("/test-data")
def test_data_page():
    test_records = TEST_CONFIG.get("test_records", [])
    total_values = sum(
        len(f.get("values", []))
        for f in DROPDOWN_FIELDS.values()
    )
    dep_map = DROPDOWN_FIELDS.get("Part_Sub_Category__c", {}).get("dependency_map", {})
    dep_values = sum(len(v) for v in dep_map.values())
    total_values += dep_values

    create_records = [r for r in test_records if "search_term" not in r.get("data", {})]

    raw_json = json.dumps(TEST_CONFIG.get("test_records", []), indent=2)

    return render_page(
        "Test Data",
        TEST_DATA_CONTENT,
        active_tab="test-data",
        test_records=test_records,
        dropdown_count=len(DROPDOWN_FIELDS),
        total_values=total_values,
        dep_categories=len(dep_map),
        create_records=create_records,
        data_source="JSON",
        raw_json=raw_json,
    )


@app.route("/dropdown-fields")
def dropdown_fields_page():
    total_values = sum(
        len(f.get("values", []))
        for f in DROPDOWN_FIELDS.values()
    )
    dep_map = DROPDOWN_FIELDS.get("Part_Sub_Category__c", {}).get("dependency_map", {})
    dep_values = sum(len(v) for v in dep_map.values())
    total_values += dep_values

    required_count = sum(1 for f in DROPDOWN_FIELDS.values() if f.get("is_required"))
    dep_count = sum(1 for f in DROPDOWN_FIELDS.values() if f.get("dependent_on"))

    return render_page(
        "Dropdown Fields",
        DROPDOWN_FIELDS_CONTENT,
        active_tab="dropdown-fields",
        fields=DROPDOWN_FIELDS,
        total_values=total_values,
        required_count=required_count,
        dep_count=dep_count,
    )


# ---------------------------------------------------------------------------
# Upload Test Data page template
# ---------------------------------------------------------------------------

UPLOAD_TEST_DATA_CONTENT = """
<div class="sf-page">
    <!-- Current Configuration -->
    <div class="td-stats-grid">
        <div class="td-stat-card">
            <div class="td-stat-value" style="font-size:14px; word-break:break-all;">{{ config.app_url }}</div>
            <div class="td-stat-label">Application URL</div>
        </div>
        <div class="td-stat-card">
            <div class="td-stat-value">{{ config.test_records_count }}</div>
            <div class="td-stat-label">Test Records Loaded</div>
        </div>
        <div class="td-stat-card">
            <div class="td-stat-value">{{ config.uploaded_file_name or 'Default' }}</div>
            <div class="td-stat-label">Data Source</div>
        </div>
        <div class="td-stat-card">
            <div class="td-stat-value">{{ config.upload_time or 'Built-in' }}</div>
            <div class="td-stat-label">Last Upload</div>
        </div>
    </div>

    <!-- Upload Form -->
    <div class="sf-card">
        <div class="sf-card-header">
            <h2>Upload Test Data &amp; Configure Application URL</h2>
        </div>
        <div class="sf-card-body">
            <form method="POST" action="/upload-test-data" enctype="multipart/form-data" id="uploadForm">
                <!-- Application URL -->
                <div style="margin-bottom:24px;">
                    <div class="td-section-title">
                        <span class="td-icon">&#127760;</span> Application URL
                    </div>
                    <p style="font-size:13px; color:#666; margin-bottom:12px;">
                        Enter the URL of the application you want to run Selenium test automation against.
                        This URL will be used as the base URL for all BDD test scenarios.
                    </p>
                    <div class="sf-form-group">
                        <label>Target Application URL <span class="required">*</span></label>
                        <input type="url" name="app_url" id="appUrl"
                               value="{{ config.app_url }}"
                               placeholder="https://your-app.lightning.force.com"
                               required
                               style="font-size:15px; padding:12px 16px;">
                    </div>
                    <div style="margin-top:8px; display:flex; gap:8px; flex-wrap:wrap;">
                        <button type="button" class="sf-btn" onclick="setUrl('http://localhost:5555')" style="font-size:11px;">Mock Salesforce (localhost:5555)</button>
                        <button type="button" class="sf-btn" onclick="setUrl('https://login.salesforce.com')" style="font-size:11px;">Salesforce Production</button>
                        <button type="button" class="sf-btn" onclick="setUrl('https://test.salesforce.com')" style="font-size:11px;">Salesforce Sandbox</button>
                        <button type="button" class="sf-btn" onclick="setUrl('http://localhost:3000')" style="font-size:11px;">React (localhost:3000)</button>
                        <button type="button" class="sf-btn" onclick="setUrl('http://localhost:4200')" style="font-size:11px;">Angular (localhost:4200)</button>
                    </div>
                </div>

                <!-- File Upload -->
                <div style="margin-bottom:24px;">
                    <div class="td-section-title">
                        <span class="td-icon">&#128194;</span> Test Data File Upload
                    </div>
                    <p style="font-size:13px; color:#666; margin-bottom:12px;">
                        Upload a JSON file containing test records for Selenium execution.
                        The file should follow the format shown in the sample below.
                    </p>
                    <div class="sf-form-group">
                        <label>Test Data File (JSON)</label>
                        <div id="dropZone" style="border:2px dashed var(--sf-border); border-radius:8px; padding:32px; text-align:center; cursor:pointer; transition:all 0.2s; background:#fafbfc;"
                             ondragover="event.preventDefault(); this.style.borderColor='var(--sf-blue)'; this.style.background='#e8f4fd';"
                             ondragleave="this.style.borderColor='var(--sf-border)'; this.style.background='#fafbfc';"
                             ondrop="handleDrop(event)"
                             onclick="document.getElementById('fileInput').click()">
                            <div style="font-size:36px; margin-bottom:8px;">&#128196;</div>
                            <div style="font-size:14px; font-weight:600; color:var(--sf-dark);">Drop JSON file here or click to browse</div>
                            <div style="font-size:12px; color:#999; margin-top:4px;">Accepts .json files up to 5MB</div>
                            <div id="fileName" style="margin-top:12px; font-size:13px; color:var(--sf-success); font-weight:600; display:none;"></div>
                        </div>
                        <input type="file" name="test_data_file" id="fileInput" accept=".json" style="display:none;" onchange="showFileName(this)">
                    </div>
                </div>

                <!-- JSON Editor (paste) -->
                <div style="margin-bottom:24px;">
                    <div class="td-section-title">
                        <span class="td-icon">&#9998;</span> Or Paste Test Data JSON
                    </div>
                    <p style="font-size:13px; color:#666; margin-bottom:12px;">
                        Alternatively, paste your test data JSON directly below. File upload takes precedence if both are provided.
                    </p>
                    <div class="sf-form-group">
                        <label>Test Data JSON</label>
                        <textarea name="test_data_json" id="jsonEditor"
                                  style="font-family:'Courier New',monospace; font-size:12px; min-height:250px; resize:vertical; background:#1e1e1e; color:#d4d4d4; padding:16px; border-radius:6px;"
                                  placeholder='[{"scenario": "Create Part", "data": {"Part Name": "...", "Part Category": "..."}}]'></textarea>
                    </div>
                    <div style="margin-top:8px; display:flex; gap:8px;">
                        <button type="button" class="sf-btn" onclick="validateJson()">Validate JSON</button>
                        <button type="button" class="sf-btn" onclick="formatJson()">Format JSON</button>
                        <button type="button" class="sf-btn" onclick="loadSample()">Load Sample</button>
                        <span id="jsonStatus" style="font-size:12px; font-weight:600; display:flex; align-items:center;"></span>
                    </div>
                </div>

                <!-- Submit -->
                <div style="display:flex; gap:12px; justify-content:flex-end; padding-top:16px; border-top:1px solid var(--sf-border);">
                    <a href="/test-data" class="sf-btn">View Current Test Data</a>
                    <button type="submit" class="sf-btn sf-btn-brand" style="padding:12px 32px; font-size:14px;">
                        Upload &amp; Save Configuration
                    </button>
                </div>
            </form>
        </div>
    </div>

    <!-- Sample Format Reference -->
    <div class="sf-card">
        <div class="sf-card-header">
            <h2>Expected JSON Format</h2>
            <button class="sf-btn" onclick="copySample()" style="font-size:11px;">Copy Sample</button>
        </div>
        <div class="sf-card-body">
            <pre id="sampleJson" style="background:#1e1e1e; color:#d4d4d4; padding:16px; border-radius:6px; overflow-x:auto; font-size:12px; max-height:400px; overflow-y:auto;">{{ sample_json }}</pre>
        </div>
    </div>

    <!-- Upload History -->
    {% if uploads %}
    <div class="sf-card">
        <div class="sf-card-header">
            <h2>Upload History</h2>
        </div>
        <div class="sf-card-body" style="padding:0;">
            <table class="sf-table">
                <thead>
                    <tr>
                        <th>Time</th>
                        <th>File Name</th>
                        <th>Records</th>
                        <th>App URL</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    {% for upload in uploads %}
                    <tr>
                        <td>{{ upload.time }}</td>
                        <td>{{ upload.file_name }}</td>
                        <td>{{ upload.records_count }}</td>
                        <td style="font-size:12px; font-family:monospace;">{{ upload.app_url }}</td>
                        <td><span class="sf-badge sf-badge-success">Active</span></td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
    {% endif %}
</div>

<script>
function setUrl(url) {
    document.getElementById('appUrl').value = url;
}

function showFileName(input) {
    var nameEl = document.getElementById('fileName');
    if (input.files.length > 0) {
        nameEl.textContent = '✓ ' + input.files[0].name + ' (' + (input.files[0].size/1024).toFixed(1) + ' KB)';
        nameEl.style.display = 'block';
    }
}

function handleDrop(e) {
    e.preventDefault();
    var dropZone = document.getElementById('dropZone');
    dropZone.style.borderColor = 'var(--sf-border)';
    dropZone.style.background = '#fafbfc';
    var files = e.dataTransfer.files;
    if (files.length > 0 && files[0].name.endsWith('.json')) {
        document.getElementById('fileInput').files = files;
        showFileName(document.getElementById('fileInput'));
    }
}

function validateJson() {
    var editor = document.getElementById('jsonEditor');
    var status = document.getElementById('jsonStatus');
    try {
        var parsed = JSON.parse(editor.value);
        var count = Array.isArray(parsed) ? parsed.length : (parsed.test_records ? parsed.test_records.length : 0);
        status.innerHTML = '<span style="color:var(--sf-success);">&#10003; Valid JSON (' + count + ' records found)</span>';
    } catch(e) {
        status.innerHTML = '<span style="color:var(--sf-error);">&#10007; Invalid JSON: ' + e.message + '</span>';
    }
}

function formatJson() {
    var editor = document.getElementById('jsonEditor');
    try {
        var parsed = JSON.parse(editor.value);
        editor.value = JSON.stringify(parsed, null, 2);
        validateJson();
    } catch(e) {
        document.getElementById('jsonStatus').innerHTML = '<span style="color:var(--sf-error);">&#10007; Cannot format: ' + e.message + '</span>';
    }
}

function loadSample() {
    var sample = document.getElementById('sampleJson').textContent;
    document.getElementById('jsonEditor').value = sample;
    validateJson();
}

function copySample() {
    var sample = document.getElementById('sampleJson').textContent;
    navigator.clipboard.writeText(sample);
}
</script>
"""


# ---------------------------------------------------------------------------
# Upload Test Data route
# ---------------------------------------------------------------------------

upload_history: list[dict] = []


@app.route("/upload-test-data", methods=["GET", "POST"])
def upload_test_data():
    global TEST_CONFIG, DROPDOWN_FIELDS, automation_config

    toast_msg = ""
    toast_type = ""

    if request.method == "POST":
        app_url = request.form.get("app_url", "").strip()
        if app_url:
            automation_config["app_url"] = app_url

        test_data = None
        file_name = None

        # Check file upload first
        uploaded_file = request.files.get("test_data_file")
        if uploaded_file and uploaded_file.filename:
            file_name = secure_filename(uploaded_file.filename)
            try:
                content = uploaded_file.read().decode("utf-8")
                test_data = json.loads(content)
                # Save file to uploads dir
                save_path = UPLOAD_DIR / file_name
                save_path.write_text(content)
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                toast_msg = f"Invalid JSON file: {e}"
                toast_type = "error"

        # Fallback to pasted JSON
        if not test_data and not toast_msg:
            json_text = request.form.get("test_data_json", "").strip()
            if json_text:
                try:
                    test_data = json.loads(json_text)
                    file_name = "pasted_data.json"
                    save_path = UPLOAD_DIR / file_name
                    save_path.write_text(json.dumps(test_data, indent=2))
                except json.JSONDecodeError as e:
                    toast_msg = f"Invalid JSON: {e}"
                    toast_type = "error"

        # Process uploaded test data
        if test_data and not toast_msg:
            # Support both formats: array of records or full config with dropdown_fields
            if isinstance(test_data, list):
                TEST_CONFIG["test_records"] = test_data
                records_count = len(test_data)
            elif isinstance(test_data, dict):
                if "test_records" in test_data:
                    TEST_CONFIG["test_records"] = test_data["test_records"]
                    records_count = len(test_data["test_records"])
                else:
                    TEST_CONFIG["test_records"] = [test_data]
                    records_count = 1
                if "dropdown_fields" in test_data:
                    TEST_CONFIG["dropdown_fields"] = test_data["dropdown_fields"]
                    DROPDOWN_FIELDS.update(test_data["dropdown_fields"])
            else:
                records_count = 0

            automation_config["uploaded_test_data"] = test_data
            automation_config["uploaded_file_name"] = file_name
            automation_config["upload_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            automation_config["test_records_count"] = records_count

            # Also save to the main test data file for Selenium runner
            with open(TEST_DATA_PATH, "w") as f:
                json.dump(TEST_CONFIG, f, indent=2)

            upload_history.insert(0, {
                "time": automation_config["upload_time"],
                "file_name": file_name,
                "records_count": records_count,
                "app_url": app_url or automation_config["app_url"],
            })

            toast_msg = f"Test data uploaded successfully! {records_count} records loaded."
            toast_type = "success"
        elif not toast_msg and app_url:
            toast_msg = f"Application URL updated to: {app_url}"
            toast_type = "success"

    sample_json = json.dumps(TEST_CONFIG.get("test_records", [])[:2], indent=2)

    return render_page(
        "Upload Test Data",
        UPLOAD_TEST_DATA_CONTENT,
        active_tab="upload",
        config=automation_config,
        sample_json=sample_json,
        uploads=upload_history,
        toast_msg=toast_msg,
        toast_type=toast_type,
    )


# ---------------------------------------------------------------------------
# API endpoints for Selenium / automation
# ---------------------------------------------------------------------------

@app.route("/api/car-parts", methods=["GET"])
def api_list():
    return jsonify(list(car_parts_db.values()))


@app.route("/api/car-parts/<part_id>", methods=["GET"])
def api_get(part_id):
    part = car_parts_db.get(part_id)
    return jsonify(part) if part else (jsonify({"error": "not found"}), 404)


@app.route("/api/dropdown-fields", methods=["GET"])
def api_dropdowns():
    return jsonify(DROPDOWN_FIELDS)


@app.route("/api/test-data", methods=["GET"])
def api_test_data():
    return jsonify(TEST_CONFIG.get("test_records", []))


@app.route("/api/automation-config", methods=["GET"])
def api_automation_config():
    return jsonify(automation_config)


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  MOCK SALESFORCE LIGHTNING - CAR PARTS MANAGEMENT")
    print("=" * 60)
    print(f"  URL:        http://localhost:5555")
    print(f"  Login:      admin@carparts.demo / demo1234")
    print(f"  Car Parts:  http://localhost:5555/car-parts")
    print(f"  Test Data:  http://localhost:5555/test-data")
    print(f"  Upload:     http://localhost:5555/upload-test-data")
    print(f"  Dropdowns:  http://localhost:5555/dropdown-fields")
    print(f"  Records:    {len(car_parts_db)} pre-seeded")
    print("=" * 60 + "\n")
    app.run(host="0.0.0.0", port=5555, debug=False)
