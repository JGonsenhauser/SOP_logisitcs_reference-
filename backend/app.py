"""
SOP App - HTTP Server
Customer SOP reference system. Zero external web dependencies (stdlib only).
Admin: full CRUD on customers + their SOP requirements.
Driver: login, search customers, view SOP cards.
"""
import http.server
import json
import os
import sys
import datetime
import secrets
import urllib.parse

sys.path.insert(0, os.path.dirname(__file__))
from database import get_db, hash_pin, init_db, SOP_CATEGORIES

# ── Sessions ──
active_sessions = {}

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")


def log_audit(user_type, user_id, action, resource_type, resource_id=None, details=None):
    conn = get_db()
    conn.execute(
        "INSERT INTO audit_log (user_type, user_id, action, resource_type, resource_id, details) VALUES (?,?,?,?,?,?)",
        (user_type, user_id, action, resource_type, resource_id, details)
    )
    conn.commit()
    conn.close()


class SOPHandler(http.server.BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        pass  # suppress default logs

    # ── Helpers ──
    def send_json(self, data, status=200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Session-Token")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.end_headers()
        self.wfile.write(body)

    def send_error_json(self, status, message):
        self.send_json({"error": message}, status)

    def send_file(self, filepath, content_type="text/html"):
        try:
            with open(filepath, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        except FileNotFoundError:
            self.send_error_json(404, "File not found")

    def read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        try:
            return json.loads(self.rfile.read(length))
        except Exception:
            return {}

    def get_session(self):
        token = self.headers.get("X-Session-Token", "")
        return active_sessions.get(token)

    def require_session(self, session_type=None):
        s = self.get_session()
        if not s:
            self.send_error_json(401, "Not authenticated")
            return None
        if session_type and s["type"] != session_type:
            self.send_error_json(403, f"{session_type} access required")
            return None
        return s

    # ── ROUTING ──
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Session-Token")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        route = parsed.path
        params = urllib.parse.parse_qs(parsed.query)

        # ── Frontend files ──
        if route == "/":
            self.send_file(os.path.join(FRONTEND_DIR, "admin.html"))
        elif route == "/driver":
            self.send_file(os.path.join(FRONTEND_DIR, "driver.html"))

        # ── API: SOP schema (public - used by both admin and driver frontends) ──
        elif route == "/api/sop-schema":
            self.send_json(SOP_CATEGORIES)

        # ── API: Driver ──
        elif route == "/api/driver/search":
            self.handle_driver_search(params)
        elif route.startswith("/api/driver/customer/") and route.endswith("/sop"):
            cid = int(route.split("/")[4])
            self.handle_driver_get_sop(cid)

        # ── API: Admin ──
        elif route == "/api/admin/dashboard":
            self.handle_admin_dashboard()
        elif route == "/api/admin/customers":
            self.handle_get_customers(params)
        elif route.startswith("/api/admin/customers/") and route.endswith("/sop"):
            cid = int(route.split("/")[4])
            self.handle_get_customer_sop(cid)
        elif route.startswith("/api/admin/customers/"):
            cid = int(route.split("/")[4])
            self.handle_get_single_customer(cid)
        elif route == "/api/admin/drivers":
            self.handle_get_drivers()
        elif route == "/api/admin/audit":
            self.handle_get_audit(params)
        else:
            self.send_error_json(404, "Not found")

    def do_POST(self):
        route = urllib.parse.urlparse(self.path).path

        if route == "/api/driver/login":
            self.handle_driver_login()
        elif route == "/api/admin/login":
            self.handle_admin_login()
        elif route == "/api/admin/customers":
            self.handle_create_customer()
        elif route == "/api/admin/drivers":
            self.handle_create_driver()
        else:
            self.send_error_json(404, "Not found")

    def do_PUT(self):
        route = urllib.parse.urlparse(self.path).path

        if route.startswith("/api/admin/customers/") and route.endswith("/sop"):
            cid = int(route.split("/")[4])
            self.handle_save_customer_sop(cid)
        elif route.startswith("/api/admin/customers/"):
            cid = int(route.split("/")[4])
            self.handle_update_customer(cid)
        else:
            self.send_error_json(404, "Not found")

    def do_DELETE(self):
        route = urllib.parse.urlparse(self.path).path

        if route.startswith("/api/admin/customers/"):
            cid = int(route.split("/")[4])
            self.handle_delete_customer(cid)
        else:
            self.send_error_json(404, "Not found")

    # ═══════════════════════════════════════════════════
    #  AUTH
    # ═══════════════════════════════════════════════════

    def handle_driver_login(self):
        data = self.read_body()
        driver_id = data.get("driver_id")
        pin = data.get("pin", "")
        conn = get_db()
        driver = conn.execute("SELECT * FROM drivers WHERE id=? AND is_active=1", (driver_id,)).fetchone()
        conn.close()
        if not driver or driver["pin_hash"] != hash_pin(pin):
            self.send_error_json(401, "Invalid driver ID or PIN")
            return
        token = secrets.token_hex(32)
        name = f"{driver['first_name']} {driver['last_name']}"
        active_sessions[token] = {"type": "driver", "id": driver["id"], "name": name}
        log_audit("driver", driver["id"], "login", "session")
        self.send_json({"token": token, "driver": {"id": driver["id"], "name": name}})

    def handle_admin_login(self):
        data = self.read_body()
        pin = data.get("pin", "")
        if pin != "admin2026":
            self.send_error_json(401, "Invalid admin PIN")
            return
        token = secrets.token_hex(32)
        active_sessions[token] = {"type": "admin", "id": 0, "name": "Admin"}
        log_audit("admin", 0, "login", "session")
        self.send_json({"token": token})

    # ═══════════════════════════════════════════════════
    #  DRIVER - Customer SOP lookup
    # ═══════════════════════════════════════════════════

    def handle_driver_search(self, params):
        session = self.require_session("driver")
        if not session:
            return
        q = params.get("q", [""])[0].strip()
        if len(q) < 2:
            self.send_json({"customers": []})
            return
        conn = get_db()
        rows = conn.execute(
            "SELECT id, company_name, customer_type, city, state FROM customers WHERE is_active=1 AND company_name LIKE ? ORDER BY company_name LIMIT 20",
            (f"%{q}%",)
        ).fetchall()
        conn.close()
        log_audit("driver", session["id"], "search", "customer", details=q)
        self.send_json({"customers": [dict(r) for r in rows]})

    def handle_driver_get_sop(self, cid):
        session = self.require_session("driver")
        if not session:
            return
        conn = get_db()
        customer = conn.execute("SELECT * FROM customers WHERE id=? AND is_active=1", (cid,)).fetchone()
        if not customer:
            conn.close()
            self.send_error_json(404, "Customer not found")
            return
        reqs = conn.execute(
            "SELECT category, requirement_key, requirement_value, notes FROM sop_requirements WHERE customer_id=? ORDER BY category, requirement_key",
            (cid,)
        ).fetchall()
        conn.close()
        log_audit("driver", session["id"], "view_sop", "customer", cid)
        self.send_json({
            "customer": dict(customer),
            "requirements": [dict(r) for r in reqs]
        })

    # ═══════════════════════════════════════════════════
    #  ADMIN - Dashboard
    # ═══════════════════════════════════════════════════

    def handle_admin_dashboard(self):
        session = self.require_session("admin")
        if not session:
            return
        conn = get_db()
        stats = {
            "total_customers": conn.execute("SELECT COUNT(*) FROM customers WHERE is_active=1").fetchone()[0],
            "total_drivers": conn.execute("SELECT COUNT(*) FROM drivers WHERE is_active=1").fetchone()[0],
            "total_requirements": conn.execute("SELECT COUNT(*) FROM sop_requirements").fetchone()[0],
            "recent_lookups": conn.execute("SELECT COUNT(*) FROM audit_log WHERE action='view_sop' AND timestamp > datetime('now', '-24 hours')").fetchone()[0],
        }
        # Recent activity
        recent = conn.execute("""
            SELECT al.*,
                   CASE WHEN al.user_type='driver' THEN d.first_name || ' ' || d.last_name ELSE 'Admin' END as user_name
            FROM audit_log al
            LEFT JOIN drivers d ON al.user_type='driver' AND al.user_id = d.id
            ORDER BY al.timestamp DESC LIMIT 15
        """).fetchall()
        conn.close()
        self.send_json({"stats": stats, "recent_activity": [dict(r) for r in recent]})

    # ═══════════════════════════════════════════════════
    #  ADMIN - Customers CRUD
    # ═══════════════════════════════════════════════════

    def handle_get_customers(self, params):
        session = self.require_session("admin")
        if not session:
            return
        conn = get_db()
        q = params.get("q", [""])[0].strip()
        if q:
            rows = conn.execute(
                "SELECT c.*, (SELECT COUNT(*) FROM sop_requirements WHERE customer_id=c.id) as req_count FROM customers c WHERE c.is_active=1 AND c.company_name LIKE ? ORDER BY c.company_name",
                (f"%{q}%",)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT c.*, (SELECT COUNT(*) FROM sop_requirements WHERE customer_id=c.id) as req_count FROM customers c WHERE c.is_active=1 ORDER BY c.company_name"
            ).fetchall()
        conn.close()
        self.send_json({"customers": [dict(r) for r in rows]})

    def handle_get_single_customer(self, cid):
        session = self.require_session("admin")
        if not session:
            return
        conn = get_db()
        row = conn.execute("SELECT * FROM customers WHERE id=?", (cid,)).fetchone()
        conn.close()
        if not row:
            self.send_error_json(404, "Customer not found")
            return
        self.send_json(dict(row))

    def handle_create_customer(self):
        session = self.require_session("admin")
        if not session:
            return
        data = self.read_body()
        if not data.get("company_name"):
            self.send_error_json(400, "Company name required")
            return
        conn = get_db()
        c = conn.execute("""
            INSERT INTO customers (company_name, customer_type, address_line1, address_line2,
                city, state, zip_code, primary_contact_name, primary_contact_phone,
                primary_contact_email, notes)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, (
            data["company_name"], data.get("customer_type", "commercial"),
            data.get("address_line1"), data.get("address_line2"),
            data.get("city"), data.get("state"), data.get("zip_code"),
            data.get("primary_contact_name"), data.get("primary_contact_phone"),
            data.get("primary_contact_email"), data.get("notes")
        ))
        conn.commit()
        cid = c.lastrowid
        conn.close()
        log_audit("admin", 0, "create", "customer", cid)
        self.send_json({"message": "Customer created", "id": cid})

    def handle_update_customer(self, cid):
        session = self.require_session("admin")
        if not session:
            return
        data = self.read_body()
        conn = get_db()
        existing = conn.execute("SELECT * FROM customers WHERE id=?", (cid,)).fetchone()
        if not existing:
            conn.close()
            self.send_error_json(404, "Customer not found")
            return
        conn.execute("""
            UPDATE customers SET company_name=?, customer_type=?, address_line1=?, address_line2=?,
                city=?, state=?, zip_code=?, primary_contact_name=?, primary_contact_phone=?,
                primary_contact_email=?, notes=?, updated_at=CURRENT_TIMESTAMP
            WHERE id=?
        """, (
            data.get("company_name", existing["company_name"]),
            data.get("customer_type", existing["customer_type"]),
            data.get("address_line1", existing["address_line1"]),
            data.get("address_line2", existing["address_line2"]),
            data.get("city", existing["city"]),
            data.get("state", existing["state"]),
            data.get("zip_code", existing["zip_code"]),
            data.get("primary_contact_name", existing["primary_contact_name"]),
            data.get("primary_contact_phone", existing["primary_contact_phone"]),
            data.get("primary_contact_email", existing["primary_contact_email"]),
            data.get("notes", existing["notes"]),
            cid
        ))
        conn.commit()
        conn.close()
        log_audit("admin", 0, "update", "customer", cid)
        self.send_json({"message": "Customer updated"})

    def handle_delete_customer(self, cid):
        session = self.require_session("admin")
        if not session:
            return
        conn = get_db()
        conn.execute("UPDATE customers SET is_active=0, updated_at=CURRENT_TIMESTAMP WHERE id=?", (cid,))
        conn.commit()
        conn.close()
        log_audit("admin", 0, "deactivate", "customer", cid)
        self.send_json({"message": "Customer deactivated"})

    # ═══════════════════════════════════════════════════
    #  ADMIN - SOP Requirements per customer
    # ═══════════════════════════════════════════════════

    def handle_get_customer_sop(self, cid):
        session = self.require_session("admin")
        if not session:
            return
        conn = get_db()
        reqs = conn.execute(
            "SELECT * FROM sop_requirements WHERE customer_id=? ORDER BY category, requirement_key",
            (cid,)
        ).fetchall()
        conn.close()
        self.send_json({"requirements": [dict(r) for r in reqs]})

    def handle_save_customer_sop(self, cid):
        """Bulk save: receives full set of requirements, replaces existing."""
        session = self.require_session("admin")
        if not session:
            return
        data = self.read_body()
        requirements = data.get("requirements", [])

        conn = get_db()
        # Verify customer exists
        if not conn.execute("SELECT id FROM customers WHERE id=?", (cid,)).fetchone():
            conn.close()
            self.send_error_json(404, "Customer not found")
            return

        # Replace all requirements
        conn.execute("DELETE FROM sop_requirements WHERE customer_id=?", (cid,))
        for req in requirements:
            val = str(req.get("requirement_value", "")).strip()
            if val and val.lower() not in ("", "no", "false", "0", "none"):
                conn.execute("""
                    INSERT INTO sop_requirements (customer_id, category, requirement_key, requirement_value, notes)
                    VALUES (?,?,?,?,?)
                """, (cid, req["category"], req["requirement_key"], val, req.get("notes")))
        conn.commit()
        count = conn.execute("SELECT COUNT(*) FROM sop_requirements WHERE customer_id=?", (cid,)).fetchone()[0]
        conn.close()
        log_audit("admin", 0, "save_sop", "customer", cid, f"{count} requirements")
        self.send_json({"message": f"Saved {count} requirements"})

    # ═══════════════════════════════════════════════════
    #  ADMIN - Drivers
    # ═══════════════════════════════════════════════════

    def handle_get_drivers(self):
        session = self.require_session("admin")
        if not session:
            return
        conn = get_db()
        rows = conn.execute("SELECT id, first_name, last_name, phone, email, is_active, created_at FROM drivers ORDER BY first_name").fetchall()
        conn.close()
        self.send_json({"drivers": [dict(r) for r in rows]})

    def handle_create_driver(self):
        session = self.require_session("admin")
        if not session:
            return
        data = self.read_body()
        if not data.get("first_name") or not data.get("pin"):
            self.send_error_json(400, "first_name and pin required")
            return
        conn = get_db()
        c = conn.execute(
            "INSERT INTO drivers (first_name, last_name, phone, email, pin_hash) VALUES (?,?,?,?,?)",
            (data["first_name"], data.get("last_name", ""), data.get("phone"), data.get("email"), hash_pin(data["pin"]))
        )
        conn.commit()
        did = c.lastrowid
        conn.close()
        log_audit("admin", 0, "create", "driver", did)
        self.send_json({"message": "Driver created", "id": did})

    # ═══════════════════════════════════════════════════
    #  ADMIN - Audit Log
    # ═══════════════════════════════════════════════════

    def handle_get_audit(self, params):
        session = self.require_session("admin")
        if not session:
            return
        limit = int(params.get("limit", [100])[0])
        conn = get_db()
        rows = conn.execute("SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT ?", (limit,)).fetchall()
        conn.close()
        self.send_json({"logs": [dict(r) for r in rows]})


# ═══════════════════════════════════════════════════
#  SERVER
# ═══════════════════════════════════════════════════

def run_server(port=8000):
    init_db()
    server = http.server.HTTPServer(("0.0.0.0", port), SOPHandler)
    print(f"\n{'='*55}")
    print(f"  LOGISTICS SOP REFERENCE APP")
    print(f"  Running on port {port}")
    print(f"{'='*55}")
    print(f"  Admin Dashboard:  http://localhost:{port}")
    print(f"  Driver Lookup:    http://localhost:{port}/driver")
    print(f"")
    print(f"  Admin PIN:  admin2026")
    print(f"{'='*55}\n")
    server.serve_forever()


if __name__ == "__main__":
    run_server()
