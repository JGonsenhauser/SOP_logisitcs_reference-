"""
SOP App - Database layer
Customer SOP reference system for delivery drivers.
Flexible key-value requirements per customer so admins can add any SOP field.
"""
import os
import sqlite3
import hashlib

# ── DATA DIRECTORY ──
_LOCAL_DATA = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(_LOCAL_DATA, exist_ok=True)
DB_PATH = os.path.join(_LOCAL_DATA, "sop_app.db")


def hash_pin(pin):
    return hashlib.sha256(pin.encode()).hexdigest()


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


# ── SOP REQUIREMENT CATEGORIES ──
# This master list drives the admin form and driver display.
# Each category groups related requirements together.
SOP_CATEGORIES = {
    "delivery_location": {
        "label": "Delivery Location & Access",
        "icon": "📍",
        "fields": {
            "delivery_address":        {"label": "Delivery Address",        "type": "text"},
            "drop_off_location":       {"label": "Drop-Off Location",       "type": "text",     "hint": "e.g. Dock 3, Side entrance, Front desk, Warehouse Bay 7"},
            "gate_code":               {"label": "Gate Code",               "type": "text",     "sensitive": True},
            "lock_code":               {"label": "Lock/Door Code",          "type": "text",     "sensitive": True},
            "access_instructions":     {"label": "Access Instructions",     "type": "textarea", "hint": "Badge required? Check-in desk? Call on arrival?"},
            "parking_instructions":    {"label": "Parking Instructions",    "type": "textarea"},
            "elevator_freight_info":   {"label": "Elevator / Freight Info", "type": "text",     "hint": "Freight elevator location, max capacity, key needed?"},
        }
    },
    "vehicle_equipment": {
        "label": "Vehicle & Equipment",
        "icon": "🚛",
        "fields": {
            "truck_type":              {"label": "Required Truck Type",     "type": "select",   "options": ["Any", "Box truck", "Flatbed", "Refrigerated", "Liftgate required", "Semi/Tractor-trailer", "Sprinter van", "Pickup"]},
            "liftgate_required":       {"label": "Liftgate Required",       "type": "yesno"},
            "pallet_jack_required":    {"label": "Pallet Jack Required",    "type": "yesno"},
            "hand_truck_required":     {"label": "Hand Truck / Dolly Required", "type": "yesno"},
            "equipment_notes":         {"label": "Other Equipment Notes",   "type": "textarea"},
            "weight_limit_lbs":        {"label": "Max Weight (lbs)",        "type": "number"},
            "vehicle_size_restriction":{"label": "Vehicle Size Restriction","type": "text",     "hint": "e.g. No trucks over 26ft, low clearance 10ft"},
        }
    },
    "safety_ppe": {
        "label": "Safety & PPE",
        "icon": "🦺",
        "fields": {
            "hard_hat":                {"label": "Hard Hat Required",        "type": "yesno"},
            "safety_vest":             {"label": "Safety Vest Required",     "type": "yesno"},
            "steel_toe_boots":         {"label": "Steel Toe Boots Required", "type": "yesno"},
            "safety_glasses":          {"label": "Safety Glasses Required",  "type": "yesno"},
            "gloves_required":         {"label": "Gloves Required",          "type": "yesno"},
            "other_ppe":               {"label": "Other PPE",                "type": "text",     "hint": "e.g. Hearing protection, face mask, hair net"},
            "hazmat_flag":             {"label": "Hazmat Involved",          "type": "yesno"},
            "hazmat_class":            {"label": "Hazmat Class / Details",   "type": "text"},
            "security_checkin":        {"label": "Security Check-In Required","type": "yesno"},
            "id_verification":         {"label": "ID Verification Required", "type": "yesno"},
            "background_check":        {"label": "Background Check Required","type": "yesno"},
            "safety_orientation":      {"label": "Site Safety Orientation",  "type": "text",     "hint": "e.g. Must watch 10-min video at guard shack"},
        }
    },
    "delivery_window": {
        "label": "Scheduling & Time Windows",
        "icon": "🕐",
        "fields": {
            "delivery_window_start":   {"label": "Earliest Delivery Time",  "type": "time"},
            "delivery_window_end":     {"label": "Latest Delivery Time",    "type": "time"},
            "appointment_required":    {"label": "Appointment Required",    "type": "yesno"},
            "appointment_instructions":{"label": "Appointment Instructions","type": "textarea", "hint": "Who to call, how far in advance, reference number"},
            "facility_hours":          {"label": "Facility Hours",          "type": "text",     "hint": "e.g. Mon-Fri 6am-4pm, Closed weekends"},
            "blackout_times":          {"label": "Blackout / Restricted Times","type": "text",  "hint": "e.g. No deliveries 11am-1pm (lunch rush)"},
            "after_hours_procedure":   {"label": "After-Hours Procedure",   "type": "textarea"},
        }
    },
    "proof_of_delivery": {
        "label": "Proof of Delivery (POD)",
        "icon": "📋",
        "fields": {
            "signature_required":      {"label": "Signature Required",      "type": "yesno"},
            "signature_type":          {"label": "Who Must Sign",           "type": "select",   "options": ["Anyone", "Specific person", "Manager only", "Pharmacist only", "Receiving clerk"]},
            "signature_person_name":   {"label": "Required Signer Name",   "type": "text"},
            "photo_required":          {"label": "Photo Required",          "type": "yesno"},
            "photo_instructions":      {"label": "Photo Instructions",      "type": "textarea", "hint": "What to photograph: product at dock, label visible, etc."},
            "bol_required":            {"label": "BOL (Bill of Lading) Required","type": "yesno"},
            "pod_scan_required":       {"label": "Barcode / POD Scan",      "type": "yesno"},
            "pod_notes":               {"label": "Other POD Notes",         "type": "textarea"},
        }
    },
    "handling_special": {
        "label": "Special Handling",
        "icon": "⚠️",
        "fields": {
            "temperature_controlled":  {"label": "Temperature Controlled",  "type": "yesno"},
            "temp_min_f":              {"label": "Min Temp (°F)",           "type": "number"},
            "temp_max_f":              {"label": "Max Temp (°F)",           "type": "number"},
            "fragile":                 {"label": "Fragile / Handle With Care","type": "yesno"},
            "white_glove":             {"label": "White Glove Service",     "type": "yesno"},
            "inside_delivery":         {"label": "Inside Delivery Required","type": "yesno"},
            "assembly_required":       {"label": "Assembly / Setup Required","type": "yesno"},
            "stacking_instructions":   {"label": "Stacking / Placement",   "type": "textarea", "hint": "e.g. Do not stack over 3 high, place on pallet rack"},
            "two_person_required":     {"label": "Two-Person Lift Required","type": "yesno"},
            "controlled_substance":    {"label": "Controlled Substance",    "type": "yesno"},
            "chain_of_custody":        {"label": "Chain of Custody Required","type": "yesno"},
        }
    },
    "contacts": {
        "label": "Contacts & Escalation",
        "icon": "📞",
        "fields": {
            "receiving_contact":       {"label": "Receiving Contact Name",  "type": "text"},
            "receiving_phone":         {"label": "Receiving Contact Phone", "type": "text"},
            "after_hours_contact":     {"label": "After-Hours Contact Name","type": "text"},
            "after_hours_phone":       {"label": "After-Hours Phone",       "type": "text"},
            "escalation_contact":      {"label": "Escalation Contact",      "type": "text"},
            "escalation_phone":        {"label": "Escalation Phone",        "type": "text"},
            "on_site_security_phone":  {"label": "On-Site Security Phone",  "type": "text"},
            "dispatcher_notes":        {"label": "Dispatcher Notes",        "type": "textarea"},
        }
    },
    "dock_procedures": {
        "label": "Dock & Unloading Procedures",
        "icon": "🏗️",
        "fields": {
            "dock_number":             {"label": "Dock / Bay Number",       "type": "text"},
            "dock_procedure":          {"label": "Dock Check-In Procedure", "type": "textarea", "hint": "CB channel, call button, guard shack, etc."},
            "unloading_method":        {"label": "Unloading Method",        "type": "select",   "options": ["Driver unloads", "Customer unloads", "Shared / Lumper", "Forklift on-site", "Drop trailer"]},
            "lumper_service":          {"label": "Lumper Service Available", "type": "yesno"},
            "detention_policy":        {"label": "Detention Policy",        "type": "text",     "hint": "e.g. Free 2 hrs, $50/hr after"},
            "return_procedure":        {"label": "Returns / Rejection Procedure","type": "textarea"},
            "pallet_exchange":         {"label": "Pallet Exchange Required","type": "yesno"},
        }
    },
    "customer_notes": {
        "label": "General Notes & Warnings",
        "icon": "📝",
        "fields": {
            "special_notes":           {"label": "Special Notes",           "type": "textarea"},
            "warnings":                {"label": "Warnings / Alerts",       "type": "textarea", "hint": "Dogs, low clearance, flood zone, construction, hostile area"},
            "preferred_communication": {"label": "Preferred Communication", "type": "select",   "options": ["Call", "Text", "Email", "Radio/CB", "In-person only"]},
            "language_preference":     {"label": "Language Preference",     "type": "text"},
            "recurring_issues":        {"label": "Recurring Issues",        "type": "textarea", "hint": "Known problems: dock always full, gate jams, etc."},
        }
    },
}


