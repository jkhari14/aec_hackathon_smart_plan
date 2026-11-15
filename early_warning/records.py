"""A site pull (data_pull.site_brief_pull) as dated events, which the sequence rules read.

One event per record, dated the way checklist.record_dates dates it, plus one event for each later
action a record carries: a complaint's disposition and a 311 resolution are written when DOB acts, so
they get their own date. HPD violations are left out on purpose: housing violations are never scored as
structural risk. A record whose date cannot be read is counted as undated and never placed in a sequence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from checklist.record_dates import DATE_FIELDS, parse_record_date
from data_pull.lot_records import DATASETS

ID_FIELDS = {
    "dob_now_filings": "job_filing_number",
    "dob_violations": "isn_dob_bis_viol",
    "ecb_violations": "ecb_violation_number",
    "dob_safety_violations": "violation_number",
    "dob_complaints": "complaint_number",
    "dob_311_requests": "unique_key",
}
TEXT_FIELDS = {
    "dob_now_filings": ("job_description",),
    "dob_violations": ("violation_type", "description", "disposition_comments"),
    "ecb_violations": ("section_law_description1", "violation_description"),
    "dob_safety_violations": ("violation_type", "violation_remarks"),
    "dob_complaints": ("complaint_category",),
    "dob_311_requests": ("descriptor", "descriptor_2"),
}
VIOLATIONS = ("dob_violations", "ecb_violations", "dob_safety_violations")
SOURCE_URLS = {key: f"https://data.cityofnewyork.us/d/{DATASETS[key][0]}" for key in ID_FIELDS}
SOURCE_NAMES = {key: DATASETS[key][1] for key in ID_FIELDS}


@dataclass(frozen=True)
class Event:
    ref: str  # "<dataset>:<record id>", the id the UI and the chat cite
    dataset: str
    kind: str  # "record", "disposition" or "resolution"
    lot_bbl: str
    lot_role: str  # "site" or "touching lot"
    when: date
    text: str  # the record's own words, upper case, whitespace collapsed
    record: dict = field(compare=False, repr=False)


@dataclass
class Lot:
    bbl: str
    role: str
    address: str | None
    year_built: int | None
    datasets: dict  # key -> the pull's {status, count, truncated, records, ...}
    events: list[Event]
    undated: int


@dataclass
class SitePull:
    bbl: str
    address: str | None
    lat: float | None
    lon: float | None
    pulled_on: date
    touching_status: str  # "ok", "error" or "skipped"
    lots: list[Lot]

    @property
    def site(self) -> Lot:
        return self.lots[0]

    @property
    def touching(self) -> list[Lot]:
        return self.lots[1:]


def _words(record: dict, fields: tuple[str, ...]) -> str:
    return " ".join(" ".join(str(record.get(f) or "").split()) for f in fields).upper()


def _float(value) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _lot_events(lot: dict, role: str) -> tuple[list[Event], int]:
    events, undated = [], 0
    for key, id_field in ID_FIELDS.items():
        result = lot["datasets"].get(key) or {}
        for record in result.get("records", []):
            ref = f"{key}:{record.get(id_field)}"
            when = parse_record_date(record.get(DATE_FIELDS[key]))
            if when is None:
                undated += 1
                continue
            events.append(Event(ref, key, "record", lot["bbl"], role, when, _words(record, TEXT_FIELDS[key]), record))
            if key == "dob_complaints" and (done := parse_record_date(record.get("disposition_date"))):
                code = str(record.get("disposition_code") or "").strip().upper()
                events.append(Event(ref, key, "disposition", lot["bbl"], role, done, code, record))
            if key == "dob_311_requests" and record.get("resolution_description"):
                if done := parse_record_date(record.get("resolution_action_updated_date")):
                    text = _words(record, ("resolution_description",))
                    events.append(Event(ref, key, "resolution", lot["bbl"], role, done, text, record))
    return sorted(events, key=lambda e: (e.when, e.ref)), undated


def _pluto(lot: dict) -> dict:
    result = lot["datasets"].get("pluto") or {}
    return (result.get("records") or [{}])[0] if result.get("status") == "ok" else {}


def from_pull(pull: dict) -> SitePull:
    lots = []
    for raw in [pull["site"], *pull.get("touching_lots", [])]:
        role = "site" if raw is pull["site"] else "touching lot"
        events, undated = _lot_events(raw, role)
        pluto = _pluto(raw)
        year = _float(pluto.get("yearbuilt"))
        lots.append(Lot(raw["bbl"], role, pluto.get("address"), int(year) if year else None,
                        raw["datasets"], events, undated))
    site_pluto, lookup = _pluto(pull["site"]), pull.get("address_lookup") or {}
    return SitePull(
        bbl=pull["site_bbl"],
        address=lookup.get("matched_label") or site_pluto.get("address"),
        lat=_float(site_pluto.get("latitude")) or _float(lookup.get("lat")),
        lon=_float(site_pluto.get("longitude")) or _float(lookup.get("lon")),
        pulled_on=date.fromisoformat(pull["pulled_at"][:10]),
        touching_status=(pull.get("touching_lots_lookup") or {}).get("status", "error"),
        lots=lots,
    )


def dataset_problems(lots: list[Lot], keys: tuple[str, ...]) -> list[str]:
    """Plain words for each dataset that did not load on these lots, so a rule reports it."""
    problems = []
    for lot in lots:
        for key in keys:
            result = lot.datasets.get(key) or {}
            if result.get("status") != "ok":
                why = result.get("reason") or result.get("error") or "not pulled"
                problems.append(f"{SOURCE_NAMES[key]} for lot {lot.bbl} couldn't load ({why})")
            elif result.get("truncated"):
                problems.append(f"{SOURCE_NAMES[key]} for lot {lot.bbl} hit the row cap, so at least this many")
    return problems
