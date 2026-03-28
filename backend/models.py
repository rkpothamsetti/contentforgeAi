"""Pydantic models for ContentForge AI pipeline."""

from __future__ import annotations
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
import uuid, datetime


# ── Enums ────────────────────────────────────────────────────────────────────

class ContentFormat(str, Enum):
    BLOG_POST = "blog_post"
    SOCIAL_MEDIA = "social_media"
    EMAIL_NEWSLETTER = "email_newsletter"
    PRESS_RELEASE = "press_release"
    SALES_COLLATERAL = "sales_collateral"


class PipelineStage(str, Enum):
    QUEUED = "queued"
    CREATING = "creating"
    REVIEWING = "reviewing"
    AWAITING_APPROVAL = "awaiting_approval"
    LOCALIZING = "localizing"
    DISTRIBUTING = "distributing"
    COMPLETED = "completed"
    FAILED = "failed"
    REJECTED = "rejected"


class AgentStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    AWAITING_HUMAN = "awaiting_human"


class ComplianceLevel(str, Enum):
    PASS = "pass"
    WARNING = "warning"
    FAIL = "fail"


class Channel(str, Enum):
    WEBSITE = "website"
    TWITTER = "twitter"
    LINKEDIN = "linkedin"
    EMAIL = "email"
    INTERNAL = "internal"
    INSTAGRAM = "instagram"


# ── Request Models ───────────────────────────────────────────────────────────

class ContentBrief(BaseModel):
    topic: str = Field(..., description="Main topic or subject")
    audience: str = Field(default="general", description="Target audience")
    format: ContentFormat = Field(default=ContentFormat.BLOG_POST)
    tone: str = Field(default="professional", description="Desired tone")
    key_points: list[str] = Field(default_factory=list, description="Key points to cover")
    brand_name: str = Field(default="TechCorp", description="Brand/company name")
    target_languages: list[str] = Field(default_factory=lambda: ["Hindi", "Spanish"])
    target_channels: list[Channel] = Field(
        default_factory=lambda: [Channel.WEBSITE, Channel.LINKEDIN, Channel.EMAIL]
    )
    knowledge_context: str = Field(default="", description="Internal docs / context to use")


class ApprovalAction(BaseModel):
    approved: bool
    feedback: str = ""


# ── Agent Result Models ──────────────────────────────────────────────────────

class AgentResult(BaseModel):
    agent_name: str
    status: AgentStatus = AgentStatus.COMPLETED
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_seconds: float = 0.0
    output: dict = Field(default_factory=dict)
    error: Optional[str] = None


class ComplianceFinding(BaseModel):
    category: str  # brand_tone, legal, regulatory, terminology
    severity: ComplianceLevel
    description: str
    suggestion: str = ""
    location: str = ""


class ComplianceReport(BaseModel):
    overall_status: ComplianceLevel
    score: float = 0.0  # 0-100
    findings: list[ComplianceFinding] = Field(default_factory=list)
    auto_fixes_applied: int = 0
    reviewed_content: str = ""


class LocalizedContent(BaseModel):
    language: str
    content: str
    cultural_notes: list[str] = Field(default_factory=list)


class ChannelDistribution(BaseModel):
    channel: Channel
    status: str = "published"
    formatted_content: str = ""
    metadata: dict = Field(default_factory=dict)


# ── Pipeline Model ───────────────────────────────────────────────────────────

class Pipeline(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    brief: ContentBrief
    stage: PipelineStage = PipelineStage.QUEUED
    created_at: str = Field(
        default_factory=lambda: datetime.datetime.now().isoformat()
    )
    updated_at: str = Field(
        default_factory=lambda: datetime.datetime.now().isoformat()
    )
    agent_results: dict[str, AgentResult] = Field(default_factory=dict)
    
    # Content flowing through the pipeline
    draft_content: str = ""
    compliance_report: Optional[ComplianceReport] = None
    reviewed_content: str = ""
    localized_versions: list[LocalizedContent] = Field(default_factory=list)
    distributions: list[ChannelDistribution] = Field(default_factory=list)
    
    # Metrics
    total_duration_seconds: float = 0.0
    estimated_manual_hours: float = 0.0  # What this would take manually

    def touch(self):
        self.updated_at = datetime.datetime.now().isoformat()


# ── WebSocket Event ──────────────────────────────────────────────────────────

class WSEvent(BaseModel):
    pipeline_id: str
    event_type: str  # stage_change, agent_start, agent_complete, log, error
    agent_name: Optional[str] = None
    stage: Optional[PipelineStage] = None
    message: str = ""
    data: dict = Field(default_factory=dict)
    timestamp: str = Field(
        default_factory=lambda: datetime.datetime.now().isoformat()
    )


# ── Analytics ────────────────────────────────────────────────────────────────

class AnalyticsOverview(BaseModel):
    total_pipelines: int = 0
    completed_pipelines: int = 0
    avg_cycle_time_seconds: float = 0.0
    avg_manual_equivalent_hours: float = 0.0
    time_savings_percent: float = 0.0
    compliance_pass_rate: float = 0.0
    languages_supported: int = 0
    channels_active: int = 0
    content_by_format: dict[str, int] = Field(default_factory=dict)
    recent_pipelines: list[dict] = Field(default_factory=list)
