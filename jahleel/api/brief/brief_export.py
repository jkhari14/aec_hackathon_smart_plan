"""Write the API schema and every cached brief as static files, so the web app works with no API running.

python -m jahleel.api.brief.brief_export   ->  jahleel/api/openapi.json, jahleel/web/public/demo_briefs/...
"""

import json
import sys
from datetime import date

from jahleel.api.brief.brief_build import FOLDER, build_brief, list_slugs
from jahleel.api.preflight_api import app

# The demo's replay dates also get static copies, so the replay works with no API running.
DEMO_AS_OF = [date(2026, 6, 1), date(2026, 11, 11)]


def main() -> int:
    (FOLDER / "api" / "openapi.json").write_text(json.dumps(app.openapi(), indent=1))
    out_dir = FOLDER / "web" / "public" / "demo_briefs"
    out_dir.mkdir(parents=True, exist_ok=True)
    index = []
    for slug in list_slugs():
        brief = build_brief(slug)
        (out_dir / f"{slug}.json").write_text(brief.model_dump_json(indent=1))
        for day in DEMO_AS_OF:
            (out_dir / f"{slug}.as-of-{day}.json").write_text(build_brief(slug, as_of=day).model_dump_json(indent=1))
        index.append({"slug": slug, "address": brief.matched_label, "project_type": brief.project_type,
                      "demo_as_of": [str(day) for day in DEMO_AS_OF]})
    (out_dir / "index.json").write_text(json.dumps(index, indent=1))
    print(f"wrote jahleel/api/openapi.json and {len(index)} demo briefs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
