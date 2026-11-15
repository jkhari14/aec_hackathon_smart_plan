"""The early-warning sequence rules, each a small function over a site's dated records with an as-of date.

As-of means "dated before that day": a record dated on or after it was not knowable yet, and neither is
anything after the pull. Every rule also reports a check (ok, error or not_applicable), so a rule that
could not run is never shown as "no warning". A warning is a prompt to look, never a finding.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Callable

from api.contracts import EarlyWarning, Source, WarningRuleCheck
from checklist.checklist_rules import EXCAVATION_FLAGS
from checklist.record_dates import parse_record_date
from early_warning import weather as weather_source
from early_warning.records import SOURCE_NAMES, SOURCE_URLS, VIOLATIONS, Event, Lot, SitePull, dataset_problems

LOOKBACK = timedelta(days=365)
FOLLOW_UP_WINDOW = timedelta(days=21)
EARTH_WORK_WINDOW = timedelta(days=90)
HEAVY_RAIN_MM = 25.0

# Violation text about protecting the property next door: "ADJACENT PROPERTIES", "ADJ PROPTERY",
# a BC 3309 citation (protection of adjoining property) or its 1968-code twin 27-1031.
ADJACENT_PROTECTION = re.compile(
    r"\bADJ(?:ACENT|OINING|\.)?\s+(?:PROP|BUILDING|BLDG|STRUCTURE|PREMISES|LOT|WALL)"
    r"|\bBC\s*3309|(?<![\d.])3309\.\d|\b27-1031\b|\bNOT PROTECTED\b"
)
STOP_WORK = re.compile(r"STOP\s*-?\s*(?:ALL\s+)?WORK|28-207\.2")
# 28-207.2.2 is the Administrative Code's "unlawful continuance" after a stop-work order.
WORK_CONTINUED = re.compile(
    r"28-207\.2\.2"
    r"|(?:CONTRARY TO|FAIL\w* TO (?:OBEY|COMPLY WITH|HONOR)|IN VIOLATION OF|DESPITE|VIOLATING)"
    r"\s+(?:THE |A |AN )?(?:\w+\s+)?STOP\s*-?\s*WORK"
    r"|WORK\s+CONTINU"
)
SOE_DESCRIPTION = re.compile(r"\bSOE\b|SUPPORT OF EXCAVATION|EXCAVAT|UNDERPINN")
SIGNED_OFF = re.compile(r"SIGNED[- ]?OFF|COMPLETED|WITHDRAWN", re.IGNORECASE)

ADJACENT_COMPLAINT = "03"
STRUCTURAL_COMPLAINTS = {
    "30": "building shaking, vibrating or structural stability affected",
    "14": "excavation undermining an adjacent building",
    "16": "inadequate support or shoring",
    "5C": "structural stability impacted, new building under construction",
}
# Complaint dispositions, as DOB's table (6v9u-ndjg) prints them.
STOP_WORK_DISPOSITIONS = {"A3": "full stop-work order served", "L1": "partial stop-work order",
                          "H5": "stop all work", "V3": "stop-work order violation served"}
WORK_CONTINUED_DISPOSITIONS = {"H3": "violation issued for failure to obey a stop-work order"}
VACATE_DISPOSITIONS = {"Y1": "full vacate order", "Y3": "partial vacate order"}

LABELS = {
    "dob_now_filings": "DOB NOW filing",
    "dob_violations": "DOB violation",
    "ecb_violations": "ECB violation",
    "dob_safety_violations": "DOB safety violation",
    "dob_complaints": "DOB complaint",
    "dob_311_requests": "311 request",
}


@dataclass
class Context:
    pull: SitePull
    as_of: date | None
    weather: Callable[..., weather_source.Weather] = weather_source.daily_weather

    @property
    def until(self) -> date:
        """Records dated before this day are known: the as-of day, or the day after the pull."""
        after_pull = self.pull.pulled_on + timedelta(days=1)
        return min(self.as_of, after_pull) if self.as_of else after_pull

    @property
    def since(self) -> date:
        return self.until - LOOKBACK

    def known(self, event: Event) -> bool:
        return event.when < self.until

    def period(self) -> str:
        if self.as_of:
            return f"before {self.as_of}"
        return f"up to the pull on {self.pull.pulled_on}"

    def lots_phrase(self) -> str:
        n = len(self.pull.touching)
        return f"the site and its {n} touching lot{'s' if n != 1 else ''}"


@dataclass
class Outcome:
    status: str
    detail: str
    warnings: list[dict] = field(default_factory=list)
    sources: list[Source] = field(default_factory=list)


@dataclass(frozen=True)
class Rule:
    id: str
    title: str
    hazard: str
    severity: int
    check: Callable[[Context], Outcome]


def _where(lot: Lot) -> str:
    if lot.role == "site":
        return "on the site"
    return f"on touching lot {lot.bbl}" + (f" ({lot.address.title()})" if lot.address else "")


def _record_id(event: Event) -> str:
    return event.ref.split(":", 1)[1]


def _named(events: list[Event]) -> str:
    """'ECB violation 39552071X' or 'ECB violations 35544269X and 35544267M'."""
    ids = [_record_id(e) for e in events]
    label = LABELS[events[0].dataset] + ("s" if len(ids) > 1 else "")
    return f"{label} {' and '.join([', '.join(ids[:-1]), ids[-1]] if len(ids) > 1 else ids)}"


def _sources(ctx: Context, keys: tuple[str, ...]) -> list[Source]:
    pulled = ctx.pull.pulled_on.isoformat()
    return [Source(name=SOURCE_NAMES[k], url=SOURCE_URLS[k], date=pulled) for k in keys]


def _with_problems(detail: str, problems: list[str]) -> tuple[str, str]:
    if not problems:
        return "ok", detail
    return "error", f"{detail} Not fully checked: {'; '.join(problems)}."


def _touching_problem(ctx: Context) -> list[str]:
    if ctx.pull.touching_status == "ok":
        return []
    return ["the touching lots couldn't be looked up, so only the site was checked"]


def _warning(ctx: Context, rule_id: str, key: str, hazard: str, severity: int, title: str, explanation: str,
             evidence: list[str], first_seen: date) -> dict:
    return EarlyWarning(
        id=f"{rule_id}:{key}", rule_id=rule_id, hazard=hazard, severity=severity, title=title,
        explanation=explanation, evidence_record_ids=list(dict.fromkeys(evidence)),
        first_seen=first_seen.isoformat(), as_of=ctx.as_of.isoformat() if ctx.as_of else None,
    ).model_dump()


# Rule 1: an adjacent-protection violation (or complaint 03), then no DOB action on that lot for 21 days.

def _is_adjacent_trigger(event: Event) -> bool:
    if event.kind != "record":
        return False
    if event.dataset in VIOLATIONS:
        return bool(ADJACENT_PROTECTION.search(event.text))
    return event.dataset == "dob_complaints" and event.text.strip() == ADJACENT_COMPLAINT


def _is_follow_up(event: Event) -> bool:
    """A DOB action: a violation, a complaint's disposition, or a 311 resolution. Not a new complaint."""
    return (event.dataset in VIOLATIONS and event.kind == "record") or event.kind in ("disposition", "resolution")


