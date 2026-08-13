from fastapi import FastAPI

from app.auth.router import router as auth_router


app = FastAPI(
    title="Customer Support & Helpdesk Management Platform",
    description="Backend API for customer support and helpdesk management",
    version="1.0.0",
)


app.include_router(auth_router)


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