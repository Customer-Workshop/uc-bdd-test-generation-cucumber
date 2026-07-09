"""
Sample application: Vehicle Quality Inspection (ANGULAR tech stack).
Vehicle-manufacturing domain. The page ships Angular markup (`<app-root>`,
`ng-version`) so the framework scanner detects it as "angular". Exposes the same
scan contract as the other samples (`/api/dropdown-fields` + screens + CRUD
endpoints) so it can be scanned INDEPENDENTLY on its own port.

Runs on port 5558.
"""
import uuid
from flask import Flask, jsonify, request

app = Flask(__name__)

# ─── Picklist field metadata (the scan contract) ───────────────────────────────
dropdown_fields = {
    "inspection_type": [
        "Incoming Material", "In-Process", "Final QA", "Road Test",
        "Emissions", "Safety Systems", "Paint Finish", "Torque Audit",
    ],
    "vehicle_model": [
        "Sedan X1", "SUV R5", "Hatchback H3", "Pickup T7",
        "Electric E2", "Crossover C4", "Van V6", "Coupe Q9",
    ],
    "defect_category": [
        "Weld Defect", "Paint Blemish", "Panel Gap", "Electrical Fault",
        "Fluid Leak", "Torque Out-of-Spec", "Trim Misalignment", "Software Fault", "None",
    ],
    "severity": ["Critical", "Major", "Minor", "Cosmetic", "Observation"],
    "component": [
        "Chassis", "Engine", "Battery Pack", "Transmission",
        "Brakes", "Suspension", "Body Panel", "Infotainment", "HVAC",
    ],
    "disposition": ["Accept", "Rework", "Repair", "Scrap", "Use-As-Is", "Return to Supplier"],
    "line_number": ["Line 1", "Line 2", "Line 3", "Line 4", "Line 5"],
    "inspector_shift": ["Shift A (Morning)", "Shift B (Afternoon)", "Shift C (Night)"],
    "plant_location": ["Plant 1 - Detroit", "Plant 2 - Stuttgart", "Plant 3 - Nagoya", "Plant 4 - Pune", "Plant 5 - Shanghai"],
}

inspections = [
    {"id": "QI-3001", "vehicle_model": "SUV R5", "inspection_type": "Final QA",
     "defect_category": "Panel Gap", "severity": "Minor", "disposition": "Rework"},
    {"id": "QI-3002", "vehicle_model": "Sedan X1", "inspection_type": "Emissions",
     "defect_category": "None", "severity": "Observation", "disposition": "Accept"},
    {"id": "QI-3003", "vehicle_model": "Pickup T7", "inspection_type": "Torque Audit",
     "defect_category": "Torque Out-of-Spec", "severity": "Major", "disposition": "Repair"},
]

defects = [
    {"id": "DF-7001", "inspection_id": "QI-3001", "component": "Body Panel",
     "severity": "Minor", "disposition": "Rework"},
    {"id": "DF-7002", "inspection_id": "QI-3003", "component": "Chassis",
     "severity": "Major", "disposition": "Repair"},
]

