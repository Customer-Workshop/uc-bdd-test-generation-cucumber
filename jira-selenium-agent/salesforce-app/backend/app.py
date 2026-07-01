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
DATA_DIR = BASE_DIR.parent.parent / "test-data"

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

# ─── Salesforce Multi-Relationship Data Model ──────────────────────────────
# Salesforce assigns two distinct API identities per relationship field:
#   - Field API Name (stores the ID): e.g. Manufacturer__c
#   - Relationship Name (for traversal): e.g. Manufacturer__r
# This prevents data blending across relationship paths.

relationship_schema = {
    "objects": {
        "Car_Part__c": {
            "api_name": "Car_Part__c",
            "label": "Car Part",
            "key_prefix": "CP",
            "fields": [
                {"api_name": "Id", "label": "Record ID", "type": "id"},
                {"api_name": "Name", "label": "Part Name", "type": "string"},
                {"api_name": "Part_Number__c", "label": "Part Number", "type": "string"},
                {"api_name": "Part_Category__c", "label": "Part Category", "type": "picklist"},
                {"api_name": "Part_Sub_Category__c", "label": "Part Sub-Category", "type": "picklist", "dependent_on": "Part_Category__c"},
                {"api_name": "Unit_Price__c", "label": "Unit Price", "type": "currency"},
                {"api_name": "Stock_Quantity__c", "label": "Stock Quantity", "type": "number"},
                {"api_name": "Condition__c", "label": "Condition", "type": "picklist"},
                {"api_name": "Vehicle_Make__c", "label": "Vehicle Make", "type": "picklist"},
                {"api_name": "Quality_Grade__c", "label": "Quality Grade", "type": "picklist"},
                {"api_name": "Shipping_Class__c", "label": "Shipping Class", "type": "picklist"},
                {"api_name": "Warranty_Type__c", "label": "Warranty Type", "type": "picklist"},
                {"api_name": "Availability__c", "label": "Availability", "type": "picklist"},
            ],
            "relationships": [
                {
                    "field_api_name": "Manufacturer__c",
                    "relationship_name": "Manufacturer__r",
                    "type": "Lookup",
                    "related_to": "Manufacturer__c",
                    "label": "Manufacturer",
                    "description": "Lookup to the manufacturer who produces this part"
                },
                {
                    "field_api_name": "Warehouse__c",
                    "relationship_name": "Warehouse__r",
                    "type": "Lookup",
                    "related_to": "Warehouse__c",
                    "label": "Warehouse Location",
                    "description": "Lookup to the warehouse where this part is stored"
                },
            ],
            "child_relationships": [
                {"relationship_name": "Orders__r", "child_object": "Order__c", "field": "Car_Part__c", "type": "Master-Detail"},
                {"relationship_name": "Warranty_Claims__r", "child_object": "Warranty_Claim__c", "field": "Car_Part__c", "type": "Lookup"},
            ]
        },
        "Manufacturer__c": {
            "api_name": "Manufacturer__c",
            "label": "Manufacturer",
            "key_prefix": "MFR",
            "fields": [
                {"api_name": "Id", "label": "Record ID", "type": "id"},
                {"api_name": "Name", "label": "Manufacturer Name", "type": "string"},
                {"api_name": "Country__c", "label": "Country", "type": "string"},
                {"api_name": "Certification__c", "label": "Certification", "type": "picklist"},
                {"api_name": "Founded_Year__c", "label": "Founded Year", "type": "number"},
                {"api_name": "Website__c", "label": "Website", "type": "url"},
                {"api_name": "Is_Active__c", "label": "Active", "type": "boolean"},
            ],
            "relationships": [
                {
                    "field_api_name": "Primary_Supplier__c",
                    "relationship_name": "Primary_Supplier__r",
                    "type": "Lookup",
                    "related_to": "Supplier__c",
                    "label": "Primary Supplier",
                    "description": "Lookup to the primary supplier for raw materials"
                },
            ],
            "child_relationships": [
                {"relationship_name": "Car_Parts__r", "child_object": "Car_Part__c", "field": "Manufacturer__c", "type": "Lookup"},
            ]
        },
        "Warehouse__c": {
            "api_name": "Warehouse__c",
            "label": "Warehouse",
            "key_prefix": "WH",
            "fields": [
                {"api_name": "Id", "label": "Record ID", "type": "id"},
                {"api_name": "Name", "label": "Warehouse Name", "type": "string"},
                {"api_name": "Location__c", "label": "Location", "type": "string"},
                {"api_name": "Capacity__c", "label": "Capacity", "type": "number"},
                {"api_name": "Region__c", "label": "Region", "type": "picklist"},
                {"api_name": "Is_Active__c", "label": "Active", "type": "boolean"},
            ],
            "relationships": [],
            "child_relationships": [
                {"relationship_name": "Car_Parts__r", "child_object": "Car_Part__c", "field": "Warehouse__c", "type": "Lookup"},
                {"relationship_name": "Orders__r", "child_object": "Order__c", "field": "Ship_From_Warehouse__c", "type": "Lookup"},
            ]
        },
        "Supplier__c": {
            "api_name": "Supplier__c",
            "label": "Supplier",
            "key_prefix": "SUP",
            "fields": [
                {"api_name": "Id", "label": "Record ID", "type": "id"},
                {"api_name": "Name", "label": "Supplier Name", "type": "string"},
                {"api_name": "Country__c", "label": "Country", "type": "string"},
                {"api_name": "Contact_Email__c", "label": "Contact Email", "type": "email"},
                {"api_name": "Rating__c", "label": "Rating", "type": "number"},
                {"api_name": "Lead_Time_Days__c", "label": "Lead Time (Days)", "type": "number"},
            ],
            "relationships": [],
            "child_relationships": [
                {"relationship_name": "Manufacturers__r", "child_object": "Manufacturer__c", "field": "Primary_Supplier__c", "type": "Lookup"},
            ]
        },
        "Order__c": {
            "api_name": "Order__c",
            "label": "Order",
            "key_prefix": "ORD",
            "fields": [
                {"api_name": "Id", "label": "Record ID", "type": "id"},
                {"api_name": "Name", "label": "Order Number", "type": "autonumber"},
                {"api_name": "Quantity__c", "label": "Quantity", "type": "number"},
                {"api_name": "Order_Date__c", "label": "Order Date", "type": "date"},
                {"api_name": "Status__c", "label": "Status", "type": "picklist"},
                {"api_name": "Total_Amount__c", "label": "Total Amount", "type": "currency", "formula": "Quantity__c * Car_Part__r.Unit_Price__c"},
                {"api_name": "Customer_Name__c", "label": "Customer Name", "type": "string"},
            ],
            "relationships": [
                {
                    "field_api_name": "Car_Part__c",
                    "relationship_name": "Car_Part__r",
                    "type": "Master-Detail",
                    "related_to": "Car_Part__c",
                    "label": "Car Part",
                    "description": "Master-Detail to the car part being ordered (cascade delete)"
                },
                {
                    "field_api_name": "Ship_From_Warehouse__c",
                    "relationship_name": "Ship_From_Warehouse__r",
                    "type": "Lookup",
                    "related_to": "Warehouse__c",
                    "label": "Ship From Warehouse",
                    "description": "Lookup to warehouse the order ships from"
                },
            ],
            "child_relationships": [
                {"relationship_name": "Warranty_Claims__r", "child_object": "Warranty_Claim__c", "field": "Order__c", "type": "Lookup"},
            ]
        },
        "Warranty_Claim__c": {
            "api_name": "Warranty_Claim__c",
            "label": "Warranty Claim",
            "key_prefix": "WC",
            "fields": [
                {"api_name": "Id", "label": "Record ID", "type": "id"},
                {"api_name": "Name", "label": "Claim Number", "type": "autonumber"},
                {"api_name": "Claim_Date__c", "label": "Claim Date", "type": "date"},
                {"api_name": "Reason__c", "label": "Reason", "type": "textarea"},
                {"api_name": "Status__c", "label": "Status", "type": "picklist"},
                {"api_name": "Resolution__c", "label": "Resolution", "type": "picklist"},
                {"api_name": "Refund_Amount__c", "label": "Refund Amount", "type": "currency"},
            ],
            "relationships": [
                {
                    "field_api_name": "Car_Part__c",
                    "relationship_name": "Car_Part__r",
                    "type": "Lookup",
                    "related_to": "Car_Part__c",
                    "label": "Car Part",
                    "description": "Lookup to the car part this claim is filed against"
                },
                {
                    "field_api_name": "Order__c",
                    "relationship_name": "Order__r",
                    "type": "Lookup",
                    "related_to": "Order__c",
                    "label": "Order",
                    "description": "Lookup to the order associated with this warranty claim"
                },
            ],
            "child_relationships": []
        }
    }
}

