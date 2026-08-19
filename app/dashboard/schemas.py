from typing import Dict

from pydantic import BaseModel


# ============================================================
# DASHBOARD SUMMARY
# ============================================================

class DashboardSummaryResponse(BaseModel):
    total_tickets: int

    open_tickets: int
    in_progress_tickets: int
    resolved_tickets: int
    closed_tickets: int

    low_priority_tickets: int
    medium_priority_tickets: int
    high_priority_tickets: int
    urgent_priority_tickets: int

    within_sla_tickets: int
    at_risk_tickets: int
    breached_tickets: int


# ============================================================
# SLA SUMMARY
# ============================================================

class DashboardSLASummaryResponse(BaseModel):
    total_tickets: int
    within_sla: int
    at_risk: int
    breached: int
    completed: int
    no_policy: int


# ============================================================
# AGENT WORKLOAD
# ============================================================

class AgentWorkloadResponse(BaseModel):
    agent_id: int
    agent_name: str
    email: str

    total_assigned: int
    open_tickets: int
    in_progress_tickets: int
    resolved_tickets: int
    closed_tickets: int


# ============================================================
# TICKET STATISTICS
# ============================================================

class TicketStatisticsResponse(BaseModel):
    by_status: Dict[str, int]
    by_priority: Dict[str, int]
    by_sla_status: Dict[str, int]