"""The project store's tables, closed value sets and size caps.

The closed sets come from api/contracts.py, so the store and the contract cannot drift apart. One
SQLite file holds every project; each write bumps its project's `version`, which a browser tab polls
(as an ETag) to see the other tab's work.
"""

from typing import get_args

from api.contracts import ActionItem, Discipline, Hazard, ProjectPin, Role, Stage

ROLES = get_args(Role)
STAGES = get_args(Stage)
DISCIPLINES = get_args(Discipline)
HAZARDS = get_args(Hazard)
ITEM_STATUSES = get_args(ActionItem.model_fields["status"].annotation)
PIN_KINDS = get_args(ProjectPin.model_fields["kind"].annotation)

# A request over a cap is refused, never cut, so one project cannot grow without bound.
MAX_TEXT = {"name": 120, "member_name": 80, "title": 200, "ref": 200, "note": 4000, "item_text": 2000}
MAX_MODEL_BYTES = 200_000
MAX_ROWS_PER_PROJECT = {"members": 20, "items": 500, "notes": 2000, "pins": 500}


def _one_of(column: str, values: tuple[str, ...], nullable: bool = False) -> str:
    allowed = f"{column} IN ({', '.join(repr(v) for v in values)})"
    return f"CHECK ({column} IS NULL OR {allowed})" if nullable else f"CHECK ({allowed})"


DDL = f"""
CREATE TABLE IF NOT EXISTS projects (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  site_bbl TEXT NOT NULL,
  stage TEXT NOT NULL {_one_of("stage", STAGES)},
  structural_model_json TEXT,
  version INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS members (
  project_id TEXT NOT NULL REFERENCES projects(id),
  position INTEGER NOT NULL,
  name TEXT NOT NULL,
  role TEXT NOT NULL {_one_of("role", ROLES)},
  PRIMARY KEY (project_id, position)
);
CREATE TABLE IF NOT EXISTS items (
  project_id TEXT NOT NULL REFERENCES projects(id),
  id TEXT NOT NULL,
  position INTEGER NOT NULL,
  discipline TEXT NOT NULL {_one_of("discipline", DISCIPLINES)},
  hazard TEXT NOT NULL {_one_of("hazard", HAZARDS)},
  title TEXT NOT NULL,
  why TEXT NOT NULL,
  code_ref TEXT,
  proof_needed TEXT,
  status TEXT NOT NULL {_one_of("status", ITEM_STATUSES)},
  owner_role TEXT {_one_of("owner_role", ROLES, nullable=True)},
  source_rule TEXT NOT NULL,
  life_safety INTEGER NOT NULL CHECK (life_safety IN (0, 1)),
  updated_at TEXT NOT NULL,
  PRIMARY KEY (project_id, id)
);
CREATE TABLE IF NOT EXISTS notes (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL REFERENCES projects(id),
  author_role TEXT NOT NULL {_one_of("author_role", ROLES)},
  text TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS pins (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL REFERENCES projects(id),
  kind TEXT NOT NULL {_one_of("kind", PIN_KINDS)},
  ref_id TEXT NOT NULL,
  title TEXT NOT NULL,
  by_role TEXT NOT NULL {_one_of("by_role", ROLES)},
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS notes_by_project ON notes(project_id);
CREATE INDEX IF NOT EXISTS pins_by_project ON pins(project_id);
"""
