"""The brief as the chat may use it on the page's as-of day.

One place decides what is visible, so the model's reading text, the items a statement may cite and
the server-written counts cannot disagree. In an as-of view a record dated on or after the day does
not exist here, text written later is left out, and today's statuses are dropped (the datasets keep
only the current status, so it says nothing about the earlier day).
"""

import json
import re
from dataclasses import dataclass
from typing import Optional, Union

from jahleel.api.brief.brief_models import Brief, ChecklistRow, Lot, PublicRecord
from jahleel.api.chat.chat_models import BriefSource, QueriedDataset, ReportedSource

LATER = "[dated on or after the as-of day]"
RECORDS_SHOWN_PER_DATASET = 25
# Housing violations run to hundreds per lot and are rarely about construction: the model reads fewer.
_SHOWN = {"hpd_violations": 5}
_ISO_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
_STATUS_KEYS = ("filing_status", "current_status_date")
# Datasets whose records carry an approval date (PublicRecord.approved_on).
_HAS_APPROVAL = {"dob_now_filings"}


@dataclass(frozen=True)
class Item:
    """One thing a statement may cite. `evidence` is the text its numbers are checked against."""

    ref: str
    trust: str  # "brief" (a city dataset or the checklist) or "lead" (reported, not read)
    source: Union[BriefSource, ReportedSource]
    evidence: str


@dataclass(frozen=True)
class DatasetView:
    bbl: str
    key: str
    name: str
    status: str
    count: Optional[int]  # None unless status is ok
    capped: bool  # the pull hit its row cap: count is a floor and the oldest records are missing
    reason: Optional[str]
    url: Optional[str]
    lot_label: str

    def queried(self) -> QueriedDataset:
        return QueriedDataset(key=self.key, name=self.name, bbl=self.bbl, url=self.url)


def _scrub(value, as_of: Optional[str]):
    """Checklist data for an as-of view: later dates masked, a status dated after the cutoff removed."""
    if as_of is None:
        return value
    if isinstance(value, str):
        return _ISO_DATE.sub(lambda m: m.group() if m.group() < as_of else LATER, value)
    if isinstance(value, list):
        return [_scrub(v, as_of) for v in value]
    if isinstance(value, dict):
        late = value.get("status_is_after_cutoff") is True
        return {k: _scrub(v, as_of) for k, v in value.items() if not (late and k in _STATUS_KEYS)}
    return value


