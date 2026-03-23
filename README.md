# Logistics SOP Reference App

A customer SOP (Standard Operating Procedure) reference system for delivery drivers. Drivers search a customer by name and instantly get the full delivery requirements — drop-off location, PPE, truck type, time windows, who to call, gate codes, photo/signature rules, and more.

**Installable as a mobile app** via Progressive Web App (PWA). Share a link via text or WhatsApp and drivers can add it to their home screen.

## Quick Start (Local)

```bash
pip install -r requirements.txt
python run.py
```

- **Admin Dashboard:** http://localhost:8000 — User ID: `1`, PIN: `admin2026`
- **Driver Lookup:** http://localhost:8000/driver
- **Install Page:** http://localhost:8000/install
- **API Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

Test driver logins (seeded):
| Driver  | ID | PIN  |
|---------|----|------|
| Marcus  | 2  | 1234 |
| Elena   | 3  | 5678 |
| James   | 4  | 9012 |

## Requirements

- Python 3.10+
- Dependencies: FastAPI, uvicorn, bcrypt, cryptography, pydantic, httpx

## Features

### Driver App (PWA)
- Mobile-first responsive design
- Installable on Android & iOS (Add to Home Screen)
- Offline support via service worker caching
- Search customers, view SOP requirements in expandable cards
- Tap-to-reveal for sensitive codes (auto-hides after 30s)
- One-tap phone calls and Google Maps navigation

### Admin Dashboard
- **Dashboard** — Key metrics + Chart.js visualizations (lookups trend, top customers, hourly activity)
- **Customer Management** — Full CRUD with SOP editor across 9 categories
- **Driver Management** — Create drivers and admins with bcrypt-hashed PINs
- **Driver Usage Report** — Per-driver lookups, unique customers, engagement levels
- **SOP Coverage Report** — Completion % per customer with progress bars
- **Security Monitor** — Failed logins, suspicious IPs, SOP access log
- **Audit Log** — Filterable by action/user type, CSV export, IP geolocation

### Security
- bcrypt PIN hashing (replaces SHA256)
- Database-persisted sessions with TTL (survives restarts)
- Rate limiting (5 failed logins per IP per 15 minutes)
- AES-256 field-level encryption for sensitive data (gate codes, lock codes)
- Security headers (X-Frame-Options, CSP, HSTS, etc.)
- Configurable CORS origins
- Individual admin accounts (no hardcoded PINs)
- IP geolocation on login via ip-api.com

### 9 SOP Categories
1. Delivery Location & Access (drop-off spot, gate codes, parking)
2. Vehicle & Equipment (truck type, liftgate, pallet jack)
3. Safety & PPE (hard hat, vest, steel toes, hazmat)
4. Scheduling & Time Windows (delivery windows, appointments, blackout times)
5. Proof of Delivery (signatures, photos, BOL)
6. Special Handling (temperature, fragile, controlled substances)
7. Contacts & Escalation (receiving, after-hours, security)
8. Dock & Unloading Procedures (dock number, unloading method, detention)
9. General Notes & Warnings (alerts, recurring issues)

## Deploy to Render

1. Push this repo to GitHub
2. Go to [render.com](https://render.com) → New → Web Service
3. Connect your GitHub repo
4. Render auto-detects `render.yaml` — confirm settings
5. Set `ALLOWED_ORIGINS` env var to your domain
6. Click Deploy

The app uses a persistent disk for the SQLite database, so data survives deploys.

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `PORT` | No | 8000 | Server port |
| `ENVIRONMENT` | No | development | `development` or `production` |
| `ENCRYPTION_KEY` | Prod | — | AES encryption key for sensitive fields |
| `SESSION_SECRET` | No | auto-generated | Session token entropy |
| `ALLOWED_ORIGINS` | Prod | `*` | Comma-separated CORS origins |
| `DB_PATH` | No | `data/sop_app.db` | SQLite database path |

## Project Structure

```
sop_app/
├── run.py                      # Entry point (uvicorn)
├── render.yaml                 # Render deployment config
├── requirements.txt            # Python dependencies
├── backend/
│   ├── app.py                  # FastAPI app, middleware, frontend routes
│   ├── config.py               # Environment-based settings
│   ├── database.py             # SQLite schema + SOP categories
│   ├── crypto.py               # AES field-level encryption
│   ├── migrations.py           # Database migration system
│   ├── backup.py               # SQLite backup utility
│   ├── seed_data.py            # 10 sample customers + drivers
│   ├── routes/
│   │   ├── auth.py             # Login endpoints + geolocation
│   │   ├── driver.py           # Driver search & SOP view
│   │   ├── admin.py            # CRUD, dashboard, analytics, audit
│   │   └── schema.py           # SOP schema endpoint
│   ├── middleware/
│   │   ├── auth.py             # Session validation dependencies
│   │   └── security.py         # Rate limiting, security headers
│   └── models/
│       ├── requests.py         # Pydantic input validation
│       └── responses.py        # Pydantic response models
├── frontend/
│   ├── admin.html              # Admin dashboard (Chart.js, 7 pages)
│   ├── driver.html             # Driver lookup (PWA, mobile-first)
│   ├── install.html            # PWA install landing page
│   ├── manifest.json           # PWA manifest
│   ├── sw.js                   # Service worker
│   └── icons/                  # App icons (SVG)
└── data/
    ├── sop_app.db              # SQLite database (auto-created)
    └── backups/                # Automatic backups
```

## API Endpoints

### Public
- `GET /api/sop-schema` — SOP category definitions
- `GET /health` — Health check with uptime and DB status

### Driver (requires session)
- `POST /api/driver/login` — `{driver_id, pin}`
- `GET /api/driver/search?q=` — Search customers
- `GET /api/driver/customer/{id}/sop` — View SOP

### Admin (requires admin session)
- `POST /api/admin/login` — `{user_id, pin}`
- `GET /api/admin/dashboard` — Stats + activity
- CRUD: `GET/POST/PUT/DELETE /api/admin/customers`
- SOP: `GET/PUT /api/admin/customers/{id}/sop`
- `GET/POST /api/admin/drivers`
- `GET /api/admin/audit` — Filterable audit log
- `GET /api/admin/analytics/*` — Charts data
- `POST /api/admin/backup` — Trigger backup

## Backup & Recovery

Backups are created automatically on production startup and can be triggered manually via the admin API. Up to 5 backups are retained with automatic rotation.

```bash
# Manual backup
python -c "import sys; sys.path.insert(0,'backend'); from backup import create_backup; create_backup()"
```
