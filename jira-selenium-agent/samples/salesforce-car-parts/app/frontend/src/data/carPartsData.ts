export interface CarPart {
  id: string;
  part_name: string;
  part_number: string;
  part_category: string;
  part_sub_category: string;
  manufacturer: string;
  condition: string;
  vehicle_make: string;
  year_range: string;
  unit_price: number;
  stock_quantity: number;
  availability: string;
  warehouse_location: string;
  quality_grade: string;
  shipping_class: string;
  warranty_type: string;
  currency: string;
  description: string;
}

export const dropdownFields: Record<string, string[]> = {
  part_category: [
    'Engine Components', 'Transmission & Drivetrain', 'Braking System',
    'Suspension & Steering', 'Electrical & Lighting', 'Exhaust System',
    'Body & Exterior', 'Interior & Comfort', 'Cooling System',
    'Fuel System', 'HVAC & Climate', 'Wheels & Tires'
  ],
  part_sub_category: [],
  manufacturer: [
    'Bosch', 'Denso', 'Brembo', 'BorgWarner', 'KYB', 'Hella', 'Continental',
    'Delphi', 'Valeo', 'NGK', 'Mahle', 'Gates', 'SKF', 'Moog', 'Monroe',
    'ACDelco', 'Motorcraft', 'Aisin', 'NTN', 'Timken', 'ZF', 'TRW', 'Sachs'
  ],
  condition: ['New', 'Refurbished', 'Used - Grade A', 'Used - Grade B', 'Used - Grade C', 'Salvage'],
  vehicle_make: [
    'Toyota', 'Honda', 'BMW', 'Mercedes-Benz', 'Tesla', 'Ford', 'Chevrolet',
    'Audi', 'Volkswagen', 'Hyundai', 'Kia', 'Nissan', 'Mazda', 'Subaru',
    'Lexus', 'Porsche', 'Volvo', 'Jaguar', 'Land Rover', 'Ferrari', 'Lamborghini'
  ],
  year_range: [
    '2024-2025', '2022-2023', '2020-2021', '2018-2019', '2015-2017',
    '2010-2014', '2005-2009', '2000-2004', 'Pre-2000', 'Universal'
  ],
  availability: [
    'In Stock', 'Low Stock', 'Out of Stock', 'Backordered',
    'Pre-Order', 'Discontinued', 'Special Order'
  ],
  warehouse_location: [
    'Main Warehouse - A1', 'Main Warehouse - B2', 'Main Warehouse - C3',
    'Secondary Warehouse - D1', 'Secondary Warehouse - E2',
    'Distribution Center - West', 'Distribution Center - East',
    'Overflow Storage - F1'
  ],
  quality_grade: ['OEM', 'OEM Equivalent', 'Premium Aftermarket', 'Standard Aftermarket', 'Economy', 'Performance'],
  shipping_class: ['Standard', 'Express', 'Overnight', 'Freight', 'Oversized', 'Hazardous Material'],
  warranty_type: [
    'Manufacturer Warranty', 'Extended Warranty', 'Limited Warranty',
    '90-Day Warranty', '1-Year Warranty', '2-Year Warranty', 'Lifetime Warranty', 'No Warranty'
  ],
  currency: ['USD', 'EUR', 'GBP', 'CAD', 'AUD', 'JPY']
};

