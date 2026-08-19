from datetime import datetime, timedelta, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import (
    Ticket,
    User,
    TicketComment,
    TicketMessage,
    SLAPolicy,
    AuditLog,
)
from app.auth.dependencies import get_current_user
from app.tickets.schemas import (
    TicketCreate,
    TicketUpdate,
    TicketAssign,
    TicketResponse,
    TicketCommentCreate,
    TicketCommentResponse,
    TicketMessageCreate,
    TicketMessageUpdate,
    TicketMessageResponse,
)


router = APIRouter(
    prefix="/tickets",
    tags=["Tickets"],
)


# ============================================================
# AUDIT LOG HELPER
# ============================================================

def create_audit_log(
    db: Session,
    user_id: int,
    ticket_id: int | None,
    action: str,
    description: str,
    old_value: str | None = None,
    new_value: str | None = None,
):
    """
    Create an audit/history record.

    The record is added to the current database transaction.
    The calling endpoint is responsible for committing it.
    """

    audit_log = AuditLog(
        user_id=user_id,
        ticket_id=ticket_id,
        action=action,
        description=description,
        old_value=old_value,
        new_value=new_value,
    )

    db.add(audit_log)

    return audit_log


# ============================================================
# SLA CALCULATION
# ============================================================

def calculate_ticket_sla(
    ticket: Ticket,
    db: Session,
):
    """
    Calculate SLA deadlines based on the ticket priority.
    """

    sla_policy = (
        db.query(SLAPolicy)
        .filter(
            SLAPolicy.priority == ticket.priority,
            SLAPolicy.is_active == True,
        )
        .first()
    )

    if sla_policy is None:
        ticket.first_response_deadline = None
        ticket.resolution_deadline = None
        ticket.sla_status = "no_policy"
        return

    created_time = ticket.created_at

    if created_time is None:
        created_time = datetime.now(timezone.utc)

    ticket.first_response_deadline = (
        created_time
        + timedelta(minutes=sla_policy.first_response_minutes)
    )

    ticket.resolution_deadline = (
        created_time
        + timedelta(minutes=sla_policy.resolution_minutes)
    )

    ticket.sla_status = "active"


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
    if current_user.role != "customer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only customers can create tickets",
        )

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
        sla_status="active",
    )

    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    calculate_ticket_sla(ticket, db)

    create_audit_log(
        db=db,
        user_id=current_user.id,
        ticket_id=ticket.id,
        action="ticket_created",
        description="Ticket created by customer",
        new_value=(
            f"priority={ticket.priority}, "
            f"status={ticket.status}"
        ),
    )

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
    # Customer -> own tickets
    if current_user.role == "customer":
        return (
            db.query(Ticket)
            .filter(Ticket.customer_id == current_user.id)
            .order_by(Ticket.created_at.desc())
            .all()
        )

    # Support agent -> assigned tickets
    if current_user.role == "support_agent":
        return (
            db.query(Ticket)
            .filter(Ticket.assigned_agent_id == current_user.id)
            .order_by(Ticket.created_at.desc())
            .all()
        )

    # Manager/Admin -> all tickets
    if current_user.role in {
        "support_manager",
        "admin",
    }:
        return (
            db.query(Ticket)
            .order_by(Ticket.created_at.desc())
            .all()
        )

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

    # Customer -> own ticket only
    if current_user.role == "customer":
        if ticket.customer_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to view this ticket",
            )

    # Agent -> assigned ticket only
    elif current_user.role == "support_agent":
        if ticket.assigned_agent_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to view this ticket",
            )

    # Manager/Admin -> all tickets
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

    # Customer restrictions
    if current_user.role == "customer":
        if ticket.customer_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own tickets",
            )

        if ticket_data.status is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Customers cannot change ticket status",
            )

    # Agent restrictions
    if current_user.role == "support_agent":
        if ticket.assigned_agent_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update tickets assigned to you",
            )

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

    # Store old values for audit history
    old_subject = ticket.subject
    old_description = ticket.description
    old_priority = ticket.priority
    old_status = ticket.status

    if ticket_data.subject is not None:
        ticket.subject = ticket_data.subject

    if ticket_data.description is not None:
        ticket.description = ticket_data.description

    priority_changed = False

    if ticket_data.priority is not None:
        ticket.priority = ticket_data.priority
        priority_changed = old_priority != ticket.priority

    if ticket_data.status is not None:
        ticket.status = ticket_data.status

    if priority_changed:
        calculate_ticket_sla(ticket, db)

    # Audit: subject changed
    if (
        ticket_data.subject is not None
        and old_subject != ticket.subject
    ):
        create_audit_log(
            db=db,
            user_id=current_user.id,
            ticket_id=ticket.id,
            action="ticket_updated",
            description="Ticket subject updated",
            old_value=old_subject,
            new_value=ticket.subject,
        )

    # Audit: description changed
    if (
        ticket_data.description is not None
        and old_description != ticket.description
    ):
        create_audit_log(
            db=db,
            user_id=current_user.id,
            ticket_id=ticket.id,
            action="ticket_updated",
            description="Ticket description updated",
            old_value=old_description,
            new_value=ticket.description,
        )

    # Audit: priority changed
    if priority_changed:
        create_audit_log(
            db=db,
            user_id=current_user.id,
            ticket_id=ticket.id,
            action="priority_changed",
            description="Ticket priority changed",
            old_value=old_priority,
            new_value=ticket.priority,
        )

    # Audit: status changed
    if (
        ticket_data.status is not None
        and old_status != ticket.status
    ):
        create_audit_log(
            db=db,
            user_id=current_user.id,
            ticket_id=ticket.id,
            action="status_changed",
            description="Ticket status changed",
            old_value=old_status,
            new_value=ticket.status,
        )

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

    old_agent_id = ticket.assigned_agent_id

    ticket.assigned_agent_id = agent.id

    if ticket.status == "open":
        ticket.status = "in_progress"

    create_audit_log(
        db=db,
        user_id=current_user.id,
        ticket_id=ticket.id,
        action=(
            "ticket_reassigned"
            if old_agent_id is not None
            else "ticket_assigned"
        ),
        description="Ticket assigned to support agent",
        old_value=(
            str(old_agent_id)
            if old_agent_id is not None
            else None
        ),
        new_value=str(agent.id),
    )

    # If assignment automatically changed status
    if ticket.status == "in_progress":
        if old_agent_id is None:
            create_audit_log(
                db=db,
                user_id=current_user.id,
                ticket_id=ticket.id,
                action="status_changed",
                description="Ticket status changed after assignment",
                old_value="open",
                new_value="in_progress",
            )

    db.commit()
    db.refresh(ticket)

    return ticket


