"""The sources a person may import by hand, and what one import of each may hold.

A source is listed here only when its terms allow a person to download or read it and us to
keep facts taken from it. docs/manual_data_imports.md gives the verdict and the terms clause
for every source we looked at, including the ones we must not use.

Each source says:
- hosts: where the file or page may come from. A copy found on another site is a hint, not
  the source, and the loader refuses it.
- fetch_methods: "browser_by_person" (a person opened it in a browser) and, only where the
  terms and the site allow scripts, "script_with_approval" (a script fetched it after a
  person approved that one download).
- raw_required: whether the import must describe a downloaded file (name, size, sha256).
- fields: the fact fields, True when required. No source has a field for a person's name.
- terms: the clause behind the verdict, as read on the date given; new_import copies it into
  each import, which must say when it was read.
- verdicts: the verdicts an import of this source may carry. "a": a script may fetch it;
  "b": a person downloads it within the terms; "c": only under a license. "d" is never imported.
"""

from __future__ import annotations

OPEN_DATA_LAW = {
    "url": "https://nycadmincode.readthedocs.io/t23/c05/#section-23-502",
    "clause": "NYC Admin. Code 23-502(d): public data sets \"shall be made available without any "
              "registration requirement, license requirement or restrictions on their use\".",
    "read_on": "2026-11-14",
    "verdict": "a",
    "note": "Read on an unofficial mirror of the Administrative Code; the official host "
            "(codelibrary.amlegal.com) disallows Anthropic's crawlers in its robots.txt.",
}

NYC_GOV_TERMS = {
    "url": "https://www.nyc.gov/main/terms-of-use",
    "clause": "Section IV.1: content on NYC.gov is the property of the City of New York; all rights "
              "reserved. No clause on automated access.",
    "read_on": "2026-11-14",
    "verdict": "b",
    "note": "www.nyc.gov and the DOB NOW portal answered scripts with HTTP 403 on 2026-11-14. We do "
            "not get around that: a person opens the page or file in a browser.",
}

SOURCES: dict[str, dict] = {
    "dob_complaint_categories": {
        "name": "DOB complaint category codes, from a list DOB published",
        "landing_url": "https://data.cityofnewyork.us/d/eabe-havv",
        # The Open Data attachment (Rev. 12/18) or DOB's newer list on nyc.gov, which scripts get a 403 for.
        "hosts": {"data.cityofnewyork.us", "www.nyc.gov"},
        "fetch_methods": {"browser_by_person", "script_with_approval"},
        "raw_required": True,
        "fields": {"code": True, "description": True, "priority": False, "page": True},
        "unique": "code",
        "terms": OPEN_DATA_LAW,
        "verdicts": {"a", "b"},
    },
    "dob_complaint_dispositions": {
        "name": "DOB complaint disposition codes, from a list DOB published",
        "landing_url": "https://data.cityofnewyork.us/d/6v9u-ndjg",
        # Open Data 6v9u-ndjg is a live table (last updated 2017); import only a newer DOB list.
        "hosts": {"data.cityofnewyork.us", "www.nyc.gov"},
        "fetch_methods": {"browser_by_person", "script_with_approval"},
        "raw_required": True,
        "fields": {"code": True, "description": True, "page": True},
        "unique": "code",
        "terms": NYC_GOV_TERMS,
        "verdicts": {"a", "b"},
    },
    "dob_now_document": {
        "name": "A document on the DOB NOW public portal (Documents tab of a job filing)",
        "landing_url": "https://a810-dobnow.nyc.gov/publish/#!/",
        "hosts": {"a810-dobnow.nyc.gov"},
        "fetch_methods": {"browser_by_person"},
        "raw_required": True,
        "fields": {"job_filing_number": True, "document_title": True, "document_date": False,
                   "fact": True, "page": True},
        "unique": None,
        "terms": NYC_GOV_TERMS,
        "verdicts": {"b"},
    },
    "precedent_report": {
        "name": "A news article or published investigation report about a past incident",
        "landing_url": None,
        "hosts": None,  # any https host; the person records the publisher's terms
        "fetch_methods": {"browser_by_person"},
        "raw_required": False,  # read in a browser; nothing is downloaded
        "fields": {"event_date": True, "address": True, "bbl": False, "event_type": True,
                   "fact": True, "quote": False, "locator": True},
        "unique": None,
        "terms": None,  # differs per publisher; each import must state it
        "verdicts": {"b", "c"},
    },
}

# The terms that govern a file depend on the host it came from, whatever the source.
HOST_TERMS = {
    "data.cityofnewyork.us": OPEN_DATA_LAW,
    "www.nyc.gov": NYC_GOV_TERMS,
    "a810-dobnow.nyc.gov": NYC_GOV_TERMS,
}


def terms_for(source_key: str, host: str | None) -> dict | None:
    return HOST_TERMS.get(host or "") or SOURCES[source_key]["terms"]


# A fact or quote longer than this is not a short quote; the repository is public.
MAX_QUOTE_WORDS = 25