# ─── Related object data stores ───────────────────────────────────────────────

manufacturers = [
    {"id": "MFR-001", "Name": "BorgWarner", "Country__c": "USA", "Certification__c": "ISO 9001", "Founded_Year__c": 1928, "Website__c": "https://borgwarner.com", "Is_Active__c": True, "Primary_Supplier__c": "SUP-001"},
    {"id": "MFR-002", "Name": "Brembo", "Country__c": "Italy", "Certification__c": "ISO 14001", "Founded_Year__c": 1961, "Website__c": "https://brembo.com", "Is_Active__c": True, "Primary_Supplier__c": "SUP-002"},
    {"id": "MFR-003", "Name": "KYB", "Country__c": "Japan", "Certification__c": "IATF 16949", "Founded_Year__c": 1919, "Website__c": "https://kyb.com", "Is_Active__c": True, "Primary_Supplier__c": "SUP-003"},
    {"id": "MFR-004", "Name": "Hella", "Country__c": "Germany", "Certification__c": "ISO 9001", "Founded_Year__c": 1899, "Website__c": "https://hella.com", "Is_Active__c": True, "Primary_Supplier__c": "SUP-001"},
    {"id": "MFR-005", "Name": "Denso", "Country__c": "Japan", "Certification__c": "IATF 16949", "Founded_Year__c": 1949, "Website__c": "https://denso.com", "Is_Active__c": True, "Primary_Supplier__c": "SUP-003"},
    {"id": "MFR-006", "Name": "Bosch", "Country__c": "Germany", "Certification__c": "ISO 9001", "Founded_Year__c": 1886, "Website__c": "https://bosch.com", "Is_Active__c": True, "Primary_Supplier__c": "SUP-002"},
]

