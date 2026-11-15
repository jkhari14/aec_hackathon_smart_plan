"""Read a structural drawing (PDF) with Claude and classify the structural system into a `StructuralModel`.

Needs the `anthropic` package and a key in the environment (ANTHROPIC_API_KEY, never in code). Without
either, `read_drawing` raises `DrawingUnavailable` and the API says so: nothing is guessed.

A drawing read by AI is a suggestion for the engineer to confirm, so the confidence is capped at
MAX_CONFIDENCE, below a Revit export's.
"""

from __future__ import annotations

import base64
import json
from typing import Optional

from api.contracts import StructuralModel

MODEL = "claude-opus-5-5"
FALLBACK_BETA = "server-side-fallback-2026-07-01"
MAX_PDF_BYTES = 30 * 1024 * 1024  # the request limit is 32 MB including the base64 overhead
MAX_CONFIDENCE = 0.7

PROMPT = """These are architectural or structural drawings for a building in New York City.
Read them and classify the building's structural system for a structural engineer.

Report only what the drawings show or state. When something is not shown, use null rather than a guess.
- material: the primary structural material (for example "unreinforced brick masonry", "reinforced concrete", "steel frame", "wood frame").
- gravity_system: how floors and roofs carry load down (for example "wood joists on masonry bearing walls").
- lateral_system: what resists wind and seismic load.
- foundation_type: footings, mat, piles, caissons and so on, as drawn.
- bearing_walls_on_lot_line: walls on or at the property line that carry load, with side (north, south, east, west, or unknown), material and length in feet when dimensioned.
- levels: number of stories above grade, if shown.
- confidence: 0 to 1, how clearly the drawings show the system.
- evidence: one or two sentences naming the sheets or notes you relied on."""

_NULLABLE_STRING = {"type": ["string", "null"]}
SCHEMA = {
    "type": "object",
    "properties": {
        "material": _NULLABLE_STRING,
        "gravity_system": _NULLABLE_STRING,
        "lateral_system": _NULLABLE_STRING,
        "foundation_type": _NULLABLE_STRING,
        "bearing_walls_on_lot_line": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "side": {"type": "string", "enum": ["north", "south", "east", "west", "unknown"]},
                    "material": _NULLABLE_STRING,
                    "length_ft": {"type": ["number", "null"]},
                },
                "required": ["side", "material", "length_ft"],
                "additionalProperties": False,
            },
        },
        "levels": {"type": ["integer", "null"]},
        "confidence": {"type": "number"},
        "evidence": {"type": "string"},
    },
    "required": ["material", "gravity_system", "lateral_system", "foundation_type",
                 "bearing_walls_on_lot_line", "levels", "confidence", "evidence"],
    "additionalProperties": False,
}


class DrawingUnavailable(Exception):
    """The drawing could not be read: no SDK, no key, a refusal, or an API error."""


def _client():
    try:
        import anthropic
    except ImportError as error:
        raise DrawingUnavailable("drawing reading needs the anthropic package (pip install anthropic)") from error
    try:
        return anthropic, anthropic.Anthropic()
    except anthropic.AnthropicError as error:  # no credentials in the environment
        raise DrawingUnavailable(f"no Anthropic credentials: {error}") from error


def to_model(answer: dict) -> tuple[dict, str]:
    """(StructuralModel dict, evidence) from the model's JSON answer."""
    model = {
        "source": "drawing",
        "material": answer.get("material"),
        "gravity_system": answer.get("gravity_system"),
        "lateral_system": answer.get("lateral_system"),
        "foundation_type": answer.get("foundation_type"),
        "bearing_walls_on_lot_line": [
            {"id": f"drawing-wall-{i + 1}", "side": w.get("side") or "unknown",
             "material": w.get("material"), "length_ft": w.get("length_ft")}
            for i, w in enumerate(answer.get("bearing_walls_on_lot_line") or [])
        ],
        "levels": answer.get("levels"),
        "confidence": round(min(max(float(answer.get("confidence") or 0), 0.0), MAX_CONFIDENCE), 2),
    }
    return StructuralModel.model_validate(model).model_dump(), str(answer.get("evidence") or "")


def read_drawing(pdf: bytes, client=None) -> tuple[dict, str]:
    """Classify the structural system in a PDF. Returns (StructuralModel dict, evidence)."""
    if not pdf.startswith(b"%PDF"):
        raise ValueError("the upload is not a PDF")
    if len(pdf) > MAX_PDF_BYTES:
        raise ValueError("the PDF is larger than 30 MB; upload the structural sheets only")
    anthropic, default_client = _client() if client is None else (None, client)
    client = client or default_client
    request = dict(
        model=MODEL,
        max_tokens=16000,
        output_config={"effort": "medium", "format": {"type": "json_schema", "schema": SCHEMA}},
        messages=[{"role": "user", "content": [
            {"type": "document", "source": {"type": "base64", "media_type": "application/pdf",
                                            "data": base64.standard_b64encode(pdf).decode("ascii")}},
            {"type": "text", "text": PROMPT},
        ]}],
    )
    # AnthropicError covers API errors and missing credentials found at request time.
    errors = (anthropic.AnthropicError,) if anthropic else (Exception,)
    try:
        try:
            response = client.beta.messages.create(**request, betas=[FALLBACK_BETA], fallbacks="default")
        except errors as error:
            if getattr(error, "status_code", None) != 400:
                raise
            # Server-side fallback is a beta: if the API rejects it, ask once more without it.
            response = client.beta.messages.create(**request)
    except errors as error:
        raise DrawingUnavailable(f"the drawing could not be read ({type(error).__name__})") from error
    if response.stop_reason == "refusal":
        raise DrawingUnavailable("the model declined to read this drawing")
    if response.stop_reason == "max_tokens":
        raise DrawingUnavailable("the answer was cut off; upload fewer sheets")
    text: Optional[str] = next((b.text for b in response.content if b.type == "text"), None)
    if not text:
        raise DrawingUnavailable("the model returned no answer")
    return to_model(json.loads(text))
