"""
Flask server for the React-based Salesforce UI.
Serves the React build (Material UI) and exposes REST API endpoints
for the Car Parts CRUD operations and dropdown field data.
Runs on port 5555.
"""
import json
import os
import uuid
from pathlib import Path
from flask import Flask, jsonify, request, send_from_directory

# Paths
BASE_DIR = Path(__file__).parent
REACT_BUILD_DIR = BASE_DIR.parent / "frontend" / "build"
DATA_DIR = BASE_DIR.parent.parent / "sample-automation"

# Initialize Flask to serve React build
app = Flask(__name__, static_folder=str(REACT_BUILD_DIR / "static"))

# ─── In-memory data store ─────────────────────────────────────────────────────

dropdown_fields = {
    "part_category": [
        "Engine Components", "Transmission & Drivetrain", "Braking System",
        "Suspension & Steering", "Electrical & Lighting", "Exhaust System",
        "Body & Exterior", "Interior & Comfort", "Cooling System",
        "Fuel System", "HVAC & Climate", "Wheels & Tires"
    ],
    "manufacturer": [
        "Bosch", "Denso", "Brembo", "BorgWarner", "KYB", "Hella", "Continental",
        "Delphi", "Valeo", "NGK", "Mahle", "Gates", "SKF", "Moog", "Monroe",
        "ACDelco", "Motorcraft", "Aisin", "NTN", "Timken", "ZF", "TRW", "Sachs"
    ],
    "condition": ["New", "Refurbished", "Used - Grade A", "Used - Grade B", "Used - Grade C", "Salvage"],
    "vehicle_make": [
        "Toyota", "Honda", "BMW", "Mercedes-Benz", "Tesla", "Ford", "Chevrolet",
        "Audi", "Volkswagen", "Hyundai", "Kia", "Nissan", "Mazda", "Subaru",
        "Lexus", "Porsche", "Volvo", "Jaguar", "Land Rover", "Ferrari", "Lamborghini"
    ],
    "year_range": [
        "2024-2025", "2022-2023", "2020-2021", "2018-2019", "2015-2017",
        "2010-2014", "2005-2009", "2000-2004", "Pre-2000", "Universal"
    ],
    "availability": [
        "In Stock", "Low Stock", "Out of Stock", "Backordered",
        "Pre-Order", "Discontinued", "Special Order"
    ],
    "warehouse_location": [
        "Main Warehouse - A1", "Main Warehouse - B2", "Main Warehouse - C3",
        "Secondary Warehouse - D1", "Secondary Warehouse - E2",
        "Distribution Center - West", "Distribution Center - East",
        "Overflow Storage - F1"
    ],
    "quality_grade": ["OEM", "OEM Equivalent", "Premium Aftermarket", "Standard Aftermarket", "Economy", "Performance"],
    "shipping_class": ["Standard", "Express", "Overnight", "Freight", "Oversized", "Hazardous Material"],
    "warranty_type": [
        "Manufacturer Warranty", "Extended Warranty", "Limited Warranty",
        "90-Day Warranty", "1-Year Warranty", "2-Year Warranty", "Lifetime Warranty", "No Warranty"
    ],
    "currency": ["USD", "EUR", "GBP", "CAD", "AUD", "JPY"]
}

