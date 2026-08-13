from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ============================================================
# CREATE TICKET
# ============================================================

class TicketCreate(BaseModel):
    subject: str = Field(
        ...,
        min_length=3,
        max_length=200,
        description="Short description of the customer issue",
    )

    description: str = Field(
        ...,
        min_length=10,
        description="Detailed description of the issue",
    )

    priority: str = Field(
        default="medium",
        description="Ticket priority: low, medium, high, urgent",
    )


# ============================================================
# UPDATE TICKET
# ============================================================

class TicketUpdate(BaseModel):
    subject: Optional[str] = Field(
        default=None,
        min_length=3,
        max_length=200,
    )

    description: Optional[str] = Field(
        default=None,
        min_length=10,
    )

    priority: Optional[str] = Field(
        default=None,
        description="Ticket priority: low, medium, high, urgent",
    )

    status: Optional[str] = Field(
        default=None,
        description="Ticket status: open, in_progress, resolved, closed",
    )


# ============================================================
# ASSIGN TICKET
# ============================================================

class TicketAssign(BaseModel):
    assigned_agent_id: int = Field(
        ...,
        gt=0,
        description="ID of the support agent to assign",
    )


# ============================================================
# TICKET RESPONSE
# ============================================================

class TicketResponse(BaseModel):
    id: int

    customer_id: int

    assigned_agent_id: Optional[int] = None

    subject: str

    description: str

    priority: str

    status: str

    created_at: datetime

    updated_at: datetime

    class Config:
        from_attributes = True