class BriefView:
    def __init__(self, brief: Brief):
        self.brief = brief
        self.as_of: Optional[str] = brief.as_of
        self.lots: list[Lot] = [brief.site] + list(brief.touching_lots)
        self.lot_labels = {lot.bbl: self._lot_label(lot) for lot in self.lots}
        self.records = [r for r in brief.records if self._dated_before(r.date)]
        self.after_as_of = {r.id for r in brief.records} - {r.id for r in self.records}
        self.items: dict[str, Item] = {}
        self.datasets: dict[tuple[str, str], DatasetView] = {}
        # Numbers a statement may always use: the view's own dates and the site's label.
        self.shared_evidence = " ".join(filter(None, [self.as_of, brief.pulled_at[:10], brief.matched_label, brief.site.bbl]))
        for lot in self.lots:
            self._add_lot(lot)
        for record in self.records:
            self._add_record(record)
        self._row_text: dict[str, str] = {}
        for row in brief.checklist:
            self._add_row(row)

    # ---- visibility ----

    def _dated_before(self, when: Optional[str]) -> bool:
        """The checklist engine's rule: dated before the day. Undated text cannot be placed, so it is left out."""
        return self.as_of is None or (when is not None and when < self.as_of)

    def _mentions_stop_work(self, record: PublicRecord) -> bool:
        return record.mentions_stop_work and self._dated_before(record.stop_work_first_mentioned)

    def _resolution(self, record: PublicRecord) -> Optional[str]:
        return record.resolution if record.resolution and self._dated_before(record.resolution_recorded) else None

    def _approval(self, record: PublicRecord) -> str:
        if record.approved_on and self._dated_before(record.approved_on):
            return f"Approved {record.approved_on}."
        return f"No approval dated before {self.as_of}." if self.as_of else "No approval date in the dataset."

    # ---- items ----

    def _lot_label(self, lot: Lot) -> str:
        where = "the site" if lot.role == "site" else "touching the site"
        if lot.facts and lot.facts.address:
            return f"{lot.facts.address} (lot {lot.bbl}, {where})"
        return f"lot {lot.bbl} ({where}, no PLUTO address)"

    def _add_lot(self, lot: Lot) -> None:
        visible = [r for r in self.brief.records if r.bbl == lot.bbl and self._dated_before(r.date)]
        pluto_url = None
        for dataset in lot.datasets:
            count = dataset.count if dataset.status == "ok" else None
            if count is not None and self.as_of and dataset.key != "pluto":
                count = sum(1 for r in visible if r.dataset_key == dataset.key)
            self.datasets[(lot.bbl, dataset.key)] = DatasetView(
                bbl=lot.bbl, key=dataset.key, name=dataset.name, status=dataset.status, count=count,
                capped=dataset.status == "ok" and dataset.truncated,
                reason=dataset.reason, url=dataset.query_url, lot_label=self.lot_labels[lot.bbl])
            if dataset.key == "pluto":
                pluto_url = dataset.query_url
        if lot.facts:
            facts = lot.facts.model_dump(exclude_none=True)
            detail = ", ".join(f"{k.replace('_', ' ')}: {v}" for k, v in facts.items())
            self.items[f"lot:{lot.bbl}"] = Item(
                ref=f"lot:{lot.bbl}", trust="brief", evidence=f"{lot.bbl} {detail}",
                source=BriefSource(type="lot_facts", ref=f"lot:{lot.bbl}", label=f"PLUTO lot facts, {self.lot_labels[lot.bbl]}",
                                   detail=detail, bbl=lot.bbl, url=pluto_url))

    def _add_record(self, record: PublicRecord) -> None:
        detail = [_scrub(record.summary, self.as_of)]
        if record.dataset_key in _HAS_APPROVAL:
            detail.append(self._approval(record))
        if self.as_of is None and record.status_today:
            detail.append(f"Status today: {record.status_today}.")
        if self._mentions_stop_work(record):
            detail.append("Its text mentions a stop-work order.")
        resolution = self._resolution(record)
        if resolution:
            detail.append(f"DOB's resolution, recorded {record.resolution_recorded or 'on an unstated date'}: {resolution}")
        text = " ".join(detail)
        self.items[record.id] = Item(
            ref=record.id, trust="brief",
            evidence=f"{record.id} {record.date or ''} {self.lot_labels.get(record.bbl, record.bbl)} {text}",
            source=BriefSource(type="public_record", ref=record.id, label=f"{record.dataset_name} {record.record_id}",
                               detail=text, date=record.date, bbl=record.bbl, url=record.query_url))

    def _lead_is_shown(self, reported_on: Optional[str]) -> bool:
        return self._dated_before(reported_on)

    def _add_row(self, row: ChecklistRow) -> None:
        data = _scrub(row.model_dump(), self.as_of)
        leads = data["proof"].pop("leads")
        ref = f"row:{row.id}"
        self.items[ref] = Item(
            ref=ref, trust="brief", evidence=json.dumps(data),
            source=BriefSource(type="requirement", ref=ref, label=f"BC §{row.section} {row.title}",
                               detail=f"{row.requirement} (A paraphrase: read the linked code text.)", url=row.source_url))
        lines = [
            f"[{ref}] BC {row.section} \"{row.title}\" | scope: {row.scope} | life safety: {'yes' if row.life_safety else 'no'}"
            f" | parties: {', '.join(row.parties)}",
            f"  requirement (a paraphrase; the linked code text governs): {row.requirement}",
            f"  proof needed: {row.proof_needed} | proof status: {row.proof.status} ({row.proof.note})"
            f" | open gap: {'yes' if row.open_gap else 'no'}",
            f"  applies: {json.dumps(data['applies'])}",
        ]
        if data["per_building"]:
            lines.append("  per adjacent building: " + "; ".join(
                f"lot {b['bbl']} ({b['address'] or 'no PLUTO address'}): {b['applies']['status']}"
                f"{', open gap' if b['open_gap'] else ''}" for b in data["per_building"]))
        lines.append(f"  records beside the row (not its proof): {json.dumps(data['related_records'])}")
        for number, lead in enumerate(leads, start=1):
            if not self._lead_is_shown(lead.get("reported_on")):
                lines.append("  a lead exists, but its report is dated on or after the as-of day: not shown in this view")
                continue
            lead = _scrub(lead, self.as_of)
            lead_ref = f"lead:{row.id}:{number}"
            self.items[lead_ref] = Item(
                ref=lead_ref, trust="lead", evidence=json.dumps(lead),
                source=ReportedSource(ref=lead_ref, reported_by=lead["reported_by"], document=lead["document"],
                                      url=lead.get("url"), reported_on=lead.get("reported_on"),
                                      document_date=lead.get("document_date")))
            lines.append(f"  [{lead_ref}] a lead (reported, not read; never proof): {json.dumps(lead)}")
        self._row_text[row.id] = "\n".join(lines)

    # ---- what the model reads ----

    def _shown_records(self) -> list[PublicRecord]:
        cited = set(re.findall(r'"ref": "([^"]+)"', " ".join(i.evidence for i in self.items.values() if i.ref.startswith("row:"))))
        taken: dict[tuple[str, str], int] = {}
        shown = []
        for record in self.records:  # newest first, as the brief sorts them
            group = (record.bbl, record.dataset_key)
            limit = _SHOWN.get(record.dataset_key, RECORDS_SHOWN_PER_DATASET)
            if taken.get(group, 0) < limit or record.id in cited or self._mentions_stop_work(record):
                taken[group] = taken.get(group, 0) + 1
                shown.append(record)
        return shown

    def digest(self) -> str:
        brief = self.brief
        out = [
            f"SITE: {brief.matched_label} | lot (BBL) {brief.site.bbl} | project type: {brief.project_type}"
            f" | records pulled {brief.pulled_at[:10]}",
            f"AS-OF VIEW: only records dated before {self.as_of}. Later records, later-written text and today's "
            "statuses are not in this brief, and you have no web search in this view. Answer as a reader of the record "
            "on that day: say nothing about anything on or after it, whatever you may know." if self.as_of else
            "VIEW: as pulled. Every status is today's, not the status on the record's date.",
            "", "LOTS (PLUTO can lag what is on the ground; landmark and historic district are hints, and "
            "'none listed' never means 'no')",
        ]
        shown = self._shown_records()
        for lot in self.lots:
            item = self.items.get(f"lot:{lot.bbl}")
            out.append(f"[lot:{lot.bbl}] {self.lot_labels[lot.bbl]}: {item.source.detail}" if item else
                       f"{self.lot_labels[lot.bbl]}: PLUTO holds no record for it, so there are no lot facts to cite")
            checks = []
            for (bbl, key), dataset in self.datasets.items():
                if bbl != lot.bbl:
                    continue
                if dataset.status != "ok":
                    checks.append(f"{key}: {dataset.status} (nothing is known; not zero)")
                else:
                    listed = sum(1 for r in shown if r.bbl == bbl and r.dataset_key == key)
                    partly = key != "pluto" and listed < (dataset.count or 0)
                    floor = "at least " if dataset.capped else ""
                    checks.append(f"{key}: {floor}{dataset.count}" + (f" ({listed} listed below)" if partly else "")
                                  + (" (the pull hit its row cap: the oldest records are missing)" if dataset.capped else ""))
            out.append("  datasets: " + "; ".join(checks))
        out += ["", "RECORDS, newest first (id | lot | date | text). Records not listed can still be counted with a dataset_check."]
        out += [f"[{r.id}] lot {r.bbl} | {r.date or 'undated'} | {self.items[r.id].source.detail}" for r in shown]
        out += ["", "CHECKLIST ROWS (Building Code duties toward adjoining property; a row is never marked done from public data)"]
        out += [self._row_text[row.id] for row in brief.checklist]
        precedents = [p for p in brief.precedents if self._dated_before(p.date)]
        if precedents:
            out += ["", "PAST INCIDENTS NEARBY (causes only as publicly reported)"]
            out += [f"{p.date} {p.title}: {p.summary} Cause: {p.cause_as_publicly_reported or 'no cause publicly reported'}"
                    for p in precedents]
        out += ["", "CAVEATS"] + [f"- {c}" for c in brief.caveats]
        return "\n".join(out)