warehouses = [
    {"id": "WH-001", "Name": "Main Warehouse - A1", "Location__c": "Detroit, MI", "Capacity__c": 5000, "Region__c": "North America", "Is_Active__c": True},
    {"id": "WH-002", "Name": "Main Warehouse - B2", "Location__c": "Detroit, MI", "Capacity__c": 3000, "Region__c": "North America", "Is_Active__c": True},
    {"id": "WH-003", "Name": "Main Warehouse - C3", "Location__c": "Detroit, MI", "Capacity__c": 4000, "Region__c": "North America", "Is_Active__c": True},
    {"id": "WH-004", "Name": "Secondary Warehouse - D1", "Location__c": "Chicago, IL", "Capacity__c": 2000, "Region__c": "North America", "Is_Active__c": True},
    {"id": "WH-005", "Name": "Distribution Center - West", "Location__c": "Los Angeles, CA", "Capacity__c": 6000, "Region__c": "West Coast", "Is_Active__c": True},
    {"id": "WH-006", "Name": "Distribution Center - East", "Location__c": "Newark, NJ", "Capacity__c": 4500, "Region__c": "East Coast", "Is_Active__c": True},
]

suppliers = [
    {"id": "SUP-001", "Name": "Global Steel Corp", "Country__c": "USA", "Contact_Email__c": "orders@globalsteel.com", "Rating__c": 4.5, "Lead_Time_Days__c": 14},
    {"id": "SUP-002", "Name": "Euro Materials GmbH", "Country__c": "Germany", "Contact_Email__c": "supply@euromaterials.de", "Rating__c": 4.8, "Lead_Time_Days__c": 21},
    {"id": "SUP-003", "Name": "Asia Pacific Components", "Country__c": "Japan", "Contact_Email__c": "procurement@apc.co.jp", "Rating__c": 4.6, "Lead_Time_Days__c": 28},
]

