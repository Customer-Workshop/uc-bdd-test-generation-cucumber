"""
Sample application: Vehicle Assembly Line (REACT tech stack).
Vehicle-manufacturing domain. The page is rendered with React (loaded via CDN)
so the framework scanner detects it as "react". Exposes the same scan contract
as the other samples (`/api/dropdown-fields` + screens + CRUD endpoints) so it
can be scanned INDEPENDENTLY on its own port.

Runs on port 5557.
"""
import uuid
from flask import Flask, jsonify, request

app = Flask(__name__)

# ─── Picklist field metadata (the scan contract) ───────────────────────────────
dropdown_fields = {
    "vehicle_model": [
        "Sedan X1", "SUV R5", "Hatchback H3", "Pickup T7",
        "Electric E2", "Crossover C4", "Van V6", "Coupe Q9",
    ],
    "assembly_station": [
        "Body Weld", "Paint Shop", "Powertrain", "Chassis Line",
        "Trim & Final", "Door Line", "Battery Install", "Final Inspection",
    ],
    "production_status": [
        "Scheduled", "In Progress", "On Hold", "Rework",
        "Completed", "Quality Hold", "Shipped",
    ],
    "engine_type": [
        "1.5L Petrol", "2.0L Petrol", "2.0L Diesel", "1.6L Turbo",
        "Full Electric", "Plug-in Hybrid", "Mild Hybrid",
    ],
    "transmission_type": ["5-Speed Manual", "6-Speed Manual", "CVT", "8-Speed Auto", "Dual-Clutch", "Single-Speed EV"],
    "paint_color": ["Pearl White", "Metallic Black", "Silver", "Racing Red", "Ocean Blue", "Graphite Grey", "Forest Green"],
    "shift": ["Shift A (Morning)", "Shift B (Afternoon)", "Shift C (Night)"],
    "plant_location": ["Plant 1 - Detroit", "Plant 2 - Stuttgart", "Plant 3 - Nagoya", "Plant 4 - Pune", "Plant 5 - Shanghai"],
    "quality_grade": ["A - Pass", "B - Minor Rework", "C - Major Rework", "D - Scrap"],
}

vehicles = [
    {"id": "VIN-1001", "vehicle_model": "SUV R5", "assembly_station": "Trim & Final",
     "production_status": "In Progress", "engine_type": "Full Electric", "plant_location": "Plant 1 - Detroit"},
    {"id": "VIN-1002", "vehicle_model": "Sedan X1", "assembly_station": "Paint Shop",
     "production_status": "Scheduled", "engine_type": "2.0L Petrol", "plant_location": "Plant 2 - Stuttgart"},
    {"id": "VIN-1003", "vehicle_model": "Pickup T7", "assembly_station": "Final Inspection",
     "production_status": "Quality Hold", "engine_type": "2.0L Diesel", "plant_location": "Plant 4 - Pune"},
]

work_orders = [
    {"id": "WO-5001", "vin": "VIN-1001", "assembly_station": "Trim & Final",
     "shift": "Shift A (Morning)", "production_status": "In Progress"},
    {"id": "WO-5002", "vin": "VIN-1003", "assembly_station": "Final Inspection",
     "shift": "Shift C (Night)", "production_status": "Quality Hold"},
]