def adjacent_protection_no_follow_up(ctx: Context) -> Outcome:
    rule = RULES_BY_ID["adjacent_protection_no_follow_up"]
    warnings = []
    for lot in ctx.pull.lots:
        triggers: dict[date, list[Event]] = {}
        for event in lot.events:
            if _is_adjacent_trigger(event) and ctx.since <= event.when and ctx.known(event):
                triggers.setdefault(event.when, []).append(event)
        for day, found in sorted(triggers.items()):
            deadline = day + FOLLOW_UP_WINDOW
            if deadline >= ctx.until or deadline > ctx.pull.pulled_on:
                continue  # the 21 days have not passed yet, or the records stop before they end
            refs = {e.ref for e in found}
            later = [e for e in lot.events if _is_follow_up(e) and ctx.known(e) and e.when > day
                     and not (e.ref in refs and e.kind == "record")]
            # A complaint's own disposition on its first day is a follow-up: someone inspected.
            later += [e for e in lot.events if e.ref in refs and e.kind == "disposition" and e.when == day]
            if any(e.when <= deadline for e in later):
                continue
            nxt = min((e.when for e in later), default=None)
            then = f"the next is dated {nxt}" if nxt else f"none is dated since, through {ctx.until - timedelta(days=1)}"
            what = ("concerns protection of adjacent property" if found[0].dataset in VIOLATIONS
                    else "reports adjacent buildings not protected (code 03)")
            if len(found) > 1:
                what = what.replace("concerns", "concern").replace("reports", "report")
            warnings.append(_warning(
                ctx, rule.id, found[0].ref, rule.hazard, rule.severity,
                "Nothing recorded for 21 days after an adjacent-protection violation",
                f"{_named(found)} ({day}, {_where(lot)}) {what}. No DOB record on that lot is dated in the 21 "
                f"days after it; {then}. The gap is a prompt to confirm the protection was put in place, not a "
                f"finding that it was not.",
                [e.ref for e in found], deadline,
            ))
    keys = (*VIOLATIONS, "dob_complaints", "dob_311_requests")
    status, detail = _with_problems(
        f"Checked DOB, ECB and safety violations and DOB complaints (code 03) on {ctx.lots_phrase()}, "
        f"dated in the year {ctx.period()}.",
        _touching_problem(ctx) + dataset_problems(ctx.pull.lots, keys),
    )
    return Outcome(status, detail, warnings, _sources(ctx, ("ecb_violations", "dob_violations", "dob_complaints")))