orders = [
    {"id": "ORD-001", "Name": "ORD-2024-0001", "Car_Part__c": "CP-001", "Ship_From_Warehouse__c": "WH-001", "Quantity__c": 5, "Order_Date__c": "2024-11-15", "Status__c": "Shipped", "Total_Amount__c": 6250.00, "Customer_Name__c": "AutoTech Solutions"},
    {"id": "ORD-002", "Name": "ORD-2024-0002", "Car_Part__c": "CP-002", "Ship_From_Warehouse__c": "WH-002", "Quantity__c": 10, "Order_Date__c": "2024-11-20", "Status__c": "Processing", "Total_Amount__c": 8900.00, "Customer_Name__c": "Premium Auto Works"},
    {"id": "ORD-003", "Name": "ORD-2024-0003", "Car_Part__c": "CP-001", "Ship_From_Warehouse__c": "WH-005", "Quantity__c": 3, "Order_Date__c": "2024-12-01", "Status__c": "Pending", "Total_Amount__c": 3750.00, "Customer_Name__c": "West Coast Motors"},
    {"id": "ORD-004", "Name": "ORD-2024-0004", "Car_Part__c": "CP-003", "Ship_From_Warehouse__c": "WH-004", "Quantity__c": 8, "Order_Date__c": "2024-12-05", "Status__c": "Shipped", "Total_Amount__c": 5400.00, "Customer_Name__c": "Civic Performance LLC"},
    {"id": "ORD-005", "Name": "ORD-2024-0005", "Car_Part__c": "CP-004", "Ship_From_Warehouse__c": "WH-003", "Quantity__c": 20, "Order_Date__c": "2024-12-10", "Status__c": "Delivered", "Total_Amount__c": 9000.00, "Customer_Name__c": "Tesla Parts Direct"},
]

warranty_claims = [
    {"id": "WC-001", "Name": "WC-2024-0001", "Car_Part__c": "CP-001", "Order__c": "ORD-001", "Claim_Date__c": "2025-01-10", "Reason__c": "Turbocharger seal failure under warranty period", "Status__c": "Approved", "Resolution__c": "Replacement", "Refund_Amount__c": 1250.00},
    {"id": "WC-002", "Name": "WC-2024-0002", "Car_Part__c": "CP-002", "Order__c": "ORD-002", "Claim_Date__c": "2025-02-15", "Reason__c": "Brake rotor premature wear", "Status__c": "Under Review", "Resolution__c": "Pending", "Refund_Amount__c": 0},
    {"id": "WC-003", "Name": "WC-2024-0003", "Car_Part__c": "CP-001", "Order__c": "ORD-003", "Claim_Date__c": "2025-03-01", "Reason__c": "Oil leak from turbo housing", "Status__c": "Approved", "Resolution__c": "Refund", "Refund_Amount__c": 1250.00},
]

# Map car part manufacturer names to manufacturer IDs
_mfr_name_to_id = {m["Name"]: m["id"] for m in manufacturers}
_wh_name_to_id = {w["Name"]: w["id"] for w in warehouses}

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
        "description": "High-performance turbocharger for BMW 3-series engines",
        "Manufacturer__c": "MFR-001",
        "Warehouse__c": "WH-001"
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
        "description": "Premium performance brake kit with cross-drilled rotors",
        "Manufacturer__c": "MFR-002",
        "Warehouse__c": "WH-002"
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
        "description": "Adjustable coilover kit for Honda Civic sport suspension",
        "Manufacturer__c": "MFR-003",
        "Warehouse__c": "WH-004"
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
        "description": "OEM LED headlight assembly with adaptive beam pattern",
        "Manufacturer__c": "MFR-004",
        "Warehouse__c": "WH-003"
    }
]

# ─── Helper: Resolve relationships ────────────────────────────────────────────

def _resolve_parent_relationship(record, field_api_name, relationship_name, data_store):
    """Resolve a parent (Lookup/Master-Detail) relationship via __r.
    E.g. Car_Part__c.Manufacturer__c -> Manufacturer__r object."""
    parent_id = record.get(field_api_name)
    if parent_id:
        parent = next((r for r in data_store if r["id"] == parent_id), None)
        if parent:
            return {k: v for k, v in parent.items() if k != "id" or k == "id"}
    return None


