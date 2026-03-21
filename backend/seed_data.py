"""
SOP App - Seed Data
Creates drivers + 10 diverse customers with rich SOP requirements.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from database import get_db, hash_pin, init_db


def seed():
    init_db()
    conn = get_db()

    # Skip if already seeded
    if conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0] > 0:
        print("Database already seeded.")
        conn.close()
        return

    # ── DRIVERS ──
    drivers = [
        ("Marcus", "Johnson", "512-555-0101", "marcus@example.com", "1234"),
        ("Elena", "Rodriguez", "512-555-0102", "elena@example.com", "5678"),
        ("James", "Mitchell", "210-555-0103", "james@example.com", "9012"),
    ]
    for fn, ln, ph, em, pin in drivers:
        conn.execute("INSERT INTO drivers (first_name, last_name, phone, email, pin_hash) VALUES (?,?,?,?,?)",
                     (fn, ln, ph, em, hash_pin(pin)))

    # ── CUSTOMERS ──
    customers = [
        {
            "company_name": "Henderson Family Residence",
            "customer_type": "residential",
            "address_line1": "4821 Oak Hollow Dr",
            "city": "Austin", "state": "TX", "zip_code": "78749",
            "primary_contact_name": "Sarah Henderson",
            "primary_contact_phone": "512-555-1001",
            "primary_contact_email": "sarah.h@email.com",
            "sop": {
                "delivery_location": {
                    "drop_off_location": "Front porch - left side of door. Ring doorbell after placing.",
                    "gate_code": "4821#",
                    "access_instructions": "Gated community. Use call box or gate code. House is 3rd on the right after gate.",
                    "parking_instructions": "Park on street, do not block driveway."
                },
                "vehicle_equipment": {
                    "truck_type": "Sprinter van",
                    "vehicle_size_restriction": "No trucks over 26ft - HOA restriction. Street is narrow with parked cars."
                },
                "safety_ppe": {},
                "proof_of_delivery": {
                    "photo_required": "Yes",
                    "photo_instructions": "Photo of package at front door with house number visible.",
                    "signature_required": "No"
                },
                "handling_special": {
                    "fragile": "Yes",
                },
                "customer_notes": {
                    "warnings": "Two large dogs in backyard - DO NOT open back gate. Dogs are friendly but will run out.",
                    "preferred_communication": "Text",
                    "special_notes": "If no one home, leave at front porch. Text photo to Sarah at 512-555-1001."
                }
            }
        },
        {
            "company_name": "Pinnacle Tech Solutions",
            "customer_type": "commercial",
            "address_line1": "300 W 6th Street, Suite 1200",
            "city": "Austin", "state": "TX", "zip_code": "78701",
            "primary_contact_name": "David Chen",
            "primary_contact_phone": "512-555-2001",
            "primary_contact_email": "dchen@pinnacletech.com",
            "sop": {
                "delivery_location": {
                    "delivery_address": "300 W 6th Street, Suite 1200, Austin TX 78701",
                    "drop_off_location": "12th floor, Suite 1200 reception desk. Do NOT leave in lobby.",
                    "access_instructions": "Check in at main lobby security desk. They will issue a visitor badge. Take elevator to 12th floor.",
                    "parking_instructions": "Use loading zone on 3rd Street side of building. 15-min limit. If full, use parking garage Level B1.",
                    "elevator_freight_info": "Freight elevator on east side of lobby. Key from security desk required."
                },
                "vehicle_equipment": {
                    "hand_truck_required": "Yes",
                    "equipment_notes": "Freight elevator fits standard hand truck. Max 500lb capacity."
                },
                "safety_ppe": {
                    "security_checkin": "Yes",
                    "id_verification": "Yes",
                },
                "delivery_window": {
                    "delivery_window_start": "09:00",
                    "delivery_window_end": "16:00",
                    "facility_hours": "Mon-Fri 8am-6pm. Building locked on weekends.",
                    "blackout_times": "No deliveries 12pm-1pm (lobby congestion during lunch)"
                },
                "proof_of_delivery": {
                    "signature_required": "Yes",
                    "signature_type": "Specific person",
                    "signature_person_name": "David Chen or Maria Santos (Office Manager)",
                    "photo_required": "No"
                },
                "contacts": {
                    "receiving_contact": "Maria Santos",
                    "receiving_phone": "512-555-2002",
                    "on_site_security_phone": "512-555-2099"
                },
                "customer_notes": {
                    "preferred_communication": "Call",
                    "special_notes": "High-value IT equipment. Call David 10 min before arrival."
                }
            }
        },
        {
            "company_name": "Gulf Coast Distribution Center",
            "customer_type": "warehouse",
            "address_line1": "8900 Industrial Blvd",
            "city": "San Antonio", "state": "TX", "zip_code": "78224",
            "primary_contact_name": "Mike Torres",
            "primary_contact_phone": "210-555-3001",
            "primary_contact_email": "mtorres@gulfcoastdist.com",
            "sop": {
                "delivery_location": {
                    "drop_off_location": "Dock 7 or 8 (assigned at guard shack)",
                    "access_instructions": "Enter through main gate off Industrial Blvd. Stop at guard shack for dock assignment. CB Channel 14 for yard communication.",
                    "parking_instructions": "Follow painted arrows in yard. Back into assigned dock. Yard jockey available if needed - radio Channel 14."
                },
                "vehicle_equipment": {
                    "truck_type": "Semi/Tractor-trailer",
                    "pallet_jack_required": "Yes",
                    "equipment_notes": "Electric pallet jacks available on-site if needed. Ask dock supervisor."
                },
                "safety_ppe": {
                    "hard_hat": "Yes",
                    "safety_vest": "Yes",
                    "steel_toe_boots": "Yes",
                    "safety_orientation": "First-time drivers must watch 5-min safety video at guard shack. Badge issued after."
                },
                "delivery_window": {
                    "delivery_window_start": "05:00",
                    "delivery_window_end": "20:00",
                    "appointment_required": "Yes",
                    "appointment_instructions": "Appointments scheduled through dispatch. Reference PO number at guard shack.",
                    "facility_hours": "24/7 but receiving only 5am-8pm"
                },
                "proof_of_delivery": {
                    "signature_required": "Yes",
                    "signature_type": "Receiving clerk",
                    "bol_required": "Yes",
                    "pod_scan_required": "Yes"
                },
                "dock_procedures": {
                    "dock_number": "Docks 1-12 (assigned at check-in)",
                    "dock_procedure": "Stop at guard shack. Show BOL and PO#. Get dock assignment. Pull to dock. Chock wheels. Open doors. Wait for dock crew.",
                    "unloading_method": "Customer unloads",
                    "lumper_service": "Yes",
                    "detention_policy": "Free 2 hours. $75/hr after. Clock starts at check-in.",
                    "pallet_exchange": "Yes"
                },
                "contacts": {
                    "receiving_contact": "Mike Torres - Dock Supervisor",
                    "receiving_phone": "210-555-3001",
                    "after_hours_contact": "Night Security",
                    "after_hours_phone": "210-555-3099",
                    "escalation_contact": "Regional Manager - Tom Bradley",
                    "escalation_phone": "210-555-3050"
                },
                "customer_notes": {
                    "preferred_communication": "Radio/CB",
                    "recurring_issues": "Dock 3 door sticks - may need to use adjacent dock. Yard floods in heavy rain near docks 10-12.",
                    "special_notes": "FIFO rotation required. Oldest product to front of stack."
                }
            }
        },
        {
            "company_name": "Fresh Mart Grocery #127",
            "customer_type": "retail",
            "address_line1": "1250 S Lamar Blvd",
            "city": "Austin", "state": "TX", "zip_code": "78704",
            "primary_contact_name": "Angela Price",
            "primary_contact_phone": "512-555-4001",
            "primary_contact_email": "store127@freshmart.com",
            "sop": {
                "delivery_location": {
                    "drop_off_location": "Rear loading dock. Access from alley behind building.",
                    "access_instructions": "Enter alley from South Lamar. Dock is behind store, single bay. Ring buzzer and wait.",
                    "parking_instructions": "Tight alley - 40ft max truck length. If dock occupied, park on street and wait. Do not double-park."
                },
                "vehicle_equipment": {
                    "truck_type": "Refrigerated",
                    "liftgate_required": "Yes",
                    "hand_truck_required": "Yes",
                    "vehicle_size_restriction": "40ft max due to alley turn radius"
                },
                "safety_ppe": {},
                "delivery_window": {
                    "delivery_window_start": "05:00",
                    "delivery_window_end": "07:00",
                    "blackout_times": "Absolutely no deliveries after 7am - store opens at 7am and dock area becomes customer parking.",
                    "facility_hours": "Store: 7am-10pm. Receiving: 5am-7am ONLY."
                },
                "proof_of_delivery": {
                    "signature_required": "Yes",
                    "signature_type": "Manager only",
                    "photo_required": "Yes",
                    "photo_instructions": "Photo of product staged in cooler/freezer showing temperature display."
                },
                "handling_special": {
                    "temperature_controlled": "Yes",
                    "temp_min_f": "33",
                    "temp_max_f": "40",
                    "stacking_instructions": "Dairy on bottom, produce on top. Never stack over 4 high. Rotate stock - FIFO."
                },
                "dock_procedures": {
                    "unloading_method": "Driver unloads",
                    "return_procedure": "Damaged or expired product: set aside, photograph, note on BOL. Manager signs damage report."
                },
                "contacts": {
                    "receiving_contact": "Angela Price (Morning Manager)",
                    "receiving_phone": "512-555-4001",
                    "escalation_contact": "District Manager - Robert Kim",
                    "escalation_phone": "512-555-4050"
                },
                "customer_notes": {
                    "preferred_communication": "Call",
                    "warnings": "Alley has a sharp 90-degree turn. Low clearance (11ft) at alley entrance. Watch for dumpster placement.",
                    "recurring_issues": "Buzzer sometimes doesn't work. If no answer in 2 min, call Angela directly.",
                    "special_notes": "Temperature log REQUIRED. Record trailer temp on arrival. If above 40F, call Angela before unloading."
                }
            }
        },
        {
            "company_name": "Rio Grande Steakhouse",
            "customer_type": "restaurant",
            "address_line1": "455 E Commerce St",
            "city": "San Antonio", "state": "TX", "zip_code": "78205",
            "primary_contact_name": "Chef Carlos Mendez",
            "primary_contact_phone": "210-555-5001",
            "primary_contact_email": "carlos@riograndesteakhouse.com",
            "sop": {
                "delivery_location": {
                    "drop_off_location": "Kitchen back door. Walk-in cooler is immediately to the left inside.",
                    "lock_code": "5501",
                    "access_instructions": "Back entrance off alley. Door may be propped open during early hours. If locked, use code 5501 on keypad.",
                    "parking_instructions": "Very limited. Use the 15-min loading zone on Commerce St or the alley. NEVER block the neighboring bar entrance."
                },
                "vehicle_equipment": {
                    "truck_type": "Refrigerated",
                    "hand_truck_required": "Yes"
                },
                "delivery_window": {
                    "delivery_window_start": "06:00",
                    "delivery_window_end": "11:00",
                    "blackout_times": "No deliveries after 11am. Kitchen goes into lunch prep and cannot accept.",
                    "facility_hours": "Kitchen active 6am-midnight. Receiving 6am-11am."
                },
                "proof_of_delivery": {
                    "signature_required": "Yes",
                    "signature_type": "Specific person",
                    "signature_person_name": "Chef Carlos or Sous Chef Maria"
                },
                "handling_special": {
                    "temperature_controlled": "Yes",
                    "temp_min_f": "28",
                    "temp_max_f": "38",
                    "inside_delivery": "Yes",
                    "stacking_instructions": "Place meats directly in walk-in cooler. Produce on the rack by back door. NEVER put anything on floor."
                },
                "contacts": {
                    "receiving_contact": "Carlos Mendez",
                    "receiving_phone": "210-555-5001",
                    "after_hours_contact": "Bar Manager - Jenny",
                    "after_hours_phone": "210-555-5002"
                },
                "customer_notes": {
                    "preferred_communication": "Call",
                    "warnings": "Kitchen floor is slippery. Watch your step. Staff is very busy during prep - be patient.",
                    "recurring_issues": "Walk-in cooler door handle sticks. Pull hard and lift slightly.",
                    "special_notes": "Check all product dates. Carlos will reject anything within 3 days of expiration."
                }
            }
        },
        {
            "company_name": "Austin Regional Medical Center",
            "customer_type": "medical",
            "address_line1": "7800 N MoPac Expy",
            "city": "Austin", "state": "TX", "zip_code": "78759",
            "primary_contact_name": "Patricia Nguyen",
            "primary_contact_phone": "512-555-6001",
            "primary_contact_email": "pnguyen@austinregionalmed.org",
            "sop": {
                "delivery_location": {
                    "drop_off_location": "Loading Dock B - Medical Supply Receiving",
                    "access_instructions": "Enter hospital campus from MoPac service road. Follow signs to 'Loading/Receiving'. Dock B is on the north side. Check in with receiving clerk.",
                    "parking_instructions": "Dock staging area only. Do NOT park in patient or emergency zones. Will be towed."
                },
                "vehicle_equipment": {
                    "truck_type": "Box truck",
                    "hand_truck_required": "Yes"
                },
                "safety_ppe": {
                    "gloves_required": "Yes",
                    "hazmat_flag": "Yes",
                    "hazmat_class": "Class 6.2 Infectious Substances (occasional). Check BOL for hazmat indicators.",
                    "id_verification": "Yes",
                    "background_check": "Yes",
                    "safety_orientation": "First delivery requires 15-min orientation at Security office (Building A, Room 102). Bring valid ID."
                },
                "delivery_window": {
                    "delivery_window_start": "07:00",
                    "delivery_window_end": "15:00",
                    "appointment_required": "Yes",
                    "appointment_instructions": "Must have pre-scheduled delivery window. Reference PO number. Call Patricia 30 min before arrival."
                },
                "proof_of_delivery": {
                    "signature_required": "Yes",
                    "signature_type": "Specific person",
                    "signature_person_name": "Patricia Nguyen or authorized receiving clerk (see badge)",
                    "bol_required": "Yes",
                    "pod_scan_required": "Yes"
                },
                "handling_special": {
                    "temperature_controlled": "Yes",
                    "temp_min_f": "36",
                    "temp_max_f": "46",
                    "chain_of_custody": "Yes",
                    "controlled_substance": "Yes",
                },
                "contacts": {
                    "receiving_contact": "Patricia Nguyen - Supply Chain Mgr",
                    "receiving_phone": "512-555-6001",
                    "on_site_security_phone": "512-555-6099",
                    "escalation_contact": "Director of Operations - Dr. James Park",
                    "escalation_phone": "512-555-6050"
                },
                "customer_notes": {
                    "preferred_communication": "Call",
                    "warnings": "Hospital campus - obey all speed limits (10mph). Emergency vehicles have absolute right-of-way.",
                    "special_notes": "Controlled substances require chain-of-custody documentation. Do NOT leave packages unattended at any time."
                }
            }
        },
        {
            "company_name": "Mueller Development Group",
            "customer_type": "construction",
            "address_line1": "4500 Mueller Blvd",
            "city": "Austin", "state": "TX", "zip_code": "78723",
            "primary_contact_name": "Tony Ramirez",
            "primary_contact_phone": "512-555-7001",
            "primary_contact_email": "tramirez@muellerdev.com",
            "sop": {
                "delivery_location": {
                    "drop_off_location": "Phase 3 staging area - follow orange cones from main gate. Look for the blue container marked 'RECEIVING'.",
                    "access_instructions": "Active construction site. Stop at gate, sign in with security. Get a visitor hardhat if you don't have one.",
                    "parking_instructions": "Pull into staging area as directed by ground crew. Stay on gravel paths. Do NOT drive on grass or unpaved areas."
                },
                "vehicle_equipment": {
                    "truck_type": "Flatbed",
                    "liftgate_required": "No",
                    "pallet_jack_required": "No",
                    "equipment_notes": "On-site forklift and crane available. Coordinate with Tony for heavy lifts."
                },
                "safety_ppe": {
                    "hard_hat": "Yes",
                    "safety_vest": "Yes",
                    "steel_toe_boots": "Yes",
                    "safety_glasses": "Yes",
                    "security_checkin": "Yes",
                    "safety_orientation": "OSHA 10-hour card required for repeat drivers. First visit: sign liability waiver at gate."
                },
                "delivery_window": {
                    "delivery_window_start": "07:00",
                    "delivery_window_end": "15:00",
                    "facility_hours": "Mon-Sat 6am-6pm. No Sunday deliveries.",
                    "blackout_times": "Concrete pours block access periodically - call ahead to confirm."
                },
                "proof_of_delivery": {
                    "signature_required": "Yes",
                    "signature_type": "Specific person",
                    "signature_person_name": "Tony Ramirez (Site Foreman) or designated lead",
                    "photo_required": "Yes",
                    "photo_instructions": "Photo of material on ground at staging area. Include any visible damage."
                },
                "handling_special": {
                    "two_person_required": "Yes",
                },
                "dock_procedures": {
                    "unloading_method": "Shared / Lumper",
                },
                "contacts": {
                    "receiving_contact": "Tony Ramirez - Foreman",
                    "receiving_phone": "512-555-7001",
                    "escalation_contact": "Project Manager - Lisa Chang",
                    "escalation_phone": "512-555-7050",
                    "on_site_security_phone": "512-555-7099"
                },
                "customer_notes": {
                    "preferred_communication": "Call",
                    "warnings": "Active construction zone. Moving heavy equipment. Stay in vehicle until directed by ground crew. Watch for overhead cranes.",
                    "recurring_issues": "Site entrance changes frequently as phases complete. Call Tony morning-of for current access point.",
                    "special_notes": "Material must match PO exactly. Tony will count and inspect on the spot. Short shipments will be noted on BOL."
                }
            }
        },
        {
            "company_name": "Westlake Academy",
            "customer_type": "school",
            "address_line1": "2700 Bee Cave Road",
            "city": "West Lake Hills", "state": "TX", "zip_code": "78746",
            "primary_contact_name": "Jennifer Walsh",
            "primary_contact_phone": "512-555-8001",
            "primary_contact_email": "jwalsh@westlakeacademy.edu",
            "sop": {
                "delivery_location": {
                    "drop_off_location": "Cafeteria loading area - rear of Building C",
                    "access_instructions": "Use service entrance off Bee Cave Road (east side). Do not use main student entrance. Buzz intercom at service gate.",
                    "parking_instructions": "Service lane only. NEVER block fire lanes. Strictly enforced."
                },
                "vehicle_equipment": {
                    "truck_type": "Box truck",
                    "vehicle_size_restriction": "26ft max. Tight turn at service entrance."
                },
                "safety_ppe": {
                    "id_verification": "Yes",
                    "background_check": "Yes",
                },
                "delivery_window": {
                    "delivery_window_start": "06:00",
                    "delivery_window_end": "07:30",
                    "blackout_times": "No deliveries 7:30am-3:30pm (school hours). Second window 3:30pm-4:30pm available by appointment.",
                    "facility_hours": "Admin office: Mon-Fri 7am-5pm. Summer hours vary - call ahead."
                },
                "proof_of_delivery": {
                    "signature_required": "Yes",
                    "signature_type": "Specific person",
                    "signature_person_name": "Jennifer Walsh (Facilities) or cafeteria manager on duty"
                },
                "handling_special": {
                    "temperature_controlled": "Yes",
                    "temp_min_f": "33",
                    "temp_max_f": "41",
                },
                "contacts": {
                    "receiving_contact": "Jennifer Walsh",
                    "receiving_phone": "512-555-8001",
                    "after_hours_contact": "School Security",
                    "after_hours_phone": "512-555-8099"
                },
                "customer_notes": {
                    "preferred_communication": "Email",
                    "warnings": "SCHOOL ZONE. 20mph speed limit on campus. Children present during school hours. Zero tolerance.",
                    "special_notes": "Background check on file required for all regular drivers. First-time drivers must present ID to front office before delivery."
                }
            }
        },
        {
            "company_name": "MedRx Pharmacy #42",
            "customer_type": "pharmacy",
            "address_line1": "1800 W Ben White Blvd",
            "city": "Austin", "state": "TX", "zip_code": "78704",
            "primary_contact_name": "Dr. Amy Patel",
            "primary_contact_phone": "512-555-9001",
            "primary_contact_email": "apatel@medrx42.com",
            "sop": {
                "delivery_location": {
                    "drop_off_location": "Pharmacy back entrance (NOT the retail store entrance). Marked 'Pharmacy Receiving'.",
                    "lock_code": "9042",
                    "access_instructions": "Rear of building. If door locked, enter code 9042 on keypad to buzz staff. Wait for staff to open - do NOT enter unescorted.",
                    "parking_instructions": "Two designated pharmacy delivery spots behind building."
                },
                "vehicle_equipment": {
                    "truck_type": "Sprinter van"
                },
                "safety_ppe": {
                    "id_verification": "Yes",
                    "gloves_required": "Yes",
                },
                "delivery_window": {
                    "delivery_window_start": "08:00",
                    "delivery_window_end": "17:00",
                    "appointment_required": "Yes",
                    "appointment_instructions": "Controlled substance deliveries MUST be pre-scheduled. Call Dr. Patel at least 24hrs in advance."
                },
                "proof_of_delivery": {
                    "signature_required": "Yes",
                    "signature_type": "Pharmacist only",
                    "signature_person_name": "Dr. Amy Patel, RPh or designated pharmacist on duty",
                    "bol_required": "Yes"
                },
                "handling_special": {
                    "controlled_substance": "Yes",
                    "chain_of_custody": "Yes",
                    "temperature_controlled": "Yes",
                    "temp_min_f": "59",
                    "temp_max_f": "77",
                },
                "contacts": {
                    "receiving_contact": "Dr. Amy Patel",
                    "receiving_phone": "512-555-9001",
                    "escalation_contact": "MedRx Regional Compliance - Sarah Kim",
                    "escalation_phone": "800-555-9099"
                },
                "customer_notes": {
                    "preferred_communication": "Call",
                    "warnings": "DEA Schedule II-V substances. Federal chain-of-custody rules apply. NEVER leave controlled packages unattended. Never hand to non-pharmacist staff.",
                    "special_notes": "Count verification required on delivery. Pharmacist will count in your presence. Any discrepancy = immediate escalation to compliance."
                }
            }
        },
        {
            "company_name": "Lakeview Event Center",
            "customer_type": "event_venue",
            "address_line1": "1200 Lakeshore Dr",
            "city": "Austin", "state": "TX", "zip_code": "78741",
            "primary_contact_name": "Brian Thompson",
            "primary_contact_phone": "512-555-0201",
            "primary_contact_email": "brian@lakeviewevents.com",
            "sop": {
                "delivery_location": {
                    "drop_off_location": "Service entrance - north side. Loading dock shared with catering. Coordinate if event setup in progress.",
                    "gate_code": "1200*",
                    "access_instructions": "Service gate on north side of property (Lakeshore Dr past main entrance). Use gate code. Follow signs to loading dock.",
                    "parking_instructions": "Loading dock area. On event days, dock may be congested - call Brian for staging instructions."
                },
                "vehicle_equipment": {
                    "truck_type": "Box truck",
                    "liftgate_required": "Yes",
                    "hand_truck_required": "Yes",
                    "equipment_notes": "Venue has two hand trucks and a flat cart available for use."
                },
                "delivery_window": {
                    "appointment_required": "Yes",
                    "appointment_instructions": "ALWAYS call day before to confirm delivery time. Schedule depends on event calendar. Event days are hectic - early delivery preferred.",
                    "facility_hours": "Variable. Based on event schedule. Office hours Tue-Sat 9am-5pm."
                },
                "proof_of_delivery": {
                    "signature_required": "Yes",
                    "signature_type": "Anyone",
                    "photo_required": "Yes",
                    "photo_instructions": "Photo of product staged at delivery location. If equipment rental, photo of each piece."
                },
                "handling_special": {
                    "inside_delivery": "Yes",
                    "white_glove": "Yes",
                    "fragile": "Yes",
                    "two_person_required": "Yes",
                },
                "dock_procedures": {
                    "unloading_method": "Shared / Lumper",
                    "dock_procedure": "Shared dock with catering vendors. Coordinate with Brian. If event setup is active, delivery may need to wait or use alternate entrance."
                },
                "contacts": {
                    "receiving_contact": "Brian Thompson - Events Manager",
                    "receiving_phone": "512-555-0201",
                    "after_hours_contact": "Venue Security",
                    "after_hours_phone": "512-555-0299"
                },
                "customer_notes": {
                    "preferred_communication": "Text",
                    "recurring_issues": "Event days are unpredictable. Dock access may shift. Always confirm same-day.",
                    "special_notes": "White glove treatment for AV equipment and decor rentals. Handle with extreme care. Brian will direct placement location inside venue."
                }
            }
        },
    ]

    for cust in customers:
        sop = cust.pop("sop", {})
        c = conn.execute("""
            INSERT INTO customers (company_name, customer_type, address_line1, city, state, zip_code,
                primary_contact_name, primary_contact_phone, primary_contact_email)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, (
            cust["company_name"], cust["customer_type"], cust.get("address_line1"),
            cust.get("city"), cust.get("state"), cust.get("zip_code"),
            cust.get("primary_contact_name"), cust.get("primary_contact_phone"),
            cust.get("primary_contact_email")
        ))
        cid = c.lastrowid

        # Insert SOP requirements
        for category, fields in sop.items():
            for key, value in fields.items():
                if value:
                    conn.execute(
                        "INSERT INTO sop_requirements (customer_id, category, requirement_key, requirement_value) VALUES (?,?,?,?)",
                        (cid, category, key, str(value))
                    )

    conn.commit()
    conn.close()
    print(f"Seeded {len(customers)} customers with SOP requirements and {len(drivers)} drivers.")


if __name__ == "__main__":
    seed()
