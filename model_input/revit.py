"""Read the Revit reader's `structural_model.json` into a `StructuralModel`.

The reader (one-way, one button) exports the structural system, foundations and the bearing walls on the
lot line. Its final output format has not arrived yet, so this accepts the contract shape (the stand-in in
`contracts/fixtures/structural_model.json`), either bare or wrapped as {"structural_model": {...}}, and
normalizes it. Anything it cannot read is rejected with the reason, never guessed.
"""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from api.contracts import StructuralModel


class ModelInputError(ValueError):
    """The uploaded model could not be read."""


_SIDES = {"n": "north", "s": "south", "e": "east", "w": "west"}


def _side(value: Any) -> str:
    text = str(value or "").strip().lower()
    if text in _SIDES.values():
        return text
    return _SIDES.get(text[:1], "unknown") if text else "unknown"


def _text(value: Any):
    text = " ".join(str(value).split()) if value is not None else ""
    return text or None


def read_revit(payload: Any) -> dict:
    if isinstance(payload, dict) and isinstance(payload.get("structural_model"), dict):
        payload = payload["structural_model"]
    if not isinstance(payload, dict):
        raise ModelInputError("expected a JSON object from the Revit reader")
    walls = payload.get("bearing_walls_on_lot_line") or []
    if not isinstance(walls, list):
        raise ModelInputError("bearing_walls_on_lot_line must be a list")
    model = {
        "source": "revit",
        "material": _text(payload.get("material")),
        "gravity_system": _text(payload.get("gravity_system")),
        "lateral_system": _text(payload.get("lateral_system")),
        "foundation_type": _text(payload.get("foundation_type")),
        "bearing_walls_on_lot_line": [
            {"id": str(w.get("id") or f"wall-{i + 1}"), "side": _side(w.get("side")),
             "material": _text(w.get("material")), "length_ft": w.get("length_ft")}
            for i, w in enumerate(walls) if isinstance(w, dict)
        ],
        "levels": payload.get("levels"),
        "confidence": payload.get("confidence", 0.9),
    }
    try:
        return StructuralModel.model_validate(model).model_dump()
    except ValidationError as error:
        raise ModelInputError(f"the Revit model does not match the contract: {error.errors()[0]['msg']}") from error
