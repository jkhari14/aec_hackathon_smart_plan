"""The brief: one JSON document per site, read by the web page, the voice agent and Rhino/Grasshopper/Revit.

The checklist rows come from the checklist engine (checklist/); statuses are closed sets, so a
row can never claim proof the public record does not hold.
"""

from typing import Literal, Optional

from pydantic import BaseModel, Field

SCHEMA_VERSION = 1

Party = Literal[
    "owner_developer",
    "design_professional",
    "excavation_support_engineer",
    "geotechnical_engineer",
    "contractor",
    "special_inspector",
    "adjoining_owner",
    "dob",
]
ProjectType = Literal["new_building", "renovation", "excavation_next_to_existing"]


class DatasetStatus(BaseModel):
    key: str
    name: str
    status: Literal["ok", "error", "skipped"] = Field(
        description="ok: queried (count 0 means none found). error: nothing is known; never show as zero."
    )
    count: Optional[int] = None
    reason: Optional[str] = None
    query_url: Optional[str] = None


class LotFacts(BaseModel):
    """From PLUTO, which can lag a demolition or a collapse."""

    address: Optional[str] = None
    year_built: Optional[int] = None
    floors: Optional[float] = None
    building_class: Optional[str] = None
    zoning_district: Optional[str] = None
    residential_units: Optional[int] = None
    lot_front_ft: Optional[float] = None
    lot_depth_ft: Optional[float] = None
    pluto_version: Optional[str] = None


class Building(BaseModel):
    """One building footprint. Heights are in feet; geometry is GeoJSON in EPSG:4326."""

    bin: Optional[str] = None
    construction_year: Optional[int] = None
    height_roof_ft: Optional[float] = None
    ground_elevation_ft: Optional[float] = None
    status: Optional[str] = None
    geometry: Optional[dict] = None


class Lot(BaseModel):
    bbl: str
    role: Literal["site", "touching"]
    facts: Optional[LotFacts] = Field(None, description="None when PLUTO has no record for the lot.")
    datasets: list[DatasetStatus]
    record_ids: list[str]
    lot_geometry: Optional[dict] = Field(None, description="Tax-lot polygon, GeoJSON in EPSG:4326.")
    buildings: list[Building] = []


class PublicRecord(BaseModel):
    id: str = Field(description='"<dataset_key>:<record_id>", unique within the brief.')
    dataset_key: str
    dataset_name: str
    record_id: str
    bbl: str
    date: Optional[str] = Field(None, description="ISO date the record was issued or filed; None if undated.")
    status_today: Optional[str] = Field(None, description="Status as published today, not as of `date`.")
    summary: str
    query_url: Optional[str] = None
    mentions_stop_work: bool = False
    stop_work_first_mentioned: Optional[str] = Field(
        None, description="ISO date the earliest stop-work mention on this record was written, which can be "
        "after `date`; None if undated. An as-of view shows the mention only from the day after.")
    resolution: Optional[str] = Field(
        None, description="DOB's resolution text (311 requests), written when DOB acted, after `date`.")
    resolution_recorded: Optional[str] = Field(
        None, description="ISO date DOB recorded `resolution`; None if undated. An as-of view shows it only "
        "from the day after.")


ApplyStatus = Literal["applies", "needs_input", "unknown", "set_by_dob", "does_not_apply"]


class Applies(BaseModel):
    """From the checklist engine: whether a duty applies, and the record, input or code text behind it."""

    status: ApplyStatus
    basis: list[dict] = Field(default_factory=list, description="Each has a kind: public_record, user_input or code_text.")
    needs: list[str] = Field(default_factory=list, description="Project inputs that would decide it.")
    notes: list[str] = Field(default_factory=list)


class Lead(BaseModel):
    """A document a public source reports and nobody here has read. Never proof."""

    reported_by: str
    document: str
    url: Optional[str] = None
    reported_on: Optional[str] = None
    document_url: Optional[str] = None
    document_date: Optional[str] = None
    checked: Optional[str] = None


class RowProof(BaseModel):
    """None of these statuses is 'verified'; a lead never closes a gap."""

    status: Literal["not_provided", "provided_unverified", "reported_not_read"]
    note: str
    leads: list[Lead] = Field(default_factory=list)
    document: Optional[str] = None
    provided_by: Optional[str] = None


class RelatedFilings(BaseModel):
    status: str
    records: list[dict] = Field(default_factory=list)


class RelatedRecords(BaseModel):
    """Records beside a row. They are not its proof."""

    filings: RelatedFilings
    citations: list[dict] = Field(default_factory=list)


class BuildingApplies(BaseModel):
    bbl: str
    address: Optional[str] = None
    building_presence: str
    applies: Applies
    open_gap: bool


class Roast(BaseModel):
    line: str
    serious: str


class ChecklistRow(BaseModel):
    """One duty, built by the checklist engine (checklist/). `roast` is filled by the roast writer."""

    id: str
    section: str
    title: str
    requirement: str = Field(description="Paraphrase of the code section; read the linked text before relying on it.")
    parties: list[Party]
    life_safety: bool = Field(description="Serious line first; the roast comes second.")
    proof_needed: str
    source_url: str
    scope: Literal["site", "each_adjacent_building"]
    applies: Applies
    proof: RowProof
    related_records: RelatedRecords
    open_gap: bool = Field(description="The duty applies and no proof was provided.")
    per_building: list[BuildingApplies] = Field(default_factory=list)
    roast: Optional[Roast] = None


class ChecklistSummary(BaseModel):
    rows: int
    applies: int
    needs_input: int
    unknown: int
    set_by_dob: int
    does_not_apply: int
    open_gaps: int
    inputs_needed: list[str]


class Precedent(BaseModel):
    id: str
    title: str
    date: str
    longitude: float
    latitude: float
    summary: str
    cause_as_publicly_reported: Optional[str] = None
    source_urls: list[str]


class Brief(BaseModel):
    schema_version: Literal[1] = SCHEMA_VERSION
    slug: str
    project_type: ProjectType
    address_input: str
    matched_label: str
    pulled_at: str
    coordinate_system: str = "EPSG:4326 (longitude, latitude); heights in feet"
    site: Lot
    touching_lots: list[Lot]
    as_of: Optional[str] = Field(None, description="Checklist built from records dated before this day; None = as pulled.")
    records: list[PublicRecord]
    checklist: list[ChecklistRow]
    checklist_summary: ChecklistSummary
    precedents: list[Precedent] = []
    caveats: list[str]


class BriefListing(BaseModel):
    slug: str
    address: str
    project_type: ProjectType