def _resolve_child_relationships(record_id, child_store, foreign_key_field):
    """Resolve child (one-to-many) records via __r.
    E.g. Car_Part__c -> Orders__r returns list of Order__c records."""
    return [r for r in child_store if r.get(foreign_key_field) == record_id]


def _expand_car_part(part):
    """Expand a car part with all relationship data (__r references)."""
    expanded = dict(part)
    # Parent relationships
    mfr = _resolve_parent_relationship(part, "Manufacturer__c", "Manufacturer__r", manufacturers)
    if mfr:
        expanded["Manufacturer__r"] = mfr
    wh = _resolve_parent_relationship(part, "Warehouse__c", "Warehouse__r", warehouses)
    if wh:
        expanded["Warehouse__r"] = wh
    # Child relationships
    expanded["Orders__r"] = {
        "totalSize": len(_resolve_child_relationships(part["id"], orders, "Car_Part__c")),
        "records": _resolve_child_relationships(part["id"], orders, "Car_Part__c")
    }
    expanded["Warranty_Claims__r"] = {
        "totalSize": len(_resolve_child_relationships(part["id"], warranty_claims, "Car_Part__c")),
        "records": _resolve_child_relationships(part["id"], warranty_claims, "Car_Part__c")
    }
    return expanded


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


# ─── Relationship API Routes ──────────────────────────────────────────────────

@app.route('/api/relationship-schema', methods=['GET'])
def api_relationship_schema():
    """Return the full Salesforce-style object relationship schema.
    Shows all custom objects, fields, Lookup/Master-Detail relationships,
    __c (field) and __r (relationship) API name pairs."""
    return jsonify(relationship_schema)


@app.route('/api/relationships/<object_name>', methods=['GET'])
def api_object_relationships(object_name):
    """Return relationships for a specific sObject.
    Shows both parent (Lookup/Master-Detail) and child relationships."""
    obj = relationship_schema["objects"].get(object_name)
    if not obj:
        return jsonify({"error": f"Object '{object_name}' not found"}), 404
    return jsonify({
        "object": object_name,
        "label": obj["label"],
        "parent_relationships": obj["relationships"],
        "child_relationships": obj["child_relationships"],
        "fields": obj["fields"],
    })


@app.route('/api/car-parts/<part_id>/related', methods=['GET'])
def api_car_part_related(part_id):
    """Get a car part with all expanded relationships (__r traversal).
    Demonstrates multi-relationship data hub pattern."""
    part = next((p for p in car_parts if p['id'] == part_id), None)
    if not part:
        return jsonify({"error": "Not found"}), 404
    return jsonify(_expand_car_part(part))


@app.route('/api/manufacturers', methods=['GET'])
def api_list_manufacturers():
    """List all manufacturers (Manufacturer__c)."""
    return jsonify(manufacturers)


@app.route('/api/manufacturers/<mfr_id>', methods=['GET'])
def api_get_manufacturer(mfr_id):
    """Get manufacturer with related car parts (child relationship)."""
    mfr = next((m for m in manufacturers if m['id'] == mfr_id), None)
    if not mfr:
        return jsonify({"error": "Not found"}), 404
    result = dict(mfr)
    # Parent: resolve Primary_Supplier__r
    supplier = _resolve_parent_relationship(mfr, "Primary_Supplier__c", "Primary_Supplier__r", suppliers)
    if supplier:
        result["Primary_Supplier__r"] = supplier
    # Children: Car_Parts__r
    result["Car_Parts__r"] = {
        "totalSize": len(_resolve_child_relationships(mfr_id, car_parts, "Manufacturer__c")),
        "records": _resolve_child_relationships(mfr_id, car_parts, "Manufacturer__c")
    }
    return jsonify(result)


@app.route('/api/warehouses', methods=['GET'])
def api_list_warehouses():
    """List all warehouses (Warehouse__c)."""
    return jsonify(warehouses)


