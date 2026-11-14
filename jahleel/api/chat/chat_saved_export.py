"""Write every saved example's answer as static files, so the chat panel works with no API running.

python -m jahleel.api.chat.chat_saved_export   ->  jahleel/web/src/features/chat/saved/<slug>[.as-of-DATE].json

Run it after the briefs or the saved examples change. Each file holds the answers exactly as the API
would return them for that site and as-of day.
"""

import json
import sys
from datetime import date

from jahleel.api.brief.brief_build import FOLDER, list_slugs
from jahleel.api.chat import chat_service
from jahleel.api.chat.chat_models import ChatRequest
from jahleel.api.chat.chat_saved_examples import examples_for

# The same replay days the brief export saves (jahleel/api/brief/brief_export.py).
DEMO_AS_OF = [date(2026, 6, 1), date(2026, 11, 11)]
OUT_DIR = FOLDER / "web" / "src" / "features" / "chat" / "saved"


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    written = 0
    for slug in list_slugs():
        for day in [None] + DEMO_AS_OF:
            answers = [chat_service.answer(ChatRequest(slug=slug, as_of=day, example_id=example.id)).model_dump(mode="json")
                       for example in examples_for(slug)]
            name = f"{slug}.as-of-{day}.json" if day else f"{slug}.json"
            (OUT_DIR / name).write_text(json.dumps(answers, indent=1) + "\n")
            written += 1
    print(f"wrote {written} saved chat files to {OUT_DIR.relative_to(FOLDER.parent)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