# ============================================================
# CREATE TICKET COMMENT
# ============================================================

@router.post(
    "/{ticket_id}/comments",
    response_model=TicketCommentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_ticket_comment(
    ticket_id: int,
    comment_data: TicketCommentCreate,
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
                detail="You can only comment on your own tickets",
            )

    elif current_user.role == "support_agent":
        if ticket.assigned_agent_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only comment on tickets assigned to you",
            )

    elif current_user.role not in {
        "support_manager",
        "admin",
    }:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to comment on tickets",
        )

    comment = TicketComment(
        ticket_id=ticket.id,
        user_id=current_user.id,
        comment=comment_data.comment,
    )

    db.add(comment)

    create_audit_log(
        db=db,
        user_id=current_user.id,
        ticket_id=ticket.id,
        action="comment_added",
        description="Ticket comment added",
        new_value=comment_data.comment,
    )

    db.commit()
    db.refresh(comment)

    return comment


# ============================================================
# LIST TICKET COMMENTS
# ============================================================

@router.get(
    "/{ticket_id}/comments",
    response_model=List[TicketCommentResponse],
)
def list_ticket_comments(
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
                detail="You do not have permission to view these comments",
            )

    elif current_user.role == "support_agent":
        if ticket.assigned_agent_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to view these comments",
            )

    elif current_user.role not in {
        "support_manager",
        "admin",
    }:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view these comments",
        )

    comments = (
        db.query(TicketComment)
        .filter(TicketComment.ticket_id == ticket_id)
        .order_by(TicketComment.created_at.asc())
        .all()
    )

    return comments


# ============================================================
# UPDATE TICKET COMMENT
# ============================================================

