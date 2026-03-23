"""
SOP App - Schema route.
Public endpoint returning the SOP category definitions.
"""
from fastapi import APIRouter

from database import SOP_CATEGORIES

router = APIRouter(prefix="/api", tags=["schema"])


@router.get("/sop-schema")
def get_sop_schema():
    return SOP_CATEGORIES
