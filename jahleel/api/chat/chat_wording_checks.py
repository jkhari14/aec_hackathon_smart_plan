"""Checks on the words of a statement. Each returns a reason to hold the statement back, or None.

Only the number check is exact. The rest are word lists: they catch the plain phrasings and miss
others, so they back up the prompt and do not replace reading the answer (see the README's limits).
"""

import re
from typing import Optional

_DIGITS = re.compile(r"\d+")
_RECORD_NOUN = r"(?:records?|violations?|complaints?|filings?|requests?|permits?|orders?|summons(?:es)?|inspections?)"
_COUNT_WORD = (r"(?:two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|"
               r"sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|several|many|multiple|numerous|"
               r"few|dozens?|hundreds?|thousands?)")
# A count in words, or a short number standing before a record noun ("4 ECB violations") and not part of a
# date, an id or a section number. The number check alone would pass a 4 that sits in the cited record's date.
_TYPED_COUNT = re.compile(
    rf"\b{_COUNT_WORD}\b(?:\s+\w+){{0,2}}?\s+{_RECORD_NOUN}\b"
    rf"|(?<![\d.\-/§:])\b(?!311\b)\d{{1,3}}\b(?![\d.\-/:,])(?:\s+[A-Za-z]+){{0,2}}?\s+{_RECORD_NOUN}\b", re.I)
_ABSENCE = re.compile(
    rf"\b(?:no|zero|not any|none|never)\b[^.;]{{0,40}}\b{_RECORD_NOUN}\b"
    r"|\b(?:none|nothing)\s+(?:was|were|is|are|has been|have been)?\s*(?:found|recorded|reported|on record|on file)\b"
    r"|\b(?:there (?:is|are|was|were) (?:no|none)|has never|have never|does not exist|do not exist)\b", re.I)
_VERDICT = re.compile(
    r"\b(?:is|are|was|were|appears?|seems?|looks?)\s+(?:\w+\s+)?(?:code[- ])?(?:compliant|non-?compliant|safe|unsafe|"
    r"sound|adequate|inadequate|legal|illegal|dangerous)\b"
    r"|\b(?:complies|does not comply|fails? to comply|in (?:full )?compliance|out of compliance|not in compliance|"
    r"structurally sound|safe to (?:dig|build|excavate|proceed|occupy)|no (?:risk|danger|hazard)|at risk of collaps)\w*", re.I)
_BLAME = re.compile(
    r"\b(?:would|could|might|should|may)(?:\s+not)?\s+have\s+(?:been\s+)?(?:prevent|avoid|stopp|caught|known|done|acted)\w*"
    r"|\b(?:at fault|to blame|blamed?|negligen\w+|reckless\w*|liable|liability|responsible for the (?:collapse|incident|"
    r"failure|deaths?)|failed to (?:prevent|protect|act))\b", re.I)
_CAUSE = re.compile(r"\b(?:caus(?:e[ds]?|ing)|led to|resulted in|result of|due to|because of|triggered|brought down)\b", re.I)
_REPORTED = re.compile(r"\b(?:report(?:ed|s|ing)?|according to|officials? (?:say|said)|under investigation)\b", re.I)
_COMPANY = re.compile(r"\b(?:LLC|L\.L\.C\.|Inc\.?|Corp\.?|Corporation|Ltd\.?|LLP|PLLC|P\.C\.|Realty)(?=\W|$)", re.I)
_QUOTED = re.compile(r"[\"\u201c]([^\"\u201c\u201d]{3,300})[\"\u201d]")


def _runs(text: str) -> set[str]:
    return {run.lstrip("0") or "0" for run in _DIGITS.findall(text)}


def untraceable_numbers(text: str, evidence: str) -> Optional[str]:
    """Every run of digits in the statement must appear in the items it cites."""
    missing = sorted(_runs(text) - _runs(evidence))
    if missing:
        return ("these numbers are not in the items cited: " + ", ".join(missing)
                + ". Quote numbers as the brief has them, and use a dataset_check for any count.")
    return None


def typed_count(text: str) -> Optional[str]:
    match = _TYPED_COUNT.search(text)
    return f"'{match.group()}' states a count: use a dataset_check, which writes the count." if match else None


def absence_claim(text: str) -> Optional[str]:
    match = _ABSENCE.search(text)
    return (f"'{match.group()}' says something is absent: only a dataset_check or a gap may say that."
            if match else None)


def verdict(text: str) -> Optional[str]:
    match = _VERDICT.search(text)
    return (f"'{match.group()}' reads as a verdict on compliance or safety: state what the record shows and add "
            "the not_a_determination notice.") if match else None


def blame(text: str) -> Optional[str]:
    match = _BLAME.search(text)
    return f"'{match.group()}' assigns blame or says what would have changed the outcome." if match else None


def cause(text: str, is_lead: bool) -> Optional[str]:
    """The public record never establishes a cause. A lead may relay one only as reported."""
    match = _CAUSE.search(text)
    if not match or (is_lead and _REPORTED.search(text)):
        return None
    return (f"'{match.group()}' states a cause: say only what a source reports, as reported, or that it is "
            "under investigation.")


def company_name(text: str) -> Optional[str]:
    match = _COMPANY.search(text)
    return f"'{match.group()}' looks like a company name: leave out owners, applicants and contractors." if match else None


def _squash(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def _without_record_quotes(text: str, evidence: str) -> str:
    """Words quoted exactly from a cited item are the record's, not the model's: the word lists skip them."""
    held = _squash(evidence)
    return _QUOTED.sub(lambda m: " " if _squash(m.group(1)) in held else m.group(), text)


def statement_problems(text: str, evidence: Optional[str], is_lead: bool) -> list[str]:
    """`evidence` is None for a web statement: a result's text is not ours to read, so its numbers go unchecked."""
    own = _without_record_quotes(text, evidence) if evidence is not None else text
    found = [typed_count(own), absence_claim(own), verdict(own), blame(own), cause(own, is_lead),
             company_name(own)]
    if evidence is not None:
        found.append(untraceable_numbers(text, evidence))
    return [reason for reason in found if reason]
