from datetime import datetime, timedelta, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models import SLAPolicy, Ticket, User
from app.sla.schemas import (
    SLAPolicyCreate,
    SLAPolicyUpdate,
    SLAPolicyResponse,
    TicketSLAResponse,
)


router = APIRouter(
    prefix="/sla",
    tags=["SLA Management"],
)


# ============================================================
# ALLOWED VALUES
# ============================================================

ALLOWED_PRIORITIES = {
    "low",
    "medium",
    "high",
    "urgent",
}

MANAGER_ROLES = {
    "support_manager",
    "admin",
}


# ============================================================
# CREATE SLA POLICY
# ============================================================

@router.post(
    "/policies",
    response_model=SLAPolicyResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_sla_policy(
    policy_data: SLAPolicyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in MANAGER_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only support managers and admins can manage SLA policies",
        )

    if policy_data.priority not in ALLOWED_PRIORITIES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid priority",
        )

    existing_policy = (
        db.query(SLAPolicy)
        .filter(SLAPolicy.priority == policy_data.priority)
        .first()
    )

    if existing_policy:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An SLA policy already exists for this priority",
        )

    policy = SLAPolicy(
        priority=policy_data.priority,
        first_response_minutes=policy_data.first_response_minutes,
        resolution_minutes=policy_data.resolution_minutes,
        is_active=policy_data.is_active,
    )

    db.add(policy)
    db.commit()
    db.refresh(policy)

    return policy


# ============================================================
# LIST SLA POLICIES
# ============================================================

@router.get(
    "/policies",
    response_model=List[SLAPolicyResponse],
)
def list_sla_policies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in MANAGER_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only support managers and admins can view SLA policies",
        )

    return (
        db.query(SLAPolicy)
        .order_by(SLAPolicy.priority.asc())
        .all()
    )


# ============================================================
# UPDATE SLA POLICY
# ============================================================

@router.put(
    "/policies/{policy_id}",
    response_model=SLAPolicyResponse,
)
def update_sla_policy(
    policy_id: int,
    policy_data: SLAPolicyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in MANAGER_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only support managers and admins can update SLA policies",
        )

    policy = (
        db.query(SLAPolicy)
        .filter(SLAPolicy.id == policy_id)
        .first()
    )

    if policy is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SLA policy not found",
        )

    if policy_data.priority is not None:

        if policy_data.priority not in ALLOWED_PRIORITIES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid priority",
            )

        duplicate = (
            db.query(SLAPolicy)
            .filter(
                SLAPolicy.priority == policy_data.priority,
                SLAPolicy.id != policy_id,
            )
            .first()
        )

        if duplicate:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An SLA policy already exists for this priority",
            )

        policy.priority = policy_data.priority

    if policy_data.first_response_minutes is not None:
        policy.first_response_minutes = (
            policy_data.first_response_minutes
        )

    if policy_data.resolution_minutes is not None:
        policy.resolution_minutes = (
            policy_data.resolution_minutes
        )

    if policy_data.is_active is not None:
        policy.is_active = policy_data.is_active

    db.commit()
    db.refresh(policy)

    return policy


# ============================================================
# DELETE SLA POLICY
# ============================================================

@router.delete(
    "/policies/{policy_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_sla_policy(
    policy_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in MANAGER_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only support managers and admins can delete SLA policies",
        )

    policy = (
        db.query(SLAPolicy)
        .filter(SLAPolicy.id == policy_id)
        .first()
    )

    if policy is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SLA policy not found",
        )

    db.delete(policy)
    db.commit()

    return None


# ============================================================
# GET TICKET SLA
# ============================================================

@router.get(
    "/tickets/{ticket_id}/sla",
    response_model=TicketSLAResponse,
)
def get_ticket_sla(
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

    # --------------------------------------------------------
    # Check ticket access
    # --------------------------------------------------------

    if current_user.role == "customer":

        if ticket.customer_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to view this ticket",
            )

    elif current_user.role == "support_agent":

        if ticket.assigned_agent_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to view this ticket",
            )

    elif current_user.role not in {
        "support_manager",
        "admin",
    }:

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view this ticket",
        )

    # --------------------------------------------------------
    # Find active SLA policy
    # --------------------------------------------------------

    policy = (
        db.query(SLAPolicy)
        .filter(
            SLAPolicy.priority == ticket.priority,
            SLAPolicy.is_active.is_(True),
        )
        .first()
    )

    # --------------------------------------------------------
    # If no SLA policy exists
    # --------------------------------------------------------

    if policy is None:

        return TicketSLAResponse(
            ticket_id=ticket.id,
            priority=ticket.priority,
            status=ticket.status,
            first_response_deadline=ticket.first_response_deadline,
            resolution_deadline=ticket.resolution_deadline,
            first_response_time=ticket.first_response_time,
            resolution_time=ticket.resolution_time,
            sla_status=ticket.sla_status,
        )

    # --------------------------------------------------------
    # Calculate deadlines if they don't exist
    # --------------------------------------------------------

    if (
        ticket.first_response_deadline is None
        or ticket.resolution_deadline is None
    ):

        created_at = ticket.created_at

        if created_at is None:
            created_at = datetime.now(timezone.utc)

        ticket.first_response_deadline = (
            created_at
            + timedelta(minutes=policy.first_response_minutes)
        )

        ticket.resolution_deadline = (
            created_at
            + timedelta(minutes=policy.resolution_minutes)
        )

        ticket.sla_status = calculate_sla_status(ticket)

        db.commit()
        db.refresh(ticket)

    else:
        # Refresh SLA status when the endpoint is called
        ticket.sla_status = calculate_sla_status(ticket)

        db.commit()
        db.refresh(ticket)

    return TicketSLAResponse(
        ticket_id=ticket.id,
        priority=ticket.priority,
        status=ticket.status,
        first_response_deadline=ticket.first_response_deadline,
        resolution_deadline=ticket.resolution_deadline,
        first_response_time=ticket.first_response_time,
        resolution_time=ticket.resolution_time,
        sla_status=ticket.sla_status,
    )


# ============================================================
# SLA STATUS CALCULATION
# ============================================================

def calculate_sla_status(ticket: Ticket) -> str:
    """
    Calculate current SLA status.

    Possible values:

    within_sla
    at_risk
    breached
    completed
    """

    # --------------------------------------------------------
    # Resolved/closed tickets
    # --------------------------------------------------------

    if ticket.status in {
        "resolved",
        "closed",
    }:

        return "completed"

    now = datetime.now(timezone.utc)

    # --------------------------------------------------------
    # Resolution deadline breached
    # --------------------------------------------------------

    if (
        ticket.resolution_deadline is not None
        and now > ticket.resolution_deadline
    ):

        return "breached"

    # --------------------------------------------------------
    # First response deadline breached
    # --------------------------------------------------------

    if (
        ticket.first_response_time is None
        and ticket.first_response_deadline is not None
        and now > ticket.first_response_deadline
    ):

        return "breached"

    # --------------------------------------------------------
    # At-risk calculation
    #
    # At risk when 80% or more of the allowed time has passed.
    # --------------------------------------------------------

    if ticket.created_at is not None:

        total_resolution_seconds = 0

        if ticket.resolution_deadline is not None:
            total_resolution_seconds = (
                ticket.resolution_deadline
                - ticket.created_at
            ).total_seconds()

        elapsed_seconds = (
            now - ticket.created_at
        ).total_seconds()

        if (
            total_resolution_seconds > 0
            and elapsed_seconds
            >= total_resolution_seconds * 0.80
        ):

            return "at_risk"

    return "within_sla"