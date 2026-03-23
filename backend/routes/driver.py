"""
SOP App - Driver routes.
Search customers and view SOP requirements.
"""
from fastapi import APIRouter, Depends, Query, HTTPException, Request

from database import get_db
from crypto import decrypt_if_sensitive
from middleware.auth import require_driver, get_client_ip
from routes.auth import _log_audit

router = APIRouter(prefix="/api/driver", tags=["driver"])


@router.get("/search")
def driver_search(
    request: Request,
    q: str = Query("", min_length=0),
    session: dict = Depends(require_driver)
):
    if len(q.strip()) < 2:
        return {"customers": []}

    conn = get_db()
    rows = conn.execute(
        """SELECT id, company_name, customer_type, city, state
           FROM customers WHERE is_active=1 AND company_name LIKE ?
           ORDER BY company_name LIMIT 20""",
        (f"%{q.strip()}%",)
    ).fetchall()
    conn.close()

    _log_audit("driver", session["user_id"], session["user_name"],
               "search", "customer", details=q.strip(),
               ip=get_client_ip(request),
               user_agent=request.headers.get("user-agent"),
               session_id=session["token"],
               request_path=str(request.url.path))

    return {"customers": [dict(r) for r in rows]}


@router.get("/customer/{customer_id}/sop")
def driver_get_sop(
    customer_id: int,
    request: Request,
    session: dict = Depends(require_driver)
):
    conn = get_db()
    customer = conn.execute(
        "SELECT * FROM customers WHERE id=? AND is_active=1",
        (customer_id,)
    ).fetchone()
    if not customer:
        conn.close()
        raise HTTPException(status_code=404, detail="Customer not found")

    reqs = conn.execute(
        """SELECT category, requirement_key, requirement_value, notes
           FROM sop_requirements WHERE customer_id=?
           ORDER BY category, requirement_key""",
        (customer_id,)
    ).fetchall()
    conn.close()

    # Decrypt sensitive fields
    requirements = []
    for r in reqs:
        rd = dict(r)
        rd["requirement_value"] = decrypt_if_sensitive(
            rd["requirement_key"], rd["requirement_value"]
        )
        requirements.append(rd)

    _log_audit("driver", session["user_id"], session["user_name"],
               "view_sop", "customer", customer_id,
               ip=get_client_ip(request),
               user_agent=request.headers.get("user-agent"),
               session_id=session["token"],
               request_path=str(request.url.path))

    return {"customer": dict(customer), "requirements": requirements}