# Rule 2: a stop-work order, then a violation for continuing work.

def _is_stop_work(event: Event) -> bool:
    if event.kind == "disposition":
        return event.text in STOP_WORK_DISPOSITIONS
    return bool(STOP_WORK.search(event.text)) and event.dataset != "dob_complaints"


def _is_work_continued(event: Event) -> bool:
    if event.kind == "disposition":
        return event.text in WORK_CONTINUED_DISPOSITIONS
    return event.kind == "record" and event.dataset in VIOLATIONS and bool(WORK_CONTINUED.search(event.text))


def _mention(event: Event) -> str:
    if event.kind == "disposition":
        return f"the disposition of DOB complaint {_record_id(event)} ({STOP_WORK_DISPOSITIONS[event.text]}, {event.when})"
    if event.kind == "resolution":
        return f"DOB's resolution of 311 request {_record_id(event)} ({event.when})"
    return f"{LABELS[event.dataset]} {_record_id(event)} ({event.when})"


def stop_work_then_work_continued(ctx: Context) -> Outcome:
    rule = RULES_BY_ID["stop_work_then_work_continued"]
    warnings = []
    for lot in ctx.pull.lots:
        for event in lot.events:
            if not (_is_work_continued(event) and ctx.since <= event.when and ctx.known(event)):
                continue
            before = [e for e in lot.events if _is_stop_work(e) and e.ref != event.ref
                      and event.when - LOOKBACK <= e.when <= event.when]
            if event.kind == "disposition":
                cited = (f"The disposition of DOB complaint {_record_id(event)} ({event.when}, {_where(lot)}) is a "
                         f"violation for failure to obey a stop-work order.")
            else:
                section = " (28-207.2.2)" if "28-207.2.2" in event.text else ""
                cited = (f"{LABELS[event.dataset]} {_record_id(event)} ({event.when}, {_where(lot)}) cites work "
                         f"contrary to a stop-work order{section}.")
            if before:
                earlier = "; ".join(_mention(e) for e in before[:3])
                cited += f" The order appears earlier in {earlier}."
            else:
                cited += (" Its own text refers to the earlier order; no separate stop-work record dated before "
                          "it was found.")
            warnings.append(_warning(
                ctx, rule.id, event.ref, rule.hazard, rule.severity, "Work continued after a stop-work order",
                f"{cited} This sequence calls for a check of what was done while the order stood.",
                [e.ref for e in before] + [event.ref], event.when,
            ))
    keys = (*VIOLATIONS, "dob_complaints", "dob_311_requests")
    status, detail = _with_problems(
        f"Checked violation text, complaint dispositions and 311 resolutions on {ctx.lots_phrase()}, "
        f"dated in the year {ctx.period()}.",
        _touching_problem(ctx) + dataset_problems(ctx.pull.lots, keys),
    )
    return Outcome(status, detail, warnings, _sources(ctx, ("ecb_violations", "dob_complaints", "dob_311_requests")))