def init_db():
    conn = get_db()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS drivers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        phone TEXT,
        email TEXT,
        pin_hash TEXT NOT NULL,
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_name TEXT NOT NULL,
        customer_type TEXT NOT NULL DEFAULT 'commercial',
        address_line1 TEXT,
        address_line2 TEXT,
        city TEXT,
        state TEXT,
        zip_code TEXT,
        primary_contact_name TEXT,
        primary_contact_phone TEXT,
        primary_contact_email TEXT,
        after_hours_contact_name TEXT,
        after_hours_contact_phone TEXT,
        receiving_contact_name TEXT,
        receiving_contact_phone TEXT,
        notes TEXT,
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS sop_requirements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER NOT NULL,
        category TEXT NOT NULL,
        requirement_key TEXT NOT NULL,
        requirement_value TEXT NOT NULL,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
    );

    CREATE INDEX IF NOT EXISTS idx_sop_customer ON sop_requirements(customer_id);
    CREATE INDEX IF NOT EXISTS idx_sop_category ON sop_requirements(category);

    CREATE TABLE IF NOT EXISTS audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_type TEXT,
        user_id INTEGER,
        action TEXT,
        resource_type TEXT,
        resource_id INTEGER,
        details TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    conn.commit()
    conn.close()
    print("Database initialized.")


if __name__ == "__main__":
    init_db()
    print(f"Database at: {DB_PATH}")
