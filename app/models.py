from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


# ============================================================
# USER MODEL
# ============================================================

class User(Base):
    __tablename__ = "users"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    full_name = Column(
        String(150),
        nullable=False,
    )

    email = Column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )

    phone_number = Column(
        String(20),
        nullable=True,
    )

    password_hash = Column(
        String(255),
        nullable=False,
    )

    role = Column(
        String(30),
        nullable=False,
        default="customer",
    )

    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Tickets created by this user
    tickets = relationship(
        "Ticket",
        foreign_keys="Ticket.customer_id",
        back_populates="customer",
    )

    # Tickets assigned to this user
    assigned_tickets = relationship(
        "Ticket",
        foreign_keys="Ticket.assigned_agent_id",
        back_populates="assigned_agent",
    )

    # Comments written by this user
    comments = relationship(
        "TicketComment",
        foreign_keys="TicketComment.user_id",
        back_populates="user",
    )

    # Messages written by this user
    messages = relationship(
        "TicketMessage",
        foreign_keys="TicketMessage.user_id",
        back_populates="user",
    )

    # Audit logs created by this user
    audit_logs = relationship(
        "AuditLog",
        foreign_keys="AuditLog.user_id",
        back_populates="user",
    )


# ============================================================
# SLA POLICY MODEL
# ============================================================

class SLAPolicy(Base):
    __tablename__ = "sla_policies"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    # Priority to which this SLA policy applies
    priority = Column(
        String(20),
        unique=True,
        nullable=False,
        index=True,
    )

    # Maximum time allowed for first response
    first_response_minutes = Column(
        Integer,
        nullable=False,
    )

    # Maximum time allowed for ticket resolution
    resolution_minutes = Column(
        Integer,
        nullable=False,
    )

    # Whether this SLA policy is currently active
    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


# ============================================================
# TICKET MODEL
# ============================================================

class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    customer_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    assigned_agent_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    subject = Column(
        String(200),
        nullable=False,
    )

    description = Column(
        Text,
        nullable=False,
    )

    priority = Column(
        String(20),
        nullable=False,
        default="medium",
    )

    status = Column(
        String(20),
        nullable=False,
        default="open",
    )

    # ========================================================
    # SLA TRACKING
    # ========================================================

    # Deadline by which first response must happen
    first_response_deadline = Column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    # Deadline by which ticket should be resolved
    resolution_deadline = Column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    # Actual first response time
    first_response_time = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Actual resolution time
    resolution_time = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Current SLA state
    # within_sla / at_risk / breached / completed
    sla_status = Column(
        String(20),
        nullable=False,
        default="within_sla",
        index=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Customer who created the ticket
    customer = relationship(
        "User",
        foreign_keys=[customer_id],
        back_populates="tickets",
    )

    # Support agent assigned to the ticket
    assigned_agent = relationship(
        "User",
        foreign_keys=[assigned_agent_id],
        back_populates="assigned_tickets",
    )

    # Comments/replies on this ticket
    comments = relationship(
        "TicketComment",
        back_populates="ticket",
        cascade="all, delete-orphan",
    )

    # Conversation messages on this ticket
    messages = relationship(
        "TicketMessage",
        back_populates="ticket",
        cascade="all, delete-orphan",
    )

    # Audit/history records for this ticket
    audit_logs = relationship(
        "AuditLog",
        foreign_keys="AuditLog.ticket_id",
        back_populates="ticket",
        cascade="all, delete-orphan",
    )


# ============================================================
# TICKET COMMENT MODEL
# ============================================================

class TicketComment(Base):
    __tablename__ = "ticket_comments"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    ticket_id = Column(
        Integer,
        ForeignKey("tickets.id"),
        nullable=False,
        index=True,
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    comment = Column(
        Text,
        nullable=False,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Ticket this comment belongs to
    ticket = relationship(
        "Ticket",
        back_populates="comments",
    )

    # User who wrote the comment
    user = relationship(
        "User",
        foreign_keys=[user_id],
        back_populates="comments",
    )


# ============================================================
# TICKET MESSAGE MODEL
# ============================================================

class TicketMessage(Base):
    __tablename__ = "ticket_messages"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    ticket_id = Column(
        Integer,
        ForeignKey("tickets.id"),
        nullable=False,
        index=True,
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    message = Column(
        Text,
        nullable=False,
    )

    # customer_reply
    # agent_reply
    # system_message
    # internal_note
    message_type = Column(
        String(30),
        nullable=False,
        default="agent_reply",
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Ticket this message belongs to
    ticket = relationship(
        "Ticket",
        back_populates="messages",
    )

    # User who sent this message
    user = relationship(
        "User",
        foreign_keys=[user_id],
        back_populates="messages",
    )


# ============================================================
# AUDIT LOG MODEL
# ============================================================

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    # User who performed the action
    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    # Ticket associated with the action
    ticket_id = Column(
        Integer,
        ForeignKey("tickets.id"),
        nullable=True,
        index=True,
    )

    # Action performed
    # Examples:
    # ticket_created
    # ticket_updated
    # ticket_assigned
    # ticket_reassigned
    # status_changed
    # priority_changed
    # comment_added
    # message_sent
    action = Column(
        String(50),
        nullable=False,
        index=True,
    )

    # Human-readable description
    description = Column(
        Text,
        nullable=False,
    )

    # Previous value, if applicable
    old_value = Column(
        Text,
        nullable=True,
    )

    # New value, if applicable
    new_value = Column(
        Text,
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # User who performed the action
    user = relationship(
        "User",
        foreign_keys=[user_id],
        back_populates="audit_logs",
    )

    # Ticket associated with the action
    ticket = relationship(
        "Ticket",
        foreign_keys=[ticket_id],
        back_populates="audit_logs",
    )

# ============================================================
# NOTIFICATION MODEL
# ============================================================

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    # User who should receive the notification
    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    # Optional ticket associated with the notification
    ticket_id = Column(
        Integer,
        ForeignKey("tickets.id"),
        nullable=True,
        index=True,
    )

    # Notification type
    # Examples:
    # ticket_created
    # ticket_assigned
    # ticket_updated
    # new_message
    # status_changed
    # sla_warning
    # sla_breached
    notification_type = Column(
        String(50),
        nullable=False,
        index=True,
    )

    # Notification title
    title = Column(
        String(200),
        nullable=False,
    )

    # Notification message
    message = Column(
        Text,
        nullable=False,
    )

    # Whether the user has read the notification
    is_read = Column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # User receiving the notification
    user = relationship(
        "User",
        foreign_keys=[user_id],
    )

    # Related ticket
    ticket = relationship(
        "Ticket",
        foreign_keys=[ticket_id],
    )