# Earth-work jobs, shared by rules 3 and 4.

@dataclass
class EarthWorkJob:
    job: str  # the job number before the filing suffix, e.g. B01330433
    lot: Lot
    filings: list[dict]
    work: list[str]

    def refs(self) -> list[str]:
        return [f"dob_now_filings:{f.get('job_filing_number')}" for f in self.filings]

    def label(self) -> str:
        suffixes = [str(f.get("job_filing_number", "")).split("-")[-1] for f in self.filings]
        return f"job {self.job} ({', '.join(self.work)}; filing{'s' if len(suffixes) > 1 else ''} {', '.join(suffixes)})"


def _earth_work(filing: dict) -> list[str]:
    names = {"earth_work_work_type_": "earth work", "foundation_work_type_": "foundation",
             "support_of_excavation_work_type_": "support of excavation"}
    work = [names[f] for f in EXCAVATION_FLAGS if str(filing.get(f) or "").strip().upper() in ("YES", "Y", "TRUE")]
    if "support of excavation" not in work and SOE_DESCRIPTION.search(str(filing.get("job_description") or "").upper()):
        work.append("support of excavation per its description")
    return work


def earth_work_jobs(ctx: Context) -> list[EarthWorkJob]:
    jobs: dict[tuple[str, str], EarthWorkJob] = {}
    for lot in ctx.pull.lots:
        result = lot.datasets.get("dob_now_filings") or {}
        for filing in result.get("records", []):
            filed = parse_record_date(filing.get("filing_date"))
            work = _earth_work(filing)
            if not work or filed is None or filed >= ctx.until:
                continue
            number = str(filing.get("job_filing_number") or "")
            job = jobs.setdefault((lot.bbl, number.split("-")[0]), EarthWorkJob(number.split("-")[0], lot, [], []))
            job.filings.append(filing)
            job.work += [w for w in work if w not in job.work]
    return sorted(jobs.values(), key=lambda j: (j.lot.role != "site", j.job))


def _known_date(raw, ctx: Context) -> date | None:
    when = parse_record_date(raw)
    return when if when and when < ctx.until else None


# Rule 3: complaint 30, 14, 16 or 5C within 90 days of an earth-work filing on a touching lot.