@router.patch(
    "/{ticket_id}/comments/{comment_id}",
    response_model=TicketCommentResponse,
)
def update_ticket_comment(
    ticket_id: int,
    comment_id: int,
    comment_data: TicketCommentCreate,
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

    comment = (
        db.query(TicketComment)
        .filter(
            TicketComment.id == comment_id,
            TicketComment.ticket_id == ticket_id,
        )
        .first()
    )

    if comment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found",
        )

    if current_user.role == "customer":
        if ticket.customer_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only edit comments on your own tickets",
            )

        if comment.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only edit your own comments",
            )

    elif current_user.role == "support_agent":
        if ticket.assigned_agent_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only edit comments on tickets assigned to you",
            )

        if comment.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only edit your own comments",
            )

    elif current_user.role not in {
        "support_manager",
        "admin",
    }:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to edit comments",
        )

    old_comment = comment.comment

    comment.comment = comment_data.comment

    create_audit_log(
        db=db,
        user_id=current_user.id,
        ticket_id=ticket.id,
        action="comment_updated",
        description="Ticket comment updated",
        old_value=old_comment,
        new_value=comment.comment,
    )

    db.commit()
    db.refresh(comment)

    return comment


# ============================================================
# DELETE TICKET COMMENT
# ============================================================

@router.delete(
    "/{ticket_id}/comments/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_ticket_comment(
    ticket_id: int,
    comment_id: int,
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

    comment = (
        db.query(TicketComment)
        .filter(
            TicketComment.id == comment_id,
            TicketComment.ticket_id == ticket_id,
        )
        .first()
    )

    if comment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found",
        )

    if current_user.role == "customer":
        if ticket.customer_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete comments on your own tickets",
            )

        if comment.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own comments",
            )

    elif current_user.role == "support_agent":
        if ticket.assigned_agent_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete comments on tickets assigned to you",
            )

        if comment.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own comments",
            )

    elif current_user.role not in {
        "support_manager",
        "admin",
    }:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete comments",
        )

    deleted_comment = comment.comment

    create_audit_log(
        db=db,
        user_id=current_user.id,
        ticket_id=ticket.id,
        action="comment_deleted",
        description="Ticket comment deleted",
        old_value=deleted_comment,
    )

    db.delete(comment)
    db.commit()

    return None


# ============================================================
# HELPER - CHECK TICKET ACCESS
# ============================================================

def check_ticket_message_access(
    ticket: Ticket,
    current_user: User,
):
    """
    Check whether the current user can access the ticket conversation.
    """

    # Customer -> own ticket only
    if current_user.role == "customer":

        if ticket.customer_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this ticket",
            )

    # Support agent -> assigned ticket only
    elif current_user.role == "support_agent":

        if ticket.assigned_agent_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this ticket",
            )

    # Manager/Admin -> all tickets
    elif current_user.role not in {
        "support_manager",
        "admin",
    }:

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this ticket",
        )


# ============================================================
# CREATE TICKET MESSAGE
# ============================================================

@router.post(
    "/{ticket_id}/messages",
    response_model=TicketMessageResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_ticket_message(
    ticket_id: int,
    message_data: TicketMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Find ticket
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

    # Check ticket access
    check_ticket_message_access(
        ticket,
        current_user,
    )

    allowed_message_types = {
        "customer_reply",
        "agent_reply",
        "system_message",
        "internal_note",
    }

    if message_data.message_type not in allowed_message_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Invalid message type. Allowed types: "
                "customer_reply, agent_reply, "
                "system_message, internal_note"
            ),
        )

    # Customer can only send customer replies
    if current_user.role == "customer":

        if message_data.message_type != "customer_reply":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Customers can only send customer replies",
            )

    # Support agent can send agent replies and internal notes
    elif current_user.role == "support_agent":

        if message_data.message_type not in {
            "agent_reply",
            "internal_note",
        }:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Support agents can only send "
                    "agent replies or internal notes"
                ),
            )

    # Manager/Admin can create all message types
    elif current_user.role in {
        "support_manager",
        "admin",
    }:
        pass

    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to send messages",
        )

    message = TicketMessage(
        ticket_id=ticket.id,
        user_id=current_user.id,
        message=message_data.message,
        message_type=message_data.message_type,
    )

    db.add(message)

    # ========================================================
    # FIRST RESPONSE SLA TRACKING
    # ========================================================

    if (
        current_user.role in {
            "support_agent",
            "support_manager",
            "admin",
        }
        and message_data.message_type == "agent_reply"
        and ticket.first_response_time is None
    ):
        response_time = datetime.now(timezone.utc)

        ticket.first_response_time = response_time

        if (
            ticket.first_response_deadline is not None
            and response_time <= ticket.first_response_deadline
        ):
            ticket.sla_status = "within_sla"
        else:
            ticket.sla_status = "breached"

    create_audit_log(
        db=db,
        user_id=current_user.id,
        ticket_id=ticket.id,
        action="message_sent",
        description="Ticket conversation message sent",
        new_value=(
            f"type={message_data.message_type}"
        ),
    )

    db.commit()
    db.refresh(message)

    return message


