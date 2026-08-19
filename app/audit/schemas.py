from datetime import datetime
from typing import Optional

from pydantic import BaseModel


# ============================================================
# AUDIT LOG RESPONSE
# ============================================================

class AuditLogResponse(BaseModel):
    id: int

    user_id: Optional[int] = None

    ticket_id: Optional[int] = None

    action: str

    description: str

    old_value: Optional[str] = None

    new_value: Optional[str] = None

    created_at: datetime

    class Config:
        from_attributes = True