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

    # --------------------------------------------------------
    # SLA INFORMATION
    # --------------------------------------------------------

    first_response_deadline: Optional[datetime] = None
    resolution_deadline: Optional[datetime] = None

    first_response_time: Optional[datetime] = None
    resolution_time: Optional[datetime] = None

    sla_status: str

    class Config:
        from_attributes = True


# ============================================================
# CREATE COMMENT
# ============================================================

class TicketCommentCreate(BaseModel):
    comment: str = Field(
        ...,
        min_length=1,
        description="Comment or reply on the ticket",
    )


# ============================================================
# COMMENT RESPONSE
# ============================================================

class TicketCommentResponse(BaseModel):
    id: int
    ticket_id: int
    user_id: int
    comment: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================
# CREATE TICKET MESSAGE
# ============================================================

class TicketMessageCreate(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        description="Conversation message",
    )

    message_type: str = Field(
        default="agent_reply",
        description=(
            "Message type: customer_reply, agent_reply, "
            "system_message, internal_note"
        ),
    )


# ============================================================
# UPDATE TICKET MESSAGE
# ============================================================

class TicketMessageUpdate(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        description="Updated conversation message",
    )


# ============================================================
# TICKET MESSAGE RESPONSE
# ============================================================

class TicketMessageResponse(BaseModel):
    id: int
    ticket_id: int
    user_id: int
    message: str
    message_type: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True