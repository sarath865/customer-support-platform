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