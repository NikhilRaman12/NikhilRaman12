from enum import StrEnum
from pydantic import BaseModel, Field, model_validator

class PregnancyStatus(StrEnum):
    NOT_PREGNANT = "not_pregnant"
    PREGNANT = "pregnant"
    UNKNOWN = "unknown"
class SafetyStatus(StrEnum):
    SUPPORTED = "supported"
    ESCALATE = "escalate"
    OUT_OF_SCOPE = "out_of_scope"
    GENERATION_ERROR = "generation_error"
class UserContext(BaseModel):
    age: int | None = Field(None, ge=0, le=120)
    pregnancy: PregnancyStatus = PregnancyStatus.UNKNOWN
    immunocompromised: bool = False
    severity: str | None = None
    duration_days: int | None = Field(None, ge=0)
class ChatRequest(BaseModel):
    message: str = Field(min_length=2, max_length=4000)
    thread_id: str = Field(min_length=8, max_length=128)
    parent_request_id: str | None = None
    language: str = "auto"
    context: UserContext = Field(default_factory=UserContext)
class Citation(BaseModel):
    citation_id: str
    source_title: str
    organization_or_authors: str | None = None
    publication_year: int | None = None
    filename_or_url: str
    page: int = Field(ge=1)
    chunk_id: str
    supporting_excerpt: str
    retrieval_score: float
class ActionRow(BaseModel):
    guidance_lens: str
    what_may_help: str
    how_to_follow: str
    frequency_or_duration: str
    evidence_strength: str
    cautions: str
    stop_and_seek_care_if: str
    supporting_citation_ids: list[str] = Field(min_length=1)
class ImplementationPlan(BaseModel):
    now: list[str]
    next_6_12_hours: list[str]
    next_24_48_hours: list[str]
class QuickAction(BaseModel):
    label: str
    standalone_query: str
    parent_topic: str
class Metrics(BaseModel):
    vector_backend: str
    vector_hit_count: int = 0
    similarity_scores: list[float] = Field(default_factory=list)
    graph_backend: str
    matched_entities: int = 0
    graph_path_count: int = 0
    groq_configured: bool
    groq_invoked: bool = False
    context_token_count: int = 0
    citations_valid: bool = False
    latency_ms: float = 0
    deployment_profile: str
class ChatResponse(BaseModel):
    request_id: str
    detected_language: str
    safety_status: SafetyStatus
    applies_to: str
    plain_language_summary: str
    action_table: list[ActionRow]
    implementation_plan: ImplementationPlan
    things_to_avoid: list[str]
    warning_signs: list[str]
    follow_up_question: str
    quick_actions: list[QuickAction]
    citations: list[Citation]
    graph_paths: list[list[str]]
    evidence_strength: str
    error: str | None = None
    metrics: Metrics

    @model_validator(mode="after")
    def citations_resolve(self):
        ids = {c.citation_id for c in self.citations}
        if any(not set(a.supporting_citation_ids) <= ids for a in self.action_table):
            raise ValueError("action citations must resolve to returned evidence")
        return self
