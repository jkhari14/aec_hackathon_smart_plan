"""The shared contracts every ForeSite module and screen builds against.

These models are the source of truth. `python -m contracts.generate` writes them out as JSON Schemas in
`contracts/schemas/` and as `api/openapi.json`, which the web app turns into TypeScript types
(`npm run contracts` in `web/`). Change a contract in its own small PR, before the PR that needs it.
"""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

Hazard = Literal[
    "structural",
    "geotech",
    "fire",
    "flood",
    "contamination",
    "facade",
    "weather",
    "construction_safety",
]

# 0 signal (a complaint), 1 enforcement (violation, stop-work, vacate),
# 2 incident (injury, partial collapse), 3 catastrophic (fatality, full collapse).
Severity = Literal[0, 1, 2, 3]

Stage = Literal["pre_acquisition", "design", "pre_filing", "construction"]

JobType = Literal["new_building", "alteration", "demolition"]

WorkType = Literal[
    "earth_work",
    "excavation",
    "foundation",
    "support_of_excavation",
    "underpinning",
    "structural",
    "facade",
    "demolition",
    "sprinkler",
    "standpipe",
    "plumbing",
    "mechanical",
    "sidewalk_shed",
    "scaffold",
    "construction_fence",
]

Discipline = Literal["architect", "structural", "geotech", "contractor"]

Role = Literal["architect", "structural_engineer"]

QueryStatus = Literal["ok", "error", "capped"]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Source(Contract):
    name: str
    url: Optional[str] = None
    date: Optional[str] = None


class DatasetStatus(Contract):
    """How one source answered for one site. An error is never shown as zero; capped is "at least"."""

    key: str
    name: str
    status: QueryStatus
    count: Optional[int] = None
    source_url: Optional[str] = None


# Layers


class LayerCatalogEntry(Contract):
    layer_id: str
    name: str
    description: str
    hazard: Hazard
    source_name: str
    source_url: str
    updated_at: Optional[str] = None
    feature_count: Optional[int] = None
    status: QueryStatus
    default_on: bool


class Geometry(Contract):
    type: Literal["Point", "LineString", "Polygon", "MultiPolygon"]
    coordinates: Any


class LayerFeatureProperties(Contract):
    id: str
    layer_id: str
    hazard: Hazard
    severity: Severity
    date: Optional[str] = None
    title: str
    summary: str
    source_name: str
    source_url: str
    bbl: Optional[str] = None
    record_id: Optional[str] = None


class LayerFeature(Contract):
    type: Literal["Feature"]
    geometry: Geometry
    properties: LayerFeatureProperties


class LayerFeatureCollection(Contract):
    type: Literal["FeatureCollection"]
    layer: LayerCatalogEntry
    features: list[LayerFeature]


# Search


class SearchResult(Contract):
    label: str
    bbl: str
    bin: Optional[str] = None
    lat: float
    lon: float


# Cases


class CaseConditions(BaseModel):
    """Open on purpose: a case records whatever conditions were publicly reported."""

    model_config = ConfigDict(extra="allow")

    neighbor_year_built: Optional[int] = None
    attached: Optional[bool] = None
    construction: Optional[str] = None
    soil: Optional[str] = None
    flood_zone: Optional[str] = None
    excavation_depth_ft: Optional[float] = None


class Case(Contract):
    id: str
    title: str
    address: str
    bbl: Optional[str] = None
    lat: float
    lon: float
    date: str
    hazards: list[Hazard] = Field(min_length=1)
    severity: Severity
    job_type: Optional[JobType] = None
    work_types: list[WorkType]
    conditions: CaseConditions
    summary: str
    cause_as_reported: Optional[str] = None
    cause_status: Literal["reported", "under_investigation", "unknown"]
    sources: list[Source] = Field(min_length=1)


# Structural model (from the Revit reader or a drawing)


class BearingWall(Contract):
    id: str
    side: Literal["north", "south", "east", "west", "unknown"]
    material: Optional[str] = None
    length_ft: Optional[float] = None


class StructuralModel(Contract):
    source: Literal["revit", "drawing"]
    material: Optional[str] = None
    gravity_system: Optional[str] = None
    lateral_system: Optional[str] = None
    foundation_type: Optional[str] = None
    bearing_walls_on_lot_line: list[BearingWall]
    levels: Optional[int] = None
    confidence: float = Field(ge=0, le=1)


# Site profile


class LotFacts(Contract):
    address: Optional[str] = None
    zoning: Optional[str] = None
    built_far: Optional[float] = None
    max_far: Optional[float] = None
    lot_area_sqft: Optional[int] = None
    year_built: Optional[int] = None
    floors: Optional[float] = None
    building_class: Optional[str] = None
    landmark: Optional[str] = None
    historic_district: Optional[str] = None


class Neighbor(Contract):
    bbl: str
    bins: list[str]
    address: Optional[str] = None
    attached: bool
    year_built: Optional[int] = None
    floors: Optional[float] = None
    building_class: Optional[str] = None
    height_ft: Optional[float] = None
    shared_wall_ft: Optional[float] = None


class FloodContext(Contract):
    fema_zone: Optional[str] = None
    stormwater: Optional[str] = None
    sandy_inundation: Optional[bool] = None


class Signal(Contract):
    id: str
    hazard: Hazard
    severity: Severity
    title: str
    explanation: str
    record_ids: list[str]
    source_name: str
    date: Optional[str] = None


