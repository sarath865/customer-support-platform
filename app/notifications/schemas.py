from datetime import datetime
from typing import Optional

from pydantic import BaseModel


# ============================================================
# NOTIFICATION RESPONSE
# ============================================================

class NotificationResponse(BaseModel):
    id: int
    user_id: int
    ticket_id: Optional[int] = None
    notification_type: str
    title: str
    message: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================
# UNREAD COUNT
# ============================================================

class NotificationCountResponse(BaseModel):
    unread_count: int