# ============================================================
# LIST TICKET MESSAGES
# ============================================================

@router.get(
    "/{ticket_id}/messages",
    response_model=List[TicketMessageResponse],
)
def list_ticket_messages(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Find ticket
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

    # Check ticket access
    check_ticket_message_access(
        ticket,
        current_user,
    )

    query = (
        db.query(TicketMessage)
        .filter(TicketMessage.ticket_id == ticket_id)
    )

    # Customers must NOT see internal notes
    if current_user.role == "customer":

        query = query.filter(
            TicketMessage.message_type != "internal_note"
        )

    messages = (
        query
        .order_by(TicketMessage.created_at.asc())
        .all()
    )

    return messages


# ============================================================
# UPDATE TICKET MESSAGE
# ============================================================

@router.put(
    "/messages/{message_id}",
    response_model=TicketMessageResponse,
)
def update_ticket_message(
    message_id: int,
    message_data: TicketMessageUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Find message
    message = (
        db.query(TicketMessage)
        .filter(TicketMessage.id == message_id)
        .first()
    )

    if message is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found",
        )

    # Find ticket
    ticket = (
        db.query(Ticket)
        .filter(Ticket.id == message.ticket_id)
        .first()
    )

    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found",
        )

    # Customer can edit own messages only
    if current_user.role == "customer":

        if ticket.customer_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to edit this message",
            )

        if message.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only edit your own messages",
            )

    # Support agent can edit own messages on assigned tickets
    elif current_user.role == "support_agent":

        if ticket.assigned_agent_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only edit messages on tickets assigned to you",
            )

        if message.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only edit your own messages",
            )

    # Manager/Admin can edit any message
    elif current_user.role in {
        "support_manager",
        "admin",
    }:
        pass

    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to edit messages",
        )

    # System messages should not be manually edited
    if message.message_type == "system_message":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="System messages cannot be edited",
        )

    old_message = message.message

    message.message = message_data.message

    create_audit_log(
        db=db,
        user_id=current_user.id,
        ticket_id=ticket.id,
        action="message_updated",
        description="Ticket message updated",
        old_value=old_message,
        new_value=message.message,
    )

    db.commit()
    db.refresh(message)

    return message


# ============================================================
# DELETE TICKET MESSAGE
# ============================================================

@router.delete(
    "/messages/{message_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_ticket_message(
    message_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Find message
    message = (
        db.query(TicketMessage)
        .filter(TicketMessage.id == message_id)
        .first()
    )

    if message is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found",
        )

    # Find ticket
    ticket = (
        db.query(Ticket)
        .filter(Ticket.id == message.ticket_id)
        .first()
    )

    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found",
        )

    # System messages cannot be deleted
    if message.message_type == "system_message":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="System messages cannot be deleted",
        )

    # Customer can delete own messages only
    if current_user.role == "customer":

        if ticket.customer_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to delete this message",
            )

        if message.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own messages",
            )

    # Support agent can delete own messages on assigned tickets
    elif current_user.role == "support_agent":

        if ticket.assigned_agent_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete messages on tickets assigned to you",
            )

        if message.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own messages",
            )

    # Manager/Admin can delete any non-system message
    elif current_user.role in {
        "support_manager",
        "admin",
    }:
        pass

    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete messages",
        )

    deleted_message = message.message

    create_audit_log(
        db=db,
        user_id=current_user.id,
        ticket_id=ticket.id,
        action="message_deleted",
        description="Ticket message deleted",
        old_value=deleted_message,
    )

    db.delete(message)
    db.commit()

    return None