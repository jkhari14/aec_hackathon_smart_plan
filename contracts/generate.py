"""Write the contracts in api/contracts.py out as JSON Schemas and the API's OpenAPI document.

Run after any contract change, then `npm run contracts` in web/ for the TypeScript types:

    .venv/bin/python -m contracts.generate
"""

from __future__ import annotations

import json
from pathlib import Path

from api import contracts
from api.main import app

ROOT = Path(__file__).resolve().parent.parent
SCHEMAS = ROOT / "contracts" / "schemas"
OPENAPI = ROOT / "api" / "openapi.json"


def schema_files() -> dict[Path, str]:
    """Every generated file and its expected contents."""
    files: dict[Path, str] = {}
    for name, (model, is_list) in contracts.FIXTURES.items():
        schema = model.model_json_schema()
        if is_list:
            defs = schema.pop("$defs", None)
            schema = {"title": f"{model.__name__} list", "type": "array", "items": schema}
            if defs:
                schema["$defs"] = defs
        files[SCHEMAS / f"{name}.schema.json"] = json.dumps(schema, indent=2) + "\n"
    files[OPENAPI] = json.dumps(app.openapi(), indent=2) + "\n"
    return files


def main() -> None:
    SCHEMAS.mkdir(parents=True, exist_ok=True)
    for path, text in schema_files().items():
        path.write_text(text)
        print(f"wrote {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
