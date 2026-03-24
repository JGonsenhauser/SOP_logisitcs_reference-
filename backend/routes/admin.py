"""
SOP App - Admin routes.
Dashboard, customer CRUD, driver management, audit log.
"""
from fastapi import APIRouter, Depends, Query, HTTPException, Request

from database import get_db, hash_pin
from crypto import encrypt_if_sensitive, decrypt_if_sensitive
from middleware.auth import require_admin, get_client_ip
from models.requests import CustomerCreate, CustomerUpdate, SOPSaveRequest, DriverCreate, DriverUpdate
from routes.auth import _log_audit

router = APIRouter(prefix="/api/admin", tags=["admin"])


def _audit(session: dict, request: Request, action: str, resource_type: str,
           resource_id: int | None = None, details: str | None = None):
    _log_audit(
        "admin", session["user_id"], session["user_name"],
        action, resource_type, resource_id, details,
        ip=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
        session_id=session["token"],
        request_path=str(request.url.path)
    )


# ── Dashboard ──

@router.get("/dashboard")
def admin_dashboard(request: Request, session: dict = Depends(require_admin)):
    conn = get_db()
    stats = {
        "total_customers": conn.execute(
            "SELECT COUNT(*) FROM customers WHERE is_active=1"
        ).fetchone()[0],
        "total_drivers": conn.execute(
            "SELECT COUNT(*) FROM drivers WHERE is_active=1"
        ).fetchone()[0],
        "total_requirements": conn.execute(
            "SELECT COUNT(*) FROM sop_requirements"
        ).fetchone()[0],
        "recent_lookups": conn.execute(
            "SELECT COUNT(*) FROM audit_log WHERE action='view_sop' AND timestamp > datetime('now', '-24 hours')"
        ).fetchone()[0],
    }
    recent = conn.execute("""
        SELECT al.*,
               COALESCE(al.user_name,
                   CASE WHEN al.user_type='driver'
                        THEN (SELECT d.first_name || ' ' || d.last_name FROM drivers d WHERE d.id = al.user_id)
                        ELSE 'Admin'
                   END) as display_name
        FROM audit_log al
        ORDER BY al.timestamp DESC LIMIT 15
    """).fetchall()
    conn.close()
    return {"stats": stats, "recent_activity": [dict(r) for r in recent]}


# ── Customers CRUD ──

@router.get("/customers")
def get_customers(
    request: Request,
    q: str = Query("", min_length=0),
    session: dict = Depends(require_admin)
):
    conn = get_db()
    if q.strip():
        rows = conn.execute(
            """SELECT c.*, (SELECT COUNT(*) FROM sop_requirements WHERE customer_id=c.id) as req_count
               FROM customers c WHERE c.is_active=1 AND c.company_name LIKE ?
               ORDER BY c.company_name""",
            (f"%{q.strip()}%",)
        ).fetchall()
    else:
        rows = conn.execute(
            """SELECT c.*, (SELECT COUNT(*) FROM sop_requirements WHERE customer_id=c.id) as req_count
               FROM customers c WHERE c.is_active=1 ORDER BY c.company_name"""
        ).fetchall()
    conn.close()
    return {"customers": [dict(r) for r in rows]}