def structural_complaint_near_earth_work(ctx: Context) -> Outcome:
    rule = RULES_BY_ID["structural_complaint_near_earth_work"]
    jobs = earth_work_jobs(ctx)
    keys = ("dob_now_filings", "dob_complaints")
    problems = _touching_problem(ctx) + dataset_problems(ctx.pull.lots, ("dob_now_filings",))
    sources = _sources(ctx, keys)
    if not jobs:
        status, detail = _with_problems(
            f"No earth-work, foundation or SOE filing across {ctx.lots_phrase()} {ctx.period()}, so there was "
            f"no earth work next door to check complaints against.", problems)
        return Outcome("not_applicable" if status == "ok" else status, detail, [], sources)

    warnings = []
    for job in jobs:
        starts = [d for f in job.filings for d in (_known_date(f.get("filing_date"), ctx),
                                                    _known_date(f.get("first_permit_date"), ctx)) if d]
        windows = [(start, start + EARTH_WORK_WINDOW) for start in starts]
        neighbors = ctx.pull.touching if job.lot.role == "site" else [ctx.pull.site]
        problems += dataset_problems(neighbors, ("dob_complaints",))
        hits: list[tuple[Lot, Event]] = []
        for lot in neighbors:
            for event in lot.events:
                code = event.text.strip()
                if (event.dataset == "dob_complaints" and event.kind == "record" and code in STRUCTURAL_COMPLAINTS
                        and ctx.known(event) and any(a <= event.when <= b for a, b in windows)):
                    hits.append((lot, event))
        if not hits:
            continue
        hits.sort(key=lambda h: h[1].when)
        by_lot: dict[str, dict[tuple[str, date], list[str]]] = {}
        for lot, e in hits:
            name = "On the site" if lot.role == "site" else (lot.address.title() if lot.address else f"Lot {lot.bbl}")
            by_lot.setdefault(name, {}).setdefault((e.text.strip(), e.when), []).append(_record_id(e))
        listed = "; ".join(
            f"{name}: " + ", ".join(f"{' and '.join(ids)} (code {code}, {when})" for (code, when), ids in groups.items())
            for name, groups in by_lot.items())
        acted = []
        for lot, e in hits:
            for d in lot.events:
                if d.ref == e.ref and d.kind == "disposition" and d.text in VACATE_DISPOSITIONS and ctx.known(d):
                    acted.append(f"{_record_id(e)} led to a {VACATE_DISPOSITIONS[d.text]} ({d.when})")
        where = "the site" if job.lot.role == "site" else _where(job.lot).replace("on ", "", 1)
        nearby = (f"{len(by_lot)} touching lot{'s' if len(by_lot) > 1 else ''}" if job.lot.role == "site"
                  else "the site")
        explanation = (f"Earth-work {job.label()} is on {where}, filed {min(starts)}. Within 90 days of its filing "
                       f"or first permit, {len(hits)} complaint{'s' if len(hits) > 1 else ''} in codes 30, 14, 16 "
                       f"or 5C {'were' if len(hits) > 1 else 'was'} entered on {nearby}. {listed}.")
        if acted:
            explanation += f" DOB's dispositions: {'; '.join(acted)}."
        explanation += " Complaints are reports, not findings; this pattern calls for a look at the neighbors' condition."
        hazard = "structural" if any(e.text.strip() in ("30", "5C") for _, e in hits) else "geotech"
        warnings.append(_warning(
            ctx, rule.id, f"{job.lot.bbl}:{job.job}", hazard, 1 if acted else 0,
            "Structural complaints next door after earth work", explanation,
            [e.ref for _, e in hits] + job.refs(), hits[0][1].when,
        ))
    status, detail = _with_problems(
        f"{len(jobs)} earth-work, foundation or SOE job{'s' if len(jobs) > 1 else ''} across {ctx.lots_phrase()}, "
        f"each checked for complaints in codes 30, 14, 16 or 5C on the lots next to it within 90 days of its "
        f"filing or first permit, {ctx.period()}.",
        list(dict.fromkeys(problems)),
    )
    return Outcome(status, detail, warnings, sources)


# Rule 4: heavy rain (over 25 mm in a day) or a freeze-thaw day during an open excavation.

def _open_period(job: EarthWorkJob, ctx: Context) -> tuple[date, date] | None:
    """From the first earth-work permit to a sign-off, or to the last day known."""
    permits = [d for f in job.filings if (d := _known_date(f.get("first_permit_date"), ctx))]
    if not permits:
        return None
    end = min(ctx.until - timedelta(days=1), ctx.pull.pulled_on)
    for f in job.filings:
        closed = _known_date(f.get("signoff_date"), ctx)
        if closed is None and SIGNED_OFF.search(str(f.get("filing_status") or "")):
            closed = _known_date(f.get("current_status_date"), ctx)
        if closed:
            end = min(end, closed)
    start = min(permits)
    return (start, end) if start <= end else None