sub_category_map = {
    "Engine Components": ["Turbocharger", "Piston", "Crankshaft", "Camshaft", "Timing Belt", "Oil Pump", "Gasket Set", "Engine Mount"],
    "Transmission & Drivetrain": ["Clutch Kit", "Torque Converter", "CV Joint", "Drive Shaft", "Differential", "Transfer Case"],
    "Braking System": ["Brake Pad", "Brake Rotor", "Brake Caliper", "Brake Line", "Master Cylinder", "ABS Sensor", "Brake Kit"],
    "Suspension & Steering": ["Shock Absorber", "Coilover Kit", "Control Arm", "Tie Rod", "Ball Joint", "Sway Bar Link", "Power Steering Pump"],
    "Electrical & Lighting": ["Headlight", "Tail Light", "Alternator", "Starter Motor", "Battery", "Wiring Harness", "LED Headlight"],
    "Exhaust System": ["Catalytic Converter", "Muffler", "Exhaust Manifold", "O2 Sensor", "Exhaust Pipe"],
    "Body & Exterior": ["Bumper", "Fender", "Hood", "Mirror", "Grille", "Door Handle"],
    "Interior & Comfort": ["Seat Cover", "Floor Mat", "Steering Wheel Cover", "Dashboard Trim", "Sun Visor"],
    "Cooling System": ["Radiator", "Water Pump", "Thermostat", "Coolant Hose", "Radiator Fan"],
    "Fuel System": ["Fuel Pump", "Fuel Injector", "Fuel Filter", "Carburetor", "Fuel Tank"],
    "HVAC & Climate": ["AC Compressor", "Condenser", "Evaporator", "Blower Motor", "Heater Core"],
    "Wheels & Tires": ["Alloy Wheel", "Steel Wheel", "Tire", "Wheel Bearing", "Lug Nut Set"]
}

car_parts = [
    {
        "id": "CP-001",
        "part_name": "Turbocharger Assembly",
        "part_number": "TB-ENG-2024-001",
        "part_category": "Engine Components",
        "part_sub_category": "Turbocharger",
        "manufacturer": "BorgWarner",
        "condition": "New",
        "vehicle_make": "BMW",
        "year_range": "2022-2023",
        "unit_price": 1250.00,
        "stock_quantity": 15,
        "availability": "In Stock",
        "warehouse_location": "Main Warehouse - A1",
        "quality_grade": "OEM",
        "shipping_class": "Freight",
        "warranty_type": "Manufacturer Warranty",
        "currency": "USD",
        "description": "High-performance turbocharger for BMW 3-series engines"
    },
    {
        "id": "CP-002",
        "part_name": "Performance Brake Kit",
        "part_number": "BK-BRK-2024-002",
        "part_category": "Braking System",
        "part_sub_category": "Brake Kit",
        "manufacturer": "Brembo",
        "condition": "New",
        "vehicle_make": "Mercedes-Benz",
        "year_range": "2020-2021",
        "unit_price": 890.00,
        "stock_quantity": 22,
        "availability": "In Stock",
        "warehouse_location": "Main Warehouse - B2",
        "quality_grade": "Premium Aftermarket",
        "shipping_class": "Oversized",
        "warranty_type": "2-Year Warranty",
        "currency": "USD",
        "description": "Premium performance brake kit with cross-drilled rotors"
    },
    {
        "id": "CP-003",
        "part_name": "Coilover Suspension Kit",
        "part_number": "SK-SUS-2024-003",
        "part_category": "Suspension & Steering",
        "part_sub_category": "Coilover Kit",
        "manufacturer": "KYB",
        "condition": "New",
        "vehicle_make": "Honda",
        "year_range": "2020-2021",
        "unit_price": 675.00,
        "stock_quantity": 8,
        "availability": "Low Stock",
        "warehouse_location": "Secondary Warehouse - D1",
        "quality_grade": "OEM Equivalent",
        "shipping_class": "Standard",
        "warranty_type": "1-Year Warranty",
        "currency": "USD",
        "description": "Adjustable coilover kit for Honda Civic sport suspension"
    },
    {
        "id": "CP-004",
        "part_name": "LED Headlight Assembly",
        "part_number": "HL-ELC-2024-004",
        "part_category": "Electrical & Lighting",
        "part_sub_category": "LED Headlight",
        "manufacturer": "Hella",
        "condition": "New",
        "vehicle_make": "Tesla",
        "year_range": "2024-2025",
        "unit_price": 450.00,
        "stock_quantity": 30,
        "availability": "In Stock",
        "warehouse_location": "Main Warehouse - C3",
        "quality_grade": "OEM",
        "shipping_class": "Standard",
        "warranty_type": "Manufacturer Warranty",
        "currency": "USD",
        "description": "OEM LED headlight assembly with adaptive beam pattern"
    }
]

