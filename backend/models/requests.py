"""
SOP App - Pydantic request models for input validation.
"""
from pydantic import BaseModel, Field
from typing import Optional


class DriverLoginRequest(BaseModel):
    driver_id: int
    pin: str = Field(min_length=4, max_length=20)


class AdminLoginRequest(BaseModel):
    user_id: int
    pin: str = Field(min_length=4, max_length=20)


class CustomerCreate(BaseModel):
    company_name: str = Field(min_length=1, max_length=200)
    customer_type: str = "commercial"
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    primary_contact_name: Optional[str] = None
    primary_contact_phone: Optional[str] = None
    primary_contact_email: Optional[str] = None
    notes: Optional[str] = None


class CustomerUpdate(BaseModel):
    company_name: Optional[str] = Field(None, min_length=1, max_length=200)
    customer_type: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    primary_contact_name: Optional[str] = None
    primary_contact_phone: Optional[str] = None
    primary_contact_email: Optional[str] = None
    notes: Optional[str] = None


class SOPRequirement(BaseModel):
    category: str
    requirement_key: str
    requirement_value: str
    notes: Optional[str] = None


class SOPSaveRequest(BaseModel):
    requirements: list[SOPRequirement] = []


class DriverCreate(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = ""
    phone: Optional[str] = None
    email: Optional[str] = None
    pin: str = Field(min_length=4, max_length=20)
    is_admin: bool = False