class SiteProfile(Contract):
    bbl: str
    bins: list[str]
    address_matched: str
    lat: float
    lon: float
    lot: LotFacts
    neighbors: list[Neighbor]
    job_type: Optional[JobType] = None
    work_types: list[WorkType]
    work_types_inferred: bool
    stage: Optional[Stage] = None
    soil: Optional[str] = None
    bedrock_depth_ft: Optional[float] = None
    flood: FloodContext
    e_designation: Optional[str] = None
    signals: list[Signal]
    structural_model: Optional[StructuralModel] = None
    datasets: list[DatasetStatus]
    as_of: Optional[str] = None


# Foresight results


class SimilarCase(Contract):
    case_id: str
    case: Case
    score: float = Field(ge=0, le=1)
    matched_on: list[str]
    differs_on: list[str]


class SimilarCases(Contract):
    bbl: str
    results: list[SimilarCase]


class EarlyWarning(Contract):
    id: str
    rule_id: str
    hazard: Hazard
    severity: Severity
    title: str
    explanation: str
    evidence_record_ids: list[str]
    first_seen: str
    as_of: Optional[str] = None


class WarningRuleCheck(Contract):
    """Whether one early-warning rule could be checked for a site. A rule that could not run is an
    error, never "no warning"; not_applicable says why the rule does not apply to this site."""

    rule_id: str
    title: str
    status: Literal["ok", "error", "not_applicable"]
    detail: str
    warnings: int = Field(ge=0)
    sources: list[Source]
    as_of: Optional[str] = None


class PatternFactor(Contract):
    feature: str
    value: Optional[str] = None
    contribution: float


class PatternScore(Contract):
    """Relative to similar sites, never a prediction that a building will fail."""

    bbl: str
    score: float = Field(ge=0, le=1)
    percentile_vs_similar: float = Field(ge=0, le=100)
    compared_with: str
    top_factors: list[PatternFactor]
    model_version: str
    calibration_note: str


class ActionItem(Contract):
    id: str
    discipline: Discipline
    hazard: Hazard
    title: str
    why: str
    code_ref: Optional[str] = None
    proof_needed: Optional[str] = None
    status: Literal["open", "in_progress", "done", "not_applicable"]
    owner_role: Optional[Role] = None
    source_rule: str
    life_safety: bool


# Projects


class ProjectMember(Contract):
    name: str
    role: Role


class ProjectNote(Contract):
    id: str
    author_role: Role
    text: str
    created_at: str


class ProjectPin(Contract):
    id: str
    kind: Literal["record", "case", "warning", "action", "chat_answer"]
    ref_id: str
    title: str
    by_role: Role
    created_at: str
    # The pinned text as the reader saw it (a chat answer, each part led by its source label). Kept as sent.
    body: Optional[str] = None


class Project(Contract):
    id: str
    name: str
    site_bbl: str
    stage: Stage
    members: list[ProjectMember]
    items: list[ActionItem]
    notes: list[ProjectNote]
    pins: list[ProjectPin]
    structural_model: Optional[StructuralModel] = None
    created_at: str


class ProjectCreate(Contract):
    name: str
    site_bbl: str
    stage: Stage
    members: list[ProjectMember]


class ActionItemUpdate(Contract):
    id: str
    status: Optional[Literal["open", "in_progress", "done", "not_applicable"]] = None
    owner_role: Optional[Role] = None


class NoteCreate(Contract):
    author_role: Role
    text: str


class PinCreate(Contract):
    kind: Literal["record", "case", "warning", "action", "chat_answer"]
    ref_id: str
    title: str
    by_role: Role
    body: Optional[str] = None


# Chat


class ChatExchange(Contract):
    """One earlier question and the answer text the reader saw, so a follow-up question has its context."""

    question: str
    answer: str


class ChatRequest(Contract):
    question: str
    bbl: Optional[str] = None
    project_id: Optional[str] = None
    as_of: Optional[str] = None
    job_type: Optional[JobType] = None
    stage: Optional[Stage] = None
    history: list[ChatExchange] = Field(default_factory=list)


class ChatAnswerPart(Contract):
    """One part of an answer, labeled by where it came from.

    `warning` and `action` are results of the early-warning and action rules, not records. `not_found`
    means it was looked for and nothing was found; `unknown` means a query or a load failed, which is
    never shown as zero or none. `notice` is a fixed line from the server (limitations, what was held back).
    """

    kind: Literal["public_record", "case", "warning", "action", "ai_suggestion", "web", "user_input",
                  "not_found", "unknown", "notice"]
    text: str
    source_name: Optional[str] = None
    source_url: Optional[str] = None
    record_id: Optional[str] = None


class ChatAction(Contract):
    type: Literal["fly_to", "toggle_layer", "pin"]
    payload: dict[str, Any]


class ChatResponse(Contract):
    answer_parts: list[ChatAnswerPart]
    actions: list[ChatAction]
    offline: bool


# Every contract with its fixture file in contracts/fixtures/. A list type means the fixture is a list.
FIXTURES: dict[str, tuple[type[BaseModel], bool]] = {
    "layer_catalog": (LayerCatalogEntry, True),
    "layer_features": (LayerFeatureCollection, False),
    "search_results": (SearchResult, True),
    "cases": (Case, True),
    "structural_model": (StructuralModel, False),
    "site_profile": (SiteProfile, False),
    "similar_cases": (SimilarCases, False),
    "warnings": (EarlyWarning, True),
    "warning_checks": (WarningRuleCheck, True),
    "pattern_score": (PatternScore, False),
    "actions": (ActionItem, True),
    "project": (Project, False),
    "chat_response": (ChatResponse, False),
}