@app.route('/api/warehouses/<wh_id>', methods=['GET'])
def api_get_warehouse(wh_id):
    """Get warehouse with related car parts and orders."""
    wh = next((w for w in warehouses if w['id'] == wh_id), None)
    if not wh:
        return jsonify({"error": "Not found"}), 404
    result = dict(wh)
    result["Car_Parts__r"] = {
        "totalSize": len(_resolve_child_relationships(wh_id, car_parts, "Warehouse__c")),
        "records": _resolve_child_relationships(wh_id, car_parts, "Warehouse__c")
    }
    result["Orders__r"] = {
        "totalSize": len(_resolve_child_relationships(wh_id, orders, "Ship_From_Warehouse__c")),
        "records": _resolve_child_relationships(wh_id, orders, "Ship_From_Warehouse__c")
    }
    return jsonify(result)


@app.route('/api/suppliers', methods=['GET'])
def api_list_suppliers():
    """List all suppliers (Supplier__c)."""
    return jsonify(suppliers)


@app.route('/api/suppliers/<sup_id>', methods=['GET'])
def api_get_supplier(sup_id):
    """Get supplier with manufacturers that use this supplier."""
    sup = next((s for s in suppliers if s['id'] == sup_id), None)
    if not sup:
        return jsonify({"error": "Not found"}), 404
    result = dict(sup)
    result["Manufacturers__r"] = {
        "totalSize": len(_resolve_child_relationships(sup_id, manufacturers, "Primary_Supplier__c")),
        "records": _resolve_child_relationships(sup_id, manufacturers, "Primary_Supplier__c")
    }
    return jsonify(result)


@app.route('/api/orders', methods=['GET'])
def api_list_orders():
    """List all orders (Order__c) with parent traversal."""
    expanded = []
    for order in orders:
        o = dict(order)
        # Child-to-parent: Order__c.Car_Part__r
        part = _resolve_parent_relationship(order, "Car_Part__c", "Car_Part__r", car_parts)
        if part:
            o["Car_Part__r"] = {"id": part["id"], "part_name": part.get("part_name", ""), "part_number": part.get("part_number", "")}
        # Child-to-parent: Order__c.Ship_From_Warehouse__r
        wh = _resolve_parent_relationship(order, "Ship_From_Warehouse__c", "Ship_From_Warehouse__r", warehouses)
        if wh:
            o["Ship_From_Warehouse__r"] = {"id": wh["id"], "Name": wh["Name"], "Location__c": wh.get("Location__c", "")}
        expanded.append(o)
    return jsonify(expanded)


@app.route('/api/orders/<order_id>', methods=['GET'])
def api_get_order(order_id):
    """Get order with parent traversals and child warranty claims."""
    order = next((o for o in orders if o['id'] == order_id), None)
    if not order:
        return jsonify({"error": "Not found"}), 404
    result = dict(order)
    # Parent: Car_Part__r
    part = _resolve_parent_relationship(order, "Car_Part__c", "Car_Part__r", car_parts)
    if part:
        result["Car_Part__r"] = part
    # Parent: Ship_From_Warehouse__r
    wh = _resolve_parent_relationship(order, "Ship_From_Warehouse__c", "Ship_From_Warehouse__r", warehouses)
    if wh:
        result["Ship_From_Warehouse__r"] = wh
    # Children: Warranty_Claims__r
    result["Warranty_Claims__r"] = {
        "totalSize": len(_resolve_child_relationships(order_id, warranty_claims, "Order__c")),
        "records": _resolve_child_relationships(order_id, warranty_claims, "Order__c")
    }
    return jsonify(result)


@app.route('/api/warranty-claims', methods=['GET'])
def api_list_warranty_claims():
    """List all warranty claims with parent traversals."""
    expanded = []
    for wc in warranty_claims:
        r = dict(wc)
        part = _resolve_parent_relationship(wc, "Car_Part__c", "Car_Part__r", car_parts)
        if part:
            r["Car_Part__r"] = {"id": part["id"], "part_name": part.get("part_name", "")}
        order = _resolve_parent_relationship(wc, "Order__c", "Order__r", orders)
        if order:
            r["Order__r"] = {"id": order["id"], "Name": order["Name"]}
        expanded.append(r)
    return jsonify(expanded)


