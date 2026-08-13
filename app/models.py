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