from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AuditLog, Ticket, User
from app.auth.dependencies import get_current_user
from app.audit.schemas import AuditLogResponse


router = APIRouter(
    prefix="/audit",
    tags=["Audit & Ticket History"],
)


@router.get(
    "/logs",
    response_model=List[AuditLogResponse],
)
def list_audit_logs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in {
        "admin",
        "support_manager",
    }:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and support managers can view audit logs",
        )

    logs = (
        db.query(AuditLog)
        .order_by(AuditLog.created_at.desc())
        .all()
    )

    return logs


@router.get(
    "/tickets/{ticket_id}",
    response_model=List[AuditLogResponse],
)
def get_ticket_audit_history(
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

    if current_user.role == "customer":

        if ticket.customer_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view history of your own tickets",
            )

    elif current_user.role == "support_agent":

        if ticket.assigned_agent_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view history of tickets assigned to you",
            )

    elif current_user.role not in {
        "support_manager",
        "admin",
    }:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view ticket history",
        )

    logs = (
        db.query(AuditLog)
        .filter(AuditLog.ticket_id == ticket_id)
        .order_by(AuditLog.created_at.asc())
        .all()
    )

    return logs