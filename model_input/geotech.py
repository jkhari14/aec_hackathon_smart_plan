"""Read a geotechnical report (PDF) with Claude into `GeotechFindings`: groundwater, soil, bearing, rock.

Same rules as the drawing reader: needs `anthropic` and ANTHROPIC_API_KEY (else `DrawingUnavailable`, so
the API says it could not read the report and nothing is guessed); the reading is a suggestion the
uploader checks and confirms, so its confidence is capped at MAX_CONFIDENCE.
"""

from __future__ import annotations

from api.contracts import GeotechFindings
from model_input.drawing import MAX_CONFIDENCE, ask_pdf

PROMPT = """This is a geotechnical (subsurface investigation) report for a building site in New York City.
Read it and report the findings a structural engineer, architect and contractor need.

Report only what the report states. When something is not stated, use null rather than a guess.
- groundwater_depth_ft: the shallowest depth below existing grade at which groundwater was measured or encountered, in feet.
- soil_description: the soil profile in one short line, top to bottom (for example "6 ft of fill over medium dense fine sand").
- allowable_bearing_tsf: the recommended allowable bearing pressure for footings, in tons per square foot.
- rock_depth_ft: depth below grade to bedrock, if reached; null if not reached.
- boring_count: number of borings or test pits.
- max_boring_depth_ft: the deepest boring, in feet below grade.
- confidence: 0 to 1, how clearly the report states these.
- evidence: one or two sentences naming the borings, tables or sections you relied on."""

_NUM = {"type": ["number", "null"]}
SCHEMA = {
    "type": "object",
    "properties": {
        "groundwater_depth_ft": _NUM,
        "soil_description": {"type": ["string", "null"]},
        "allowable_bearing_tsf": _NUM,
        "rock_depth_ft": _NUM,
        "boring_count": {"type": ["integer", "null"]},
        "max_boring_depth_ft": _NUM,
        "confidence": {"type": "number"},
        "evidence": {"type": "string"},
    },
    "required": ["groundwater_depth_ft", "soil_description", "allowable_bearing_tsf", "rock_depth_ft",
                 "boring_count", "max_boring_depth_ft", "confidence", "evidence"],
    "additionalProperties": False,
}


def to_findings(answer: dict) -> tuple[dict, str]:
    """(GeotechFindings dict, evidence) from the model's JSON answer."""
    findings = {key: answer.get(key) for key in SCHEMA["required"] if key not in ("confidence", "evidence")}
    findings["confidence"] = round(min(max(float(answer.get("confidence") or 0), 0.0), MAX_CONFIDENCE), 2)
    return GeotechFindings.model_validate(findings).model_dump(), str(answer.get("evidence") or "")


def read_geotech(pdf: bytes, client=None) -> tuple[dict, str]:
    """Findings from a geotechnical report PDF. Returns (GeotechFindings dict, evidence)."""
    return to_findings(ask_pdf(pdf, PROMPT, SCHEMA, client))
