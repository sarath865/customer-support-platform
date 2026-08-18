from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ============================================================
# CREATE SLA POLICY
# ============================================================

class SLAPolicyCreate(BaseModel):
    priority: str = Field(
        ...,
        description="Priority: low, medium, high, urgent",
    )

    first_response_minutes: int = Field(
        ...,
        gt=0,
        description="Maximum allowed first response time in minutes",
    )

    resolution_minutes: int = Field(
        ...,
        gt=0,
        description="Maximum allowed resolution time in minutes",
    )

    is_active: bool = Field(
        default=True,
        description="Whether this SLA policy is active",
    )


# ============================================================
# UPDATE SLA POLICY
# ============================================================

class SLAPolicyUpdate(BaseModel):
    priority: Optional[str] = Field(
        default=None,
        description="Priority: low, medium, high, urgent",
    )

    first_response_minutes: Optional[int] = Field(
        default=None,
        gt=0,
    )

    resolution_minutes: Optional[int] = Field(
        default=None,
        gt=0,
    )

    is_active: Optional[bool] = None


# ============================================================
# SLA POLICY RESPONSE
# ============================================================

class SLAPolicyResponse(BaseModel):
    id: int
    priority: str
    first_response_minutes: int
    resolution_minutes: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================
# TICKET SLA RESPONSE
# ============================================================

class TicketSLAResponse(BaseModel):
    ticket_id: int
    priority: str
    status: str

    first_response_deadline: Optional[datetime] = None
    resolution_deadline: Optional[datetime] = None

    first_response_time: Optional[datetime] = None
    resolution_time: Optional[datetime] = None

    sla_status: str