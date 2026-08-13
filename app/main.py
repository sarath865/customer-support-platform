from fastapi import FastAPI

from app.auth.router import router as auth_router
from app.tickets.router import router as ticket_router


app = FastAPI(
    title="Customer Support & Helpdesk Management Platform",
    description="Backend API for customer support and helpdesk management",
    version="1.0.0",
)


# Authentication APIs
app.include_router(auth_router)

# Ticket APIs
app.include_router(ticket_router)


@app.get("/")
def root():
    return {
        "message": "Customer Support & Helpdesk Management Platform API",
        "status": "running",
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }