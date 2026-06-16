from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TaskState(str, Enum):
    CREATED = "CREATED"
    PLANNED = "PLANNED"
    ASSIGNED = "ASSIGNED"
    RUNNING = "RUNNING"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    VERIFYING = "VERIFYING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    PAID = "PAID"
    DISPUTED = "DISPUTED"


class ConnectorMode(str, Enum):
    API = "api"
    BROWSER_AUTOMATION = "browser_automation"
    MANUAL_SESSION_REQUIRED = "manual_session_required"
    UNAVAILABLE = "unavailable"


class OpportunityType(str, Enum):
    BUG_BOUNTY = "bug_bounty"
    VDP = "vdp"
    CHALLENGE = "challenge"
    OPEN_SOURCE_TASK = "open_source_task"
    RESEARCH_TASK = "research_task"


class PayoutState(str, Enum):
    NOT_STARTED = "not_started"
    PENDING_SUBMISSION = "pending_submission"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    DISPUTED = "disputed"
    PAYOUT_PENDING = "payout_pending"
    PAID = "paid"
    FAILED = "failed"


class ConnectorStatus(BaseModel):
    platform: str
    module_present: bool = True
    mode: ConnectorMode
    auth_requirement: str
    ingest_ready: bool = False
    submission_ready: bool = False
    payout_tracking_ready: bool = False
    notes: Optional[str] = None


class Opportunity(BaseModel):
    id: str
    platform: str
    title: str
    description: str
    url: Optional[str] = None
    opportunity_type: OpportunityType = OpportunityType.BUG_BOUNTY
    reward_amount: Optional[float] = None
    reward_currency: Optional[str] = None
    payout_speed_days: Optional[int] = None
    platform_trust_score: float = 0.5
    skill_match_score: float = 0.5
    execution_complexity: float = 0.5
    confidence_score: float = 0.5
    risk_score: float = 0.5
    eligibility_clear: bool = False
    requires_manual_login: bool = False
    tags: List[str] = Field(default_factory=list)
    raw: Dict[str, Any] = Field(default_factory=dict)


class OpportunityScore(BaseModel):
    opportunity_id: str
    total_score: float
    reward_score: float
    trust_score: float
    speed_score: float
    fit_score: float
    clarity_score: float
    risk_penalty: float
    recommendation: str
    reasons: List[str] = Field(default_factory=list)


class ExecutionDecision(BaseModel):
    opportunity_id: str
    action: str
    why: List[str] = Field(default_factory=list)
    requires_human_approval: bool = False
    next_best_action: Optional[str] = None


class EvidencePack(BaseModel):
    opportunity_id: str
    summary: str
    screenshots: List[str] = Field(default_factory=list)
    files: List[str] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)
    completeness_score: float = 0.0


class PayoutRecord(BaseModel):
    opportunity_id: str
    platform: str
    state: PayoutState = PayoutState.NOT_STARTED
    expected_amount: Optional[float] = None
    currency: Optional[str] = None
    submitted_at: Optional[str] = None
    updated_at: Optional[str] = None
    payout_reference: Optional[str] = None
    notes: List[str] = Field(default_factory=list)


class MemorySignal(BaseModel):
    key: str
    value: str
    weight: float = 1.0
    source: str = "system"


class BrowserJob(BaseModel):
    id: str
    task: str
    allowed_domains: List[str] = Field(default_factory=list)
    headless: bool = True
    status: str = "queued"
    result: Dict[str, Any] = Field(default_factory=dict)
