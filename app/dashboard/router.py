from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Ticket, User
from app.auth.dependencies import get_current_user
from app.dashboard.schemas import (
    DashboardSummaryResponse,
    DashboardSLASummaryResponse,
    AgentWorkloadResponse,
    TicketStatisticsResponse,
)


router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard & Statistics"],
)


# ============================================================
# PERMISSION HELPER
# ============================================================

def check_dashboard_access(current_user: User):
    if current_user.role not in {
        "admin",
        "support_manager",
    }:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Only admins and support managers "
                "can access dashboard statistics"
            ),
        )


# ============================================================
# DASHBOARD SUMMARY
# ============================================================

@router.get(
    "/summary",
    response_model=DashboardSummaryResponse,
)
def dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check_dashboard_access(current_user)

    total_tickets = db.query(Ticket).count()

    open_tickets = (
        db.query(Ticket)
        .filter(Ticket.status == "open")
        .count()
    )

    in_progress_tickets = (
        db.query(Ticket)
        .filter(Ticket.status == "in_progress")
        .count()
    )

    resolved_tickets = (
        db.query(Ticket)
        .filter(Ticket.status == "resolved")
        .count()
    )

    closed_tickets = (
        db.query(Ticket)
        .filter(Ticket.status == "closed")
        .count()
    )

    low_priority_tickets = (
        db.query(Ticket)
        .filter(Ticket.priority == "low")
        .count()
    )

    medium_priority_tickets = (
        db.query(Ticket)
        .filter(Ticket.priority == "medium")
        .count()
    )

    high_priority_tickets = (
        db.query(Ticket)
        .filter(Ticket.priority == "high")
        .count()
    )

    urgent_priority_tickets = (
        db.query(Ticket)
        .filter(Ticket.priority == "urgent")
        .count()
    )

    within_sla_tickets = (
        db.query(Ticket)
        .filter(Ticket.sla_status == "within_sla")
        .count()
    )

    at_risk_tickets = (
        db.query(Ticket)
        .filter(Ticket.sla_status == "at_risk")
        .count()
    )

    breached_tickets = (
        db.query(Ticket)
        .filter(Ticket.sla_status == "breached")
        .count()
    )

    return DashboardSummaryResponse(
        total_tickets=total_tickets,

        open_tickets=open_tickets,
        in_progress_tickets=in_progress_tickets,
        resolved_tickets=resolved_tickets,
        closed_tickets=closed_tickets,

        low_priority_tickets=low_priority_tickets,
        medium_priority_tickets=medium_priority_tickets,
        high_priority_tickets=high_priority_tickets,
        urgent_priority_tickets=urgent_priority_tickets,

        within_sla_tickets=within_sla_tickets,
        at_risk_tickets=at_risk_tickets,
        breached_tickets=breached_tickets,
    )


# ============================================================
# SLA SUMMARY
# ============================================================

@router.get(
    "/sla",
    response_model=DashboardSLASummaryResponse,
)
def dashboard_sla_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check_dashboard_access(current_user)

    total_tickets = db.query(Ticket).count()

    within_sla = (
        db.query(Ticket)
        .filter(Ticket.sla_status == "within_sla")
        .count()
    )

    at_risk = (
        db.query(Ticket)
        .filter(Ticket.sla_status == "at_risk")
        .count()
    )

    breached = (
        db.query(Ticket)
        .filter(Ticket.sla_status == "breached")
        .count()
    )

    completed = (
        db.query(Ticket)
        .filter(Ticket.sla_status == "completed")
        .count()
    )

    no_policy = (
        db.query(Ticket)
        .filter(Ticket.sla_status == "no_policy")
        .count()
    )

    return DashboardSLASummaryResponse(
        total_tickets=total_tickets,
        within_sla=within_sla,
        at_risk=at_risk,
        breached=breached,
        completed=completed,
        no_policy=no_policy,
    )


# ============================================================
# TICKET STATISTICS
# ============================================================

@router.get(
    "/tickets",
    response_model=TicketStatisticsResponse,
)
def ticket_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check_dashboard_access(current_user)

    status_rows = (
        db.query(
            Ticket.status,
            func.count(Ticket.id),
        )
        .group_by(Ticket.status)
        .all()
    )

    priority_rows = (
        db.query(
            Ticket.priority,
            func.count(Ticket.id),
        )
        .group_by(Ticket.priority)
        .all()
    )

    sla_rows = (
        db.query(
            Ticket.sla_status,
            func.count(Ticket.id),
        )
        .group_by(Ticket.sla_status)
        .all()
    )

    return TicketStatisticsResponse(
        by_status={
            str(ticket_status): count
            for ticket_status, count in status_rows
        },
        by_priority={
            str(priority): count
            for priority, count in priority_rows
        },
        by_sla_status={
            str(sla_status): count
            for sla_status, count in sla_rows
        },
    )


# ============================================================
# AGENT WORKLOAD
# ============================================================

@router.get(
    "/agents",
    response_model=List[AgentWorkloadResponse],
)
def agent_workload(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check_dashboard_access(current_user)

    agents = (
        db.query(User)
        .filter(
            User.role == "support_agent",
            User.is_active == True,
        )
        .order_by(User.id)
        .all()
    )

    result = []

    for agent in agents:

        total_assigned = (
            db.query(Ticket)
            .filter(
                Ticket.assigned_agent_id == agent.id
            )
            .count()
        )

        open_tickets = (
            db.query(Ticket)
            .filter(
                Ticket.assigned_agent_id == agent.id,
                Ticket.status == "open",
            )
            .count()
        )

        in_progress_tickets = (
            db.query(Ticket)
            .filter(
                Ticket.assigned_agent_id == agent.id,
                Ticket.status == "in_progress",
            )
            .count()
        )

        resolved_tickets = (
            db.query(Ticket)
            .filter(
                Ticket.assigned_agent_id == agent.id,
                Ticket.status == "resolved",
            )
            .count()
        )

        closed_tickets = (
            db.query(Ticket)
            .filter(
                Ticket.assigned_agent_id == agent.id,
                Ticket.status == "closed",
            )
            .count()
        )

        result.append(
            AgentWorkloadResponse(
                agent_id=agent.id,
                agent_name=agent.full_name,
                email=agent.email,
                total_assigned=total_assigned,
                open_tickets=open_tickets,
                in_progress_tickets=in_progress_tickets,
                resolved_tickets=resolved_tickets,
                closed_tickets=closed_tickets,
            )
        )

    return result