export const subCategoryMap: Record<string, string[]> = {
  'Engine Components': ['Turbocharger', 'Piston', 'Crankshaft', 'Camshaft', 'Timing Belt', 'Oil Pump', 'Gasket Set', 'Engine Mount'],
  'Transmission & Drivetrain': ['Clutch Kit', 'Torque Converter', 'CV Joint', 'Drive Shaft', 'Differential', 'Transfer Case'],
  'Braking System': ['Brake Pad', 'Brake Rotor', 'Brake Caliper', 'Brake Line', 'Master Cylinder', 'ABS Sensor', 'Brake Kit'],
  'Suspension & Steering': ['Shock Absorber', 'Coilover Kit', 'Control Arm', 'Tie Rod', 'Ball Joint', 'Sway Bar Link', 'Power Steering Pump'],
  'Electrical & Lighting': ['Headlight', 'Tail Light', 'Alternator', 'Starter Motor', 'Battery', 'Wiring Harness', 'LED Headlight'],
  'Exhaust System': ['Catalytic Converter', 'Muffler', 'Exhaust Manifold', 'O2 Sensor', 'Exhaust Pipe'],
  'Body & Exterior': ['Bumper', 'Fender', 'Hood', 'Mirror', 'Grille', 'Door Handle'],
  'Interior & Comfort': ['Seat Cover', 'Floor Mat', 'Steering Wheel Cover', 'Dashboard Trim', 'Sun Visor'],
  'Cooling System': ['Radiator', 'Water Pump', 'Thermostat', 'Coolant Hose', 'Radiator Fan'],
  'Fuel System': ['Fuel Pump', 'Fuel Injector', 'Fuel Filter', 'Carburetor', 'Fuel Tank'],
  'HVAC & Climate': ['AC Compressor', 'Condenser', 'Evaporator', 'Blower Motor', 'Heater Core'],
  'Wheels & Tires': ['Alloy Wheel', 'Steel Wheel', 'Tire', 'Wheel Bearing', 'Lug Nut Set']
};

export const initialCarParts: CarPart[] = [
  {
    id: 'CP-001',
    part_name: 'Turbocharger Assembly',
    part_number: 'TB-ENG-2024-001',
    part_category: 'Engine Components',
    part_sub_category: 'Turbocharger',
    manufacturer: 'BorgWarner',
    condition: 'New',
    vehicle_make: 'BMW',
    year_range: '2022-2023',
    unit_price: 1250.00,
    stock_quantity: 15,
    availability: 'In Stock',
    warehouse_location: 'Main Warehouse - A1',
    quality_grade: 'OEM',
    shipping_class: 'Freight',
    warranty_type: 'Manufacturer Warranty',
    currency: 'USD',
    description: 'High-performance turbocharger for BMW 3-series engines'
  },
  {
    id: 'CP-002',
    part_name: 'Performance Brake Kit',
    part_number: 'BK-BRK-2024-002',
    part_category: 'Braking System',
    part_sub_category: 'Brake Kit',
    manufacturer: 'Brembo',
    condition: 'New',
    vehicle_make: 'Mercedes-Benz',
    year_range: '2020-2021',
    unit_price: 890.00,
    stock_quantity: 22,
    availability: 'In Stock',
    warehouse_location: 'Main Warehouse - B2',
    quality_grade: 'Premium Aftermarket',
    shipping_class: 'Oversized',
    warranty_type: '2-Year Warranty',
    currency: 'USD',
    description: 'Premium performance brake kit with cross-drilled rotors'
  },
  {
    id: 'CP-003',
    part_name: 'Coilover Suspension Kit',
    part_number: 'SK-SUS-2024-003',
    part_category: 'Suspension & Steering',
    part_sub_category: 'Coilover Kit',
    manufacturer: 'KYB',
    condition: 'New',
    vehicle_make: 'Honda',
    year_range: '2020-2021',
    unit_price: 675.00,
    stock_quantity: 8,
    availability: 'Low Stock',
    warehouse_location: 'Secondary Warehouse - D1',
    quality_grade: 'OEM Equivalent',
    shipping_class: 'Standard',
    warranty_type: '1-Year Warranty',
    currency: 'USD',
    description: 'Adjustable coilover kit for Honda Civic sport suspension'
  },
  {
    id: 'CP-004',
    part_name: 'LED Headlight Assembly',
    part_number: 'HL-ELC-2024-004',
    part_category: 'Electrical & Lighting',
    part_sub_category: 'LED Headlight',
    manufacturer: 'Hella',
    condition: 'New',
    vehicle_make: 'Tesla',
    year_range: '2024-2025',
    unit_price: 450.00,
    stock_quantity: 30,
    availability: 'In Stock',
    warehouse_location: 'Main Warehouse - C3',
    quality_grade: 'OEM',
    shipping_class: 'Standard',
    warranty_type: 'Manufacturer Warranty',
    currency: 'USD',
    description: 'OEM LED headlight assembly with adaptive beam pattern'
  }
];
