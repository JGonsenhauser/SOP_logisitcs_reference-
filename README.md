# Logistics SOP Reference App

A customer SOP (Standard Operating Procedure) reference system for delivery drivers. Drivers search a customer by name and instantly get the full delivery requirements — drop-off location, PPE, truck type, time windows, who to call, gate codes, photo/signature rules, and more.

## Quick Start (Local)

```bash
cd sop_app
python run.py
```

- **Admin Dashboard:** http://localhost:8000 — PIN: `admin2026`
- **Driver Lookup:** http://localhost:8000/driver

Test driver logins (seeded):
| Driver  | ID | PIN  |
|---------|----|------|
| Marcus  | 1  | 1234 |
| Elena   | 2  | 5678 |
| James   | 3  | 9012 |

## Requirements

- Python 3.10+
- No external packages (stdlib only: `http.server`, `sqlite3`, `json`)

## What It Does

**Admin side** — Add customers, then click "Edit SOP" to fill in their delivery requirements across 9 categories:

1. Delivery Location & Access (drop-off spot, gate codes, parking)
2. Vehicle & Equipment (truck type, liftgate, pallet jack)
3. Safety & PPE (hard hat, vest, steel toes, hazmat)
4. Scheduling & Time Windows (delivery windows, appointments, blackout times)
5. Proof of Delivery (signatures, photos, BOL)
6. Special Handling (temperature, fragile, controlled substances)
7. Contacts & Escalation (receiving, after-hours, security)
8. Dock & Unloading Procedures (dock number, unloading method, detention)
9. General Notes & Warnings (alerts, recurring issues)

**Driver side** — Login with ID + PIN, type a customer name, tap to see all their requirements organized in expandable cards. Tap-to-reveal for sensitive codes, one-tap phone calls, navigate button.

## Deploy to Render (Free)

1. Push this repo to GitHub
2. Go to [render.com](https://render.com) → New → Web Service
3. Connect your GitHub repo
4. Render auto-detects `render.yaml` — confirm settings
5. Click Deploy

The app will be live at `https://sop-logistics-reference.onrender.com` (or similar).

Note: Render free tier spins down after 15 min of inactivity. First request after sleep takes ~30 seconds.

## Project Structure

```
sop_app/
├── run.py                  # Entry point
├── render.yaml             # Render deployment config
├── requirements.txt        # (empty - no dependencies)
├── backend/
│   ├── database.py         # Schema + SOP category definitions
│   ├── seed_data.py        # 10 sample customers with SOPs
│   └── app.py              # HTTP server + API routes
├── frontend/
│   ├── admin.html          # Admin dashboard (SPA)
│   └── driver.html         # Driver lookup (mobile-first SPA)
└── data/
    └── sop_app.db          # SQLite database (auto-created)
```