def weather_during_open_excavation(ctx: Context) -> Outcome:
    rule = RULES_BY_ID["weather_during_open_excavation"]
    problems = _touching_problem(ctx) + dataset_problems(ctx.pull.lots, ("dob_now_filings",))
    sources = _sources(ctx, ("dob_now_filings",))
    open_jobs = [(job, period) for job in earth_work_jobs(ctx) if (period := _open_period(job, ctx))]
    if not open_jobs:
        status, detail = _with_problems(
            f"No earth-work, foundation or SOE permit across {ctx.lots_phrase()} was issued {ctx.period()}, so there "
            f"was no open excavation to check the weather against.", problems)
        return Outcome("not_applicable" if status == "ok" else status, detail, [], sources)
    if ctx.pull.lat is None or ctx.pull.lon is None:
        return Outcome("error", "The site has no coordinates, so the weather couldn't be looked up.", [], sources)

    warnings, checked = [], []
    for job, (start, end) in open_jobs:
        try:
            weather = ctx.weather(ctx.pull.lat, ctx.pull.lon, start, end)
        except weather_source.WeatherError as error:
            problems.append(f"{weather_source.SOURCE_NAME} couldn't load for {job.job} ({error})")
            continue
        sources.append(Source(name=weather_source.SOURCE_NAME, url=weather.url, date=end.isoformat()))
        missing = sum(1 for d in weather.days if d.precipitation_mm is None or d.min_c is None or d.max_c is None)
        if missing:
            problems.append(f"{missing} of {len(weather.days)} days for {job.job} have no weather data")
        rain = [d for d in weather.days if d.precipitation_mm is not None and d.precipitation_mm > HEAVY_RAIN_MM]
        frost = [d for d in weather.days if d.min_c is not None and d.max_c is not None and d.min_c < 0 < d.max_c]
        checked.append(f"{job.job} open {start} to {end}")
        if not (rain or frost):
            continue
        parts = []
        if rain:
            days = ", ".join(f"{d.day} ({d.precipitation_mm:.0f} mm)" for d in rain[:4])
            parts.append(f"{len(rain)} day{'s' if len(rain) > 1 else ''} over {HEAVY_RAIN_MM:.0f} mm of rain: {days}"
                         + (" and more" if len(rain) > 4 else ""))
        if frost:
            days = ", ".join(str(d.day) for d in frost[:4])
            parts.append(f"{len(frost)} freeze-thaw day{'s' if len(frost) > 1 else ''} (below and above 0 °C the "
                         f"same day): {days}" + (" and more" if len(frost) > 4 else ""))
        title = ("Heavy rain and freeze-thaw" if rain and frost else "Heavy rain" if rain else "Freeze-thaw")
        where = "the site" if job.lot.role == "site" else _where(job.lot).replace("on ", "", 1)
        flagged = sorted(rain + frost, key=lambda d: d.day)
        warnings.append(_warning(
            ctx, rule.id, f"{job.lot.bbl}:{job.job}", "weather", 0, f"{title} during an open excavation",
            f"Earth-work {job.label()} on {where} has had a permit since {start} with no sign-off recorded "
            f"through {end}. {weather_source.SOURCE_NAME} at the site shows {' and '.join(parts)}. "
            f"{'Heavy rain and frost are' if rain and frost else 'Heavy rain is' if rain else 'Frost is'} often "
            f"material to excavation support; check that monitoring covered these days.",
            job.refs() + [f"open_meteo:{d.day}" for d in flagged], flagged[0].day,
        ))
    if checked:
        checked_text = (f"Daily rain and temperature checked for {'; '.join(checked)}: heavy rain is over "
                        f"{HEAVY_RAIN_MM:.0f} mm in a day, freeze-thaw is a day that goes below and above 0 °C.")
    else:
        checked_text = f"{len(open_jobs)} open excavation{'s' if len(open_jobs) > 1 else ''}, but no weather was checked."
    status, detail = _with_problems(checked_text, problems)
    return Outcome(status, detail, warnings, sources)


RULES = [
    Rule("adjacent_protection_no_follow_up", "Adjacent-protection violation, then nothing recorded for 21 days",
         "structural", 1, adjacent_protection_no_follow_up),
    Rule("stop_work_then_work_continued", "Stop-work order, then a violation for continuing work",
         "construction_safety", 1, stop_work_then_work_continued),
    Rule("structural_complaint_near_earth_work", "Structural complaint within 90 days of earth work next door",
         "structural", 0, structural_complaint_near_earth_work),
    Rule("weather_during_open_excavation", "Heavy rain or freeze-thaw during an open excavation",
         "weather", 0, weather_during_open_excavation),
]
RULES_BY_ID = {rule.id: rule for rule in RULES}


def evaluate(pull: SitePull, as_of: date | None = None, weather=weather_source.daily_weather
             ) -> tuple[list[EarlyWarning], list[WarningRuleCheck]]:
    """Every rule over one site: the warnings (most severe, then newest, first) and one check per rule."""
    ctx = Context(pull, as_of, weather)
    warnings, checks = [], []
    for rule in RULES:
        outcome = rule.check(ctx)
        warnings += outcome.warnings
        checks.append(WarningRuleCheck(
            rule_id=rule.id, title=rule.title, status=outcome.status, detail=outcome.detail,
            warnings=len(outcome.warnings), sources=outcome.sources,
            as_of=as_of.isoformat() if as_of else None,
        ))
    warnings.sort(key=lambda w: (w["severity"], w["first_seen"]), reverse=True)
    return [EarlyWarning.model_validate(w) for w in warnings], checks