@router.get("/customers/{customer_id}")
def get_single_customer(
    customer_id: int,
    request: Request,
    session: dict = Depends(require_admin)
):
    conn = get_db()
    row = conn.execute("SELECT * FROM customers WHERE id=?", (customer_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Customer not found")
    return dict(row)


@router.post("/customers")
def create_customer(
    body: CustomerCreate,
    request: Request,
    session: dict = Depends(require_admin)
):
    conn = get_db()
    c = conn.execute("""
        INSERT INTO customers (company_name, customer_type, address_line1, address_line2,
            city, state, zip_code, primary_contact_name, primary_contact_phone,
            primary_contact_email, notes)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)
    """, (
        body.company_name, body.customer_type,
        body.address_line1, body.address_line2,
        body.city, body.state, body.zip_code,
        body.primary_contact_name, body.primary_contact_phone,
        body.primary_contact_email, body.notes
    ))
    conn.commit()
    cid = c.lastrowid
    conn.close()
    _audit(session, request, "create", "customer", cid)
    return {"message": "Customer created", "id": cid}


@router.put("/customers/{customer_id}")
def update_customer(
    customer_id: int,
    body: CustomerUpdate,
    request: Request,
    session: dict = Depends(require_admin)
):
    conn = get_db()
    existing = conn.execute("SELECT * FROM customers WHERE id=?", (customer_id,)).fetchone()
    if not existing:
        conn.close()
        raise HTTPException(status_code=404, detail="Customer not found")

    conn.execute("""
        UPDATE customers SET company_name=?, customer_type=?, address_line1=?, address_line2=?,
            city=?, state=?, zip_code=?, primary_contact_name=?, primary_contact_phone=?,
            primary_contact_email=?, notes=?, updated_at=CURRENT_TIMESTAMP
        WHERE id=?
    """, (
        body.company_name or existing["company_name"],
        body.customer_type or existing["customer_type"],
        body.address_line1 if body.address_line1 is not None else existing["address_line1"],
        body.address_line2 if body.address_line2 is not None else existing["address_line2"],
        body.city if body.city is not None else existing["city"],
        body.state if body.state is not None else existing["state"],
        body.zip_code if body.zip_code is not None else existing["zip_code"],
        body.primary_contact_name if body.primary_contact_name is not None else existing["primary_contact_name"],
        body.primary_contact_phone if body.primary_contact_phone is not None else existing["primary_contact_phone"],
        body.primary_contact_email if body.primary_contact_email is not None else existing["primary_contact_email"],
        body.notes if body.notes is not None else existing["notes"],
        customer_id
    ))
    conn.commit()
    conn.close()
    _audit(session, request, "update", "customer", customer_id)
    return {"message": "Customer updated"}


@router.delete("/customers/{customer_id}")
def delete_customer(
    customer_id: int,
    request: Request,
    session: dict = Depends(require_admin)
):
    conn = get_db()
    conn.execute(
        "UPDATE customers SET is_active=0, updated_at=CURRENT_TIMESTAMP WHERE id=?",
        (customer_id,)
    )
    conn.commit()
    conn.close()
    _audit(session, request, "deactivate", "customer", customer_id)
    return {"message": "Customer deactivated"}


# ── SOP Requirements ──

@router.get("/customers/{customer_id}/sop")
def get_customer_sop(
    customer_id: int,
    request: Request,
    session: dict = Depends(require_admin)
):
    conn = get_db()
    reqs = conn.execute(
        "SELECT * FROM sop_requirements WHERE customer_id=? ORDER BY category, requirement_key",
        (customer_id,)
    ).fetchall()
    conn.close()

    # Decrypt sensitive fields for admin view
    requirements = []
    for r in reqs:
        rd = dict(r)
        rd["requirement_value"] = decrypt_if_sensitive(
            rd["requirement_key"], rd["requirement_value"]
        )
        requirements.append(rd)

    return {"requirements": requirements}


@router.put("/customers/{customer_id}/sop")
def save_customer_sop(
    customer_id: int,
    body: SOPSaveRequest,
    request: Request,
    session: dict = Depends(require_admin)
):
    conn = get_db()
    if not conn.execute("SELECT id FROM customers WHERE id=?", (customer_id,)).fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Customer not found")

    # Replace all requirements
    conn.execute("DELETE FROM sop_requirements WHERE customer_id=?", (customer_id,))
    for req in body.requirements:
        val = req.requirement_value.strip()
        if val and val.lower() not in ("", "no", "false", "0", "none"):
            # Encrypt sensitive fields before storage
            encrypted_val = encrypt_if_sensitive(req.requirement_key, val)
            conn.execute("""
                INSERT INTO sop_requirements (customer_id, category, requirement_key, requirement_value, notes)
                VALUES (?,?,?,?,?)
            """, (customer_id, req.category, req.requirement_key, encrypted_val, req.notes))

    conn.commit()
    count = conn.execute(
        "SELECT COUNT(*) FROM sop_requirements WHERE customer_id=?",
        (customer_id,)
    ).fetchone()[0]
    conn.close()
    _audit(session, request, "save_sop", "customer", customer_id, f"{count} requirements")
    return {"message": f"Saved {count} requirements"}


# ── Drivers ──

@router.get("/drivers")
def get_drivers(request: Request, session: dict = Depends(require_admin)):
    conn = get_db()
    rows = conn.execute(
        "SELECT id, first_name, last_name, phone, email, is_admin, is_active, created_at,"
        " SUBSTR(first_name,1,1) || last_name as username"
        " FROM drivers ORDER BY id"
    ).fetchall()
    conn.close()
    return {"drivers": [dict(r) for r in rows]}


@router.post("/drivers")
def create_driver(
    body: DriverCreate,
    request: Request,
    session: dict = Depends(require_admin)
):
    conn = get_db()
    c = conn.execute(
        "INSERT INTO drivers (first_name, last_name, phone, email, pin_hash, is_admin) VALUES (?,?,?,?,?,?)",
        (body.first_name, body.last_name, body.phone, body.email,
         hash_pin(body.pin), 1 if body.is_admin else 0)
    )
    conn.commit()
    did = c.lastrowid
    conn.close()
    _audit(session, request, "create", "driver", did)
    return {"message": "Driver created", "id": did}


@router.put("/drivers/{driver_id}")
def update_driver(
    driver_id: int,
    body: DriverUpdate,
    request: Request,
    session: dict = Depends(require_admin)
):
    conn = get_db()
    existing = conn.execute("SELECT * FROM drivers WHERE id=?", (driver_id,)).fetchone()
    if not existing:
        conn.close()
        raise HTTPException(status_code=404, detail="Driver not found")

    # Prevent admin from removing their own admin access
    if driver_id == session["user_id"] and body.is_admin is False:
        conn.close()
        raise HTTPException(status_code=400, detail="Cannot remove your own admin access")

    updates = []
    params = []
    if body.first_name is not None:
        updates.append("first_name=?"); params.append(body.first_name)
    if body.last_name is not None:
        updates.append("last_name=?"); params.append(body.last_name)
    if body.phone is not None:
        updates.append("phone=?"); params.append(body.phone)
    if body.email is not None:
        updates.append("email=?"); params.append(body.email)
    if body.pin is not None:
        updates.append("pin_hash=?"); params.append(hash_pin(body.pin))
    if body.is_admin is not None:
        updates.append("is_admin=?"); params.append(1 if body.is_admin else 0)

    if updates:
        params.append(driver_id)
        conn.execute(f"UPDATE drivers SET {', '.join(updates)} WHERE id=?", params)
        conn.commit()
    conn.close()
    _audit(session, request, "update", "driver", driver_id)
    return {"message": "Driver updated"}


@router.delete("/drivers/{driver_id}")
def deactivate_driver(
    driver_id: int,
    request: Request,
    session: dict = Depends(require_admin)
):
    # Prevent admin from deactivating themselves
    if driver_id == session["user_id"]:
        raise HTTPException(status_code=400, detail="Cannot deactivate your own account")

    conn = get_db()
    existing = conn.execute("SELECT * FROM drivers WHERE id=?", (driver_id,)).fetchone()
    if not existing:
        conn.close()
        raise HTTPException(status_code=404, detail="Driver not found")

    new_status = 0 if existing["is_active"] else 1
    conn.execute("UPDATE drivers SET is_active=? WHERE id=?", (new_status, driver_id))
    # Expire their sessions if deactivating
    if new_status == 0:
        conn.execute("DELETE FROM sessions WHERE user_id=?", (driver_id,))
    conn.commit()
    conn.close()
    action = "deactivate" if new_status == 0 else "reactivate"
    _audit(session, request, action, "driver", driver_id)
    return {"message": f"Driver {'deactivated' if new_status == 0 else 'reactivated'}"}


# ── Audit Log ──

@router.get("/audit")
def get_audit(
    request: Request,
    limit: int = Query(100, ge=1, le=1000),
    action: str = Query("", min_length=0),
    user_type: str = Query("", min_length=0),
    driver_id: int = Query(0, ge=0),
    session: dict = Depends(require_admin)
):
    conn = get_db()
    query = "SELECT * FROM audit_log WHERE 1=1"
    params: list = []
    if action:
        query += " AND action=?"
        params.append(action)
    if user_type:
        query += " AND user_type=?"
        params.append(user_type)
    if driver_id:
        query += " AND user_id=?"
        params.append(driver_id)
    query += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return {"logs": [dict(r) for r in rows]}


# ── Analytics ──

@router.get("/analytics/lookups-over-time")
def lookups_over_time(
    request: Request,
    days: int = Query(30, ge=1, le=90),
    session: dict = Depends(require_admin)
):
    conn = get_db()
    rows = conn.execute("""
        SELECT DATE(timestamp) as day, COUNT(*) as count
        FROM audit_log
        WHERE action='view_sop' AND timestamp > datetime('now', ? || ' days')
        GROUP BY DATE(timestamp) ORDER BY day
    """, (f"-{days}",)).fetchall()
    conn.close()
    return {"data": [dict(r) for r in rows]}


@router.get("/analytics/top-customers")
def top_customers(
    request: Request,
    limit: int = Query(10, ge=1, le=50),
    session: dict = Depends(require_admin)
):
    conn = get_db()
    rows = conn.execute("""
        SELECT c.company_name, COUNT(al.id) as view_count
        FROM audit_log al
        JOIN customers c ON al.resource_id = c.id
        WHERE al.action='view_sop' AND al.resource_type='customer'
        GROUP BY al.resource_id
        ORDER BY view_count DESC LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return {"data": [dict(r) for r in rows]}


@router.get("/analytics/hourly-activity")
def hourly_activity(
    request: Request,
    session: dict = Depends(require_admin)
):
    conn = get_db()
    rows = conn.execute("""
        SELECT CAST(strftime('%H', timestamp) AS INTEGER) as hour, COUNT(*) as count
        FROM audit_log
        WHERE action IN ('view_sop', 'search') AND timestamp > datetime('now', '-30 days')
        GROUP BY hour ORDER BY hour
    """).fetchall()
    conn.close()
    # Fill in missing hours with 0
    hour_map = {r["hour"]: r["count"] for r in rows}
    data = [{"hour": h, "count": hour_map.get(h, 0)} for h in range(24)]
    return {"data": data}


@router.get("/analytics/driver-usage")
def driver_usage(
    request: Request,
    session: dict = Depends(require_admin)
):
    conn = get_db()
    rows = conn.execute("""
        SELECT d.id, d.first_name || ' ' || d.last_name as name,
               COUNT(CASE WHEN al.action='view_sop' THEN 1 END) as total_lookups,
               COUNT(DISTINCT CASE WHEN al.action='view_sop' THEN al.resource_id END) as unique_customers,
               MAX(al.timestamp) as last_active
        FROM drivers d
        LEFT JOIN audit_log al ON d.id = al.user_id AND al.user_type='driver'
        WHERE d.is_active=1 AND d.is_admin=0
        GROUP BY d.id ORDER BY total_lookups DESC
    """).fetchall()
    conn.close()
    return {"drivers": [dict(r) for r in rows]}


@router.get("/analytics/customer-coverage")
def customer_coverage(
    request: Request,
    session: dict = Depends(require_admin)
):
    conn = get_db()
    # Count total possible fields across all categories
    from database import SOP_CATEGORIES
    total_fields = sum(len(cat["fields"]) for cat in SOP_CATEGORIES.values())

    rows = conn.execute("""
        SELECT c.id, c.company_name, c.customer_type,
               COUNT(sr.id) as filled_fields,
               MAX(sr.updated_at) as last_updated
        FROM customers c
        LEFT JOIN sop_requirements sr ON c.id = sr.customer_id
        WHERE c.is_active=1
        GROUP BY c.id ORDER BY filled_fields ASC
    """).fetchall()
    conn.close()

    customers = []
    for r in rows:
        rd = dict(r)
        rd["total_fields"] = total_fields
        rd["coverage_pct"] = round((rd["filled_fields"] / total_fields) * 100) if total_fields > 0 else 0
        customers.append(rd)
    return {"customers": customers, "total_fields": total_fields}


@router.get("/analytics/security")
def security_monitor(
    request: Request,
    session: dict = Depends(require_admin)
):
    conn = get_db()
    failed_logins_24h = conn.execute(
        "SELECT COUNT(*) FROM audit_log WHERE action='login_failed' AND timestamp > datetime('now', '-24 hours')"
    ).fetchone()[0]

    # Recent failed logins with detail
    failed_recent = conn.execute("""
        SELECT ip_address, user_id, timestamp, user_agent
        FROM audit_log WHERE action='login_failed'
        ORDER BY timestamp DESC LIMIT 20
    """).fetchall()

    # Suspicious: multiple driver IDs from same IP
    suspicious_ips = conn.execute("""
        SELECT ip_address, COUNT(DISTINCT user_id) as driver_count, COUNT(*) as login_count
        FROM audit_log WHERE action='login' AND user_type='driver'
        AND timestamp > datetime('now', '-7 days')
        GROUP BY ip_address HAVING driver_count > 2
        ORDER BY driver_count DESC LIMIT 10
    """).fetchall()

    # Sensitive field access (gate codes, lock codes viewed)
    sensitive_access = conn.execute("""
        SELECT al.user_name, al.resource_id, c.company_name, al.timestamp, al.ip_address
        FROM audit_log al
        LEFT JOIN customers c ON al.resource_id = c.id
        WHERE al.action='view_sop' AND al.user_type='driver'
        ORDER BY al.timestamp DESC LIMIT 20
    """).fetchall()

    conn.close()
    return {
        "failed_logins_24h": failed_logins_24h,
        "failed_recent": [dict(r) for r in failed_recent],
        "suspicious_ips": [dict(r) for r in suspicious_ips],
        "sensitive_access": [dict(r) for r in sensitive_access],
    }