@app.route('/api/soql', methods=['POST'])
def api_soql_query():
    """Simulate SOQL-style cross-object query.
    Supports parent-to-child and child-to-parent traversal patterns.
    Example queries:
      SELECT Name, Manufacturer__r.Name FROM Car_Part__c
      SELECT Name, (SELECT Name FROM Orders__r) FROM Car_Part__c
      SELECT Name, Car_Part__r.Name, Order__r.Name FROM Warranty_Claim__c
    """
    data = request.get_json()
    query = data.get("query", "") if data else ""
    if not query:
        return jsonify({"error": "No query provided"}), 400

    query_upper = query.upper()

    # Determine the FROM object
    from_object = None
    for obj_name in relationship_schema["objects"]:
        if obj_name.upper() in query_upper.split("FROM")[-1] if "FROM" in query_upper else "":
            from_object = obj_name
            break

    if not from_object:
        return jsonify({"error": "Could not determine FROM object", "supported_objects": list(relationship_schema["objects"].keys())}), 400

    # Route to appropriate data store
    store_map = {
        "Car_Part__c": car_parts,
        "Manufacturer__c": manufacturers,
        "Warehouse__c": warehouses,
        "Supplier__c": suppliers,
        "Order__c": orders,
        "Warranty_Claim__c": warranty_claims,
    }
    records = store_map.get(from_object, [])

    # Expand with relationships if __r is in the query
    results = []
    for rec in records:
        r = dict(rec)
        if "__r" in query:
            if from_object == "Car_Part__c":
                r = _expand_car_part(rec)
            elif from_object == "Order__c":
                part = _resolve_parent_relationship(rec, "Car_Part__c", "Car_Part__r", car_parts)
                if part:
                    r["Car_Part__r"] = part
                wh = _resolve_parent_relationship(rec, "Ship_From_Warehouse__c", "Ship_From_Warehouse__r", warehouses)
                if wh:
                    r["Ship_From_Warehouse__r"] = wh
            elif from_object == "Warranty_Claim__c":
                part = _resolve_parent_relationship(rec, "Car_Part__c", "Car_Part__r", car_parts)
                if part:
                    r["Car_Part__r"] = part
                order = _resolve_parent_relationship(rec, "Order__c", "Order__r", orders)
                if order:
                    r["Order__r"] = order
            elif from_object == "Manufacturer__c":
                sup = _resolve_parent_relationship(rec, "Primary_Supplier__c", "Primary_Supplier__r", suppliers)
                if sup:
                    r["Primary_Supplier__r"] = sup
                r["Car_Parts__r"] = {"totalSize": len(_resolve_child_relationships(rec["id"], car_parts, "Manufacturer__c")), "records": _resolve_child_relationships(rec["id"], car_parts, "Manufacturer__c")}
        results.append(r)

    return jsonify({
        "totalSize": len(results),
        "done": True,
        "records": results,
        "query": query,
        "from_object": from_object,
    })


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
    print(f"    GET  /api/dropdown-fields            - All dropdown definitions")
    print(f"    GET  /api/sub-categories/<cat>       - Sub-categories for category")
    print(f"    GET  /api/car-parts                  - List all parts")
    print(f"    POST /api/car-parts                  - Create part")
    print(f"    GET  /api/car-parts/<id>             - Get single part")
    print(f"    PUT  /api/car-parts/<id>             - Update part")
    print(f"    DEL  /api/car-parts/<id>             - Delete part")
    print(f"    GET  /api/car-parts/<id>/related     - Part with all relationships")
    print(f"    GET  /api/relationship-schema        - Full sObject schema")
    print(f"    GET  /api/relationships/<object>     - Object relationship map")
    print(f"    GET  /api/manufacturers              - All manufacturers")
    print(f"    GET  /api/manufacturers/<id>         - Manufacturer + car parts")
    print(f"    GET  /api/warehouses                 - All warehouses")
    print(f"    GET  /api/warehouses/<id>            - Warehouse + car parts + orders")
    print(f"    GET  /api/suppliers                  - All suppliers")
    print(f"    GET  /api/suppliers/<id>             - Supplier + manufacturers")
    print(f"    GET  /api/orders                     - All orders (with __r)")
    print(f"    GET  /api/orders/<id>                - Order + relationships")
    print(f"    GET  /api/warranty-claims            - All warranty claims")
    print(f"    POST /api/soql                       - SOQL-style cross-object query")
    print(f"    GET  /api/test-data                  - Test data JSON")
    print("\n" + "=" * 60 + "\n")
    app.run(host='0.0.0.0', port=5555, debug=False)
