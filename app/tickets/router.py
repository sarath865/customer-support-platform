from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Ticket, User
from app.auth.dependencies import get_current_user
from app.tickets.schemas import (
    TicketCreate,
    TicketUpdate,
    TicketAssign,
    TicketResponse,
)


router = APIRouter(
    prefix="/tickets",
    tags=["Tickets"],
)


# ============================================================
# CREATE TICKET
# Customer can create a ticket
# ============================================================

@router.post(
    "/",
    response_model=TicketResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_ticket(
    ticket_data: TicketCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Only customers can create tickets
    if current_user.role != "customer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only customers can create tickets",
        )

    # Validate priority
    allowed_priorities = {
        "low",
        "medium",
        "high",
        "urgent",
    }

    if ticket_data.priority not in allowed_priorities:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid priority",
        )

    ticket = Ticket(
        customer_id=current_user.id,
        subject=ticket_data.subject,
        description=ticket_data.description,
        priority=ticket_data.priority,
        status="open",
    )

    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    return ticket


# ============================================================
# LIST TICKETS
# ============================================================

@router.get(
    "/",
    response_model=List[TicketResponse],
)
def list_tickets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Customer → only their own tickets
    if current_user.role == "customer":

        tickets = (
            db.query(Ticket)
            .filter(Ticket.customer_id == current_user.id)
            .order_by(Ticket.created_at.desc())
            .all()
        )

        return tickets

    # Support agent → tickets assigned to them
    if current_user.role == "support_agent":

        tickets = (
            db.query(Ticket)
            .filter(Ticket.assigned_agent_id == current_user.id)
            .order_by(Ticket.created_at.desc())
            .all()
        )

        return tickets

    # Support manager / admin → all tickets
    if current_user.role in {
        "support_manager",
        "admin",
    }:

        tickets = (
            db.query(Ticket)
            .order_by(Ticket.created_at.desc())
            .all()
        )

        return tickets

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You do not have permission to view tickets",
    )


# ============================================================
# GET SINGLE TICKET
# ============================================================

@router.get(
    "/{ticket_id}",
    response_model=TicketResponse,
)
def get_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ticket = (
        db.query(Ticket)
        .filter(Ticket.id == ticket_id)
        .first()
    )

    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found",
        )

    # Customer can only see their own ticket
    if current_user.role == "customer":
        if ticket.customer_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to view this ticket",
            )

    # Agent can only see assigned tickets
    elif current_user.role == "support_agent":
        if ticket.assigned_agent_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to view this ticket",
            )

    # Manager and admin can see everything
    elif current_user.role not in {
        "support_manager",
        "admin",
    }:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view this ticket",
        )

    return ticket


# ============================================================
# UPDATE TICKET
# ============================================================

@router.patch(
    "/{ticket_id}",
    response_model=TicketResponse,
)
def update_ticket(
    ticket_id: int,
    ticket_data: TicketUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ticket = (
        db.query(Ticket)
        .filter(Ticket.id == ticket_id)
        .first()
    )

    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found",
        )

    # Allowed roles
    if current_user.role not in {
        "customer",
        "support_agent",
        "support_manager",
        "admin",
    }:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to update tickets",
        )

    # Customer can update only their own ticket
    if current_user.role == "customer":

        if ticket.customer_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own tickets",
            )

        # Customer cannot change status
        if ticket_data.status is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Customers cannot change ticket status",
            )

    # Agent can update only assigned tickets
    if current_user.role == "support_agent":

        if ticket.assigned_agent_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update tickets assigned to you",
            )

    # Validate priority
    allowed_priorities = {
        "low",
        "medium",
        "high",
        "urgent",
    }

    if (
        ticket_data.priority is not None
        and ticket_data.priority not in allowed_priorities
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid priority",
        )

    # Validate status
    allowed_statuses = {
        "open",
        "in_progress",
        "resolved",
        "closed",
    }

    if (
        ticket_data.status is not None
        and ticket_data.status not in allowed_statuses
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid status",
        )

    # Update only supplied fields
    if ticket_data.subject is not None:
        ticket.subject = ticket_data.subject

    if ticket_data.description is not None:
        ticket.description = ticket_data.description

    if ticket_data.priority is not None:
        ticket.priority = ticket_data.priority

    if ticket_data.status is not None:
        ticket.status = ticket_data.status

    db.commit()
    db.refresh(ticket)

    return ticket


# ============================================================
# ASSIGN TICKET
# Manager/Admin only
# ============================================================

@router.patch(
    "/{ticket_id}/assign",
    response_model=TicketResponse,
)
def assign_ticket(
    ticket_id: int,
    assignment: TicketAssign,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Only manager and admin can assign tickets
    if current_user.role not in {
        "support_manager",
        "admin",
    }:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only support managers and admins can assign tickets",
        )

    ticket = (
        db.query(Ticket)
        .filter(Ticket.id == ticket_id)
        .first()
    )

    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found",
        )

    # Find assigned user
    agent = (
        db.query(User)
        .filter(User.id == assignment.assigned_agent_id)
        .first()
    )

    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assigned user not found",
        )

    # Must be a support agent
    if agent.role != "support_agent":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ticket can only be assigned to a support agent",
        )

    if not agent.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Support agent is inactive",
        )

    ticket.assigned_agent_id = agent.id

    # Automatically move ticket to in_progress
    if ticket.status == "open":
        ticket.status = "in_progress"

    db.commit()
    db.refresh(ticket)

    return ticket