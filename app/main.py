from fastapi import FastAPI

from app.auth.router import router as auth_router
from app.tickets.router import router as ticket_router
from app.sla.router import router as sla_router
from app.audit.router import router as audit_router
from app.dashboard.router import router as dashboard_router
from app.notifications.router import router as notification_router


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="Customer Support & Helpdesk Management Platform",
    description="Backend API for customer support and helpdesk management",
    version="1.0.0",
)


# ============================================================
# AUTHENTICATION APIs
# ============================================================

app.include_router(auth_router)


# ============================================================
# TICKET APIs
# ============================================================

app.include_router(ticket_router)


# ============================================================
# SLA MANAGEMENT APIs
# ============================================================

app.include_router(sla_router)


# ============================================================
# AUDIT & TICKET HISTORY APIs
# ============================================================

app.include_router(audit_router)


# ============================================================
# DASHBOARD & STATISTICS APIs
# ============================================================

app.include_router(dashboard_router)

# ============================================================
# NOTIFICATION APIs
# ============================================================

app.include_router(notification_router)


# ============================================================
# ROOT ENDPOINT
# ============================================================

@app.get("/")
def root():
    return {
        "message": "Customer Support & Helpdesk Management Platform API",
        "status": "running",
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
    }