# Angular application shell — the scanner detects "angular" / "ng-" from this markup.
PAGE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>Vehicle Quality Inspection (Angular)</title>
  <!-- Angular application shell -->
  <style>
    body{font-family:Roboto,'Segoe UI',Arial,sans-serif;margin:0;background:#fafafa;color:#212121}
    .mat-toolbar{background:#b71c1c;color:#fff;padding:16px 28px;font-size:20px;font-weight:600}
    main{padding:28px;max-width:980px;margin:0 auto}
    .mat-card{background:#fff;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,.2);padding:20px;margin-bottom:20px}
    table{width:100%;border-collapse:collapse}
    th,td{text-align:left;padding:8px 10px;border-bottom:1px solid #e0e0e0;font-size:14px}
    th{background:#ffebee}
    .mat-chip{display:inline-block;padding:2px 10px;border-radius:12px;background:#ffebee;color:#b71c1c;font-size:12px}
    nav a{color:#b71c1c;margin-right:16px;text-decoration:none;font-size:14px}
  </style>
</head>
<body ng-app="inspectionApp">
  <app-root ng-version="17.0.8">
    <div class="mat-toolbar" ng-bind="title">&#128295; Vehicle Quality Inspection
      <span style="font-size:13px;font-weight:400">(Angular sample &middot; port 5558)</span>
    </div>
    <main>
      <nav>
        <a href="/" ng-click="nav('home')">Home</a>
        <a href="/inspections">Inspections</a>
        <a href="/defects">Defects</a>
        <a href="/dropdown-fields">Fields</a>
      </nav>
      <mat-card class="mat-card">
        <h3>Inspections</h3>
        <table>
          <thead><tr><th>ID</th><th>Model</th><th>Type</th><th>Defect</th><th>Disposition</th></tr></thead>
          <tbody id="inspection-rows" ng-repeat="row in inspections"></tbody>
        </table>
      </mat-card>
      <mat-card class="mat-card">
        <h3>Scan contract</h3>
        <p>This Angular sample exposes <span class="mat-chip">/api/dropdown-fields</span>
        with <span id="field-count">9</span> picklist fields, plus
        <span class="mat-chip">/api/inspections</span> and
        <span class="mat-chip">/api/defects</span>. Scan
        <b>http://localhost:5558</b> from the Config Portal.</p>
      </mat-card>
    </main>
  </app-root>
  <script>
    // Lightweight Angular-style bootstrap (ng-version shell rendered above).
    fetch('/api/inspections').then(r => r.json()).then(function(rows){
      var tb = document.getElementById('inspection-rows');
      tb.innerHTML = rows.map(function(r){
        return '<tr><td>'+r.id+'</td><td>'+r.vehicle_model+'</td><td>'+r.inspection_type+
               '</td><td>'+r.defect_category+'</td><td>'+r.disposition+'</td></tr>';
      }).join('');
    });
    fetch('/api/dropdown-fields').then(r => r.json()).then(function(f){
      document.getElementById('field-count').textContent = Object.keys(f).length;
    });
  </script>
</body>
</html>"""


# ─── Screen routes ─────────────────────────────────────────────────────────────
@app.route('/')
@app.route('/inspections')
@app.route('/defects')
@app.route('/dropdown-fields')
def index():
    return PAGE


# ─── API (scan contract) ────────────────────────────────────────────────────────
@app.route('/api/health', methods=['GET'])
def api_health():
    return jsonify({"status": "ok", "app": "vehicle-inspection-angular", "stack": "angular", "port": 5558})


@app.route('/api/meta', methods=['GET'])
def api_meta():
    """Advertise this app's real screens + API endpoints so the scanner reports
    them accurately instead of probing a hardcoded path list."""
    return jsonify({
        "app": "vehicle-inspection-angular",
        "stack": "angular",
        "screens": [
            {"path": "/", "label": "Home"},
            {"path": "/inspections", "label": "Inspections List"},
            {"path": "/defects", "label": "Defects"},
            {"path": "/dropdown-fields", "label": "Fields"},
        ],
        "api_endpoints": [
            {"path": "/api/health", "method": "GET", "description": "Health Check"},
            {"path": "/api/dropdown-fields", "method": "GET", "description": "Field Metadata"},
            {"path": "/api/inspections", "method": "GET", "description": "Inspections CRUD"},
            {"path": "/api/defects", "method": "GET", "description": "Defects CRUD"},
        ],
    })


@app.route('/api/dropdown-fields', methods=['GET'])
def api_dropdown_fields():
    return jsonify(dropdown_fields)


@app.route('/api/inspections', methods=['GET', 'POST'])
def api_inspections():
    if request.method == 'POST':
        body = request.get_json(silent=True) or {}
        body['id'] = body.get('id') or f"QI-{uuid.uuid4().hex[:4].upper()}"
        inspections.append(body)
        return jsonify(body), 201
    return jsonify(inspections)


@app.route('/api/inspections/<iid>', methods=['GET'])
def api_inspection(iid):
    for i in inspections:
        if i['id'] == iid:
            return jsonify(i)
    return jsonify({"error": "Not found"}), 404


@app.route('/api/defects', methods=['GET', 'POST'])
def api_defects():
    if request.method == 'POST':
        body = request.get_json(silent=True) or {}
        body['id'] = body.get('id') or f"DF-{uuid.uuid4().hex[:4].upper()}"
        defects.append(body)
        return jsonify(body), 201
    return jsonify(defects)


if __name__ == '__main__':
    print("Vehicle Quality Inspection (Angular) sample running on http://localhost:5558")
    app.run(host='0.0.0.0', port=5558, debug=False)