# ─── API Routes ───────────────────────────────────────────────────────────────

@app.route('/api/dropdown-fields', methods=['GET'])
def api_dropdown_fields():
    """Return all dropdown field definitions."""
    return jsonify(dropdown_fields)


@app.route('/api/sub-categories/<category>', methods=['GET'])
def api_sub_categories(category):
    """Return sub-categories for a given parent category."""
    subs = sub_category_map.get(category, [])
    return jsonify(subs)


@app.route('/api/car-parts', methods=['GET'])
def api_list_parts():
    """List all car parts."""
    return jsonify(car_parts)


@app.route('/api/car-parts/<part_id>', methods=['GET'])
def api_get_part(part_id):
    """Get a single car part by ID."""
    part = next((p for p in car_parts if p['id'] == part_id), None)
    if not part:
        return jsonify({"error": "Not found"}), 404
    return jsonify(part)


@app.route('/api/car-parts', methods=['POST'])
def api_create_part():
    """Create a new car part."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    data['id'] = f"CP-{str(len(car_parts) + 1).zfill(3)}"
    car_parts.append(data)
    return jsonify(data), 201


@app.route('/api/car-parts/<part_id>', methods=['PUT'])
def api_update_part(part_id):
    """Update an existing car part."""
    data = request.get_json()
    for i, part in enumerate(car_parts):
        if part['id'] == part_id:
            car_parts[i] = {**part, **data, 'id': part_id}
            return jsonify(car_parts[i])
    return jsonify({"error": "Not found"}), 404


@app.route('/api/car-parts/<part_id>', methods=['DELETE'])
def api_delete_part(part_id):
    """Delete a car part."""
    global car_parts
    original_len = len(car_parts)
    car_parts = [p for p in car_parts if p['id'] != part_id]
    if len(car_parts) < original_len:
        return jsonify({"message": "Deleted"}), 200
    return jsonify({"error": "Not found"}), 404


@app.route('/api/test-data', methods=['GET'])
def api_test_data():
    """Return the test data JSON (used by Selenium)."""
    td_path = DATA_DIR / "car_parts_test_data.json"
    if td_path.exists():
        with open(td_path) as f:
            return jsonify(json.load(f))
    return jsonify({"error": "Test data file not found"}), 404


# ─── Serve React App ──────────────────────────────────────────────────────────

@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve React static assets (JS, CSS)."""
    return send_from_directory(str(REACT_BUILD_DIR / "static"), filename)


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_react(path):
    """Serve React app - all non-API routes go to index.html for client-side routing."""
    if path.startswith('api/'):
        return jsonify({"error": "Not found"}), 404
    # Try to serve the file directly (favicon, manifest, etc.)
    file_path = REACT_BUILD_DIR / path
    if path and file_path.exists() and file_path.is_file():
        return send_from_directory(str(REACT_BUILD_DIR), path)
    # Fall back to index.html for React Router
    return send_from_directory(str(REACT_BUILD_DIR), 'index.html')


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("  Car Parts Management - React + Material UI")
    print("  Salesforce Lightning Web Component (Mock)")
    print("=" * 60)
    print(f"\n  React Build:  {REACT_BUILD_DIR}")
    print(f"  API Base:     http://localhost:5555/api/")
    print(f"  UI:           http://localhost:5555/")
    print(f"\n  Endpoints:")
    print(f"    GET  /api/dropdown-fields       - All dropdown definitions")
    print(f"    GET  /api/sub-categories/<cat>  - Sub-categories for category")
    print(f"    GET  /api/car-parts             - List all parts")
    print(f"    POST /api/car-parts             - Create part")
    print(f"    GET  /api/car-parts/<id>        - Get single part")
    print(f"    PUT  /api/car-parts/<id>        - Update part")
    print(f"    DEL  /api/car-parts/<id>        - Delete part")
    print(f"    GET  /api/test-data             - Test data JSON")
    print("\n" + "=" * 60 + "\n")
    app.run(host='0.0.0.0', port=5555, debug=False)