# React SPA served from CDN — the scanner detects "react" from this markup.
PAGE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>Vehicle Assembly Line (React)</title>
  <script crossorigin src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
  <script crossorigin src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
  <style>
    body{font-family:'Segoe UI',Arial,sans-serif;margin:0;background:#f4f6f8;color:#1a2027}
    header{background:#1565c0;color:#fff;padding:16px 28px;font-size:20px;font-weight:600}
    main{padding:28px;max-width:980px;margin:0 auto}
    .card{background:#fff;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,.12);padding:20px;margin-bottom:20px}
    table{width:100%;border-collapse:collapse}
    th,td{text-align:left;padding:8px 10px;border-bottom:1px solid #e0e0e0;font-size:14px}
    th{background:#e3f2fd}
    .chip{display:inline-block;padding:2px 10px;border-radius:12px;background:#e3f2fd;color:#1565c0;font-size:12px}
    nav a{color:#1565c0;margin-right:16px;text-decoration:none;font-size:14px}
  </style>
</head>
<body>
  <!-- React application root -->
  <div id="root" data-reactroot></div>
  <script>
    const e = React.createElement;
    function App() {
      const [vehicles, setVehicles] = React.useState([]);
      const [fields, setFields] = React.useState({});
      React.useEffect(() => {
        fetch('/api/vehicles').then(r => r.json()).then(setVehicles);
        fetch('/api/dropdown-fields').then(r => r.json()).then(setFields);
      }, []);
      return e('div', null,
        e('header', null, '\\uD83D\\uDE97 Vehicle Assembly Line ',
          e('span', {style:{fontSize:13,fontWeight:400}}, '(React sample \\u00B7 port 5557)')),
        e('main', null,
          e('nav', null,
            e('a', {href:'/'}, 'Home'),
            e('a', {href:'/vehicles'}, 'Vehicles'),
            e('a', {href:'/work-orders'}, 'Work Orders'),
            e('a', {href:'/dropdown-fields'}, 'Fields')),
          e('div', {className:'card'},
            e('h3', null, 'Vehicles on the line'),
            e('table', null,
              e('thead', null, e('tr', null,
                e('th', null, 'VIN'), e('th', null, 'Model'),
                e('th', null, 'Station'), e('th', null, 'Status'), e('th', null, 'Engine'))),
              e('tbody', null, vehicles.map(v =>
                e('tr', {key:v.id},
                  e('td', null, v.id), e('td', null, v.vehicle_model),
                  e('td', null, v.assembly_station), e('td', null, v.production_status),
                  e('td', null, v.engine_type)))))),
          e('div', {className:'card'},
            e('h3', null, 'Scan contract'),
            e('p', null,
              'This React sample exposes ',
              e('span', {className:'chip'}, '/api/dropdown-fields'),
              ' with ' + Object.keys(fields).length + ' picklist fields. Scan ',
              e('b', null, 'http://localhost:5557'), ' from the Config Portal.'))));
    }
    ReactDOM.createRoot(document.getElementById('root')).render(e(App));
  </script>
</body>
</html>"""


# ─── Screen routes ─────────────────────────────────────────────────────────────
@app.route('/')
@app.route('/vehicles')
@app.route('/work-orders')
@app.route('/dropdown-fields')
def index():
    return PAGE


# ─── API (scan contract) ────────────────────────────────────────────────────────
@app.route('/api/health', methods=['GET'])
def api_health():
    return jsonify({"status": "ok", "app": "vehicle-assembly-react", "stack": "react", "port": 5557})


@app.route('/api/meta', methods=['GET'])
def api_meta():
    """Advertise this app's real screens + API endpoints so the scanner reports
    them accurately instead of probing a hardcoded path list."""
    return jsonify({
        "app": "vehicle-assembly-react",
        "stack": "react",
        "screens": [
            {"path": "/", "label": "Home"},
            {"path": "/vehicles", "label": "Vehicles List"},
            {"path": "/work-orders", "label": "Work Orders"},
            {"path": "/dropdown-fields", "label": "Fields"},
        ],
        "api_endpoints": [
            {"path": "/api/health", "method": "GET", "description": "Health Check"},
            {"path": "/api/dropdown-fields", "method": "GET", "description": "Field Metadata"},
            {"path": "/api/vehicles", "method": "GET", "description": "Vehicles CRUD"},
            {"path": "/api/work-orders", "method": "GET", "description": "Work Orders CRUD"},
        ],
    })


@app.route('/api/dropdown-fields', methods=['GET'])
def api_dropdown_fields():
    return jsonify(dropdown_fields)


@app.route('/api/vehicles', methods=['GET', 'POST'])
def api_vehicles():
    if request.method == 'POST':
        body = request.get_json(silent=True) or {}
        body['id'] = body.get('id') or f"VIN-{uuid.uuid4().hex[:4].upper()}"
        vehicles.append(body)
        return jsonify(body), 201
    return jsonify(vehicles)


@app.route('/api/vehicles/<vin>', methods=['GET'])
def api_vehicle(vin):
    for v in vehicles:
        if v['id'] == vin:
            return jsonify(v)
    return jsonify({"error": "Not found"}), 404


@app.route('/api/work-orders', methods=['GET', 'POST'])
def api_work_orders():
    if request.method == 'POST':
        body = request.get_json(silent=True) or {}
        body['id'] = body.get('id') or f"WO-{uuid.uuid4().hex[:4].upper()}"
        work_orders.append(body)
        return jsonify(body), 201
    return jsonify(work_orders)


if __name__ == '__main__':
    print("Vehicle Assembly Line (React) sample running on http://localhost:5557")
    app.run(host='0.0.0.0', port=5557, debug=False)
