"""New York State DEC's Environmental Remediation Sites (c6ci-rzpg on data.ny.gov), the five boroughs.

The dataset repeats a site once per project, contaminant and party, so rows far outnumber sites;
here each site (`program_number`) appears once, with the contaminants its rows list. It has no lot
or BBL column, only coordinates, so matching a site to a lot is a distance test, not a join.

Owner, operator and disposal names, and the facility name (often a business), are never requested.
Program and site-class wording is the dataset's own column description; a code it does not list is
shown as the code.
"""

from __future__ import annotations

from datetime import date

from city_layers import source_rows
from city_layers.layer_file import LayerInfo, Pulled, feature, left_out, point, point_geometry

DATASET = "c6ci-rzpg"
PORTAL = "data.ny.gov"
COUNTIES = {"New York": "Manhattan", "Bronx": "Bronx", "Kings": "Brooklyn", "Queens": "Queens", "Richmond": "Staten Island"}
# Both tables are the dataset's column descriptions (read 2026-11-14), the class wording shortened.
PROGRAMS = {"HW": "State Superfund Program", "BCP": "Brownfield Cleanup Program", "VCP": "Voluntary Cleanup Program",
            "ERP": "Environmental Restoration Program", "RCRA": "Hazardous Waste Management Program"}
SITE_CLASSES = {
    "02": "the disposal of hazardous waste represents a significant threat to the environment or to health",
    "03": "contamination does not presently constitute a significant threat to the environment or to health",
    "04": "properly closed, but requires continued site management",
    "05": "no further action required",
    "A": "active",
    "C": "completed",
    "P": "preliminary information indicates the site may have contamination",
    "PR": "is, or has been, subject to the requirements of RCRA",
    "N": "no further action",
}
MAX_CONTAMINANTS = 6
INFO = LayerInfo(
    layer_id="remediation_sites",
    name="State remediation sites",
    description="Sites in New York State DEC's remediation programs (brownfield, voluntary cleanup, "
    "state superfund and others) in the five boroughs, one mark per site with the contaminants DEC lists. "
    "Being listed is not a finding about today's condition: many sites are cleaned up and closed.",
    hazard="contamination",
    source_name="NYS DEC Environmental Remediation Sites",
    source_url=f"https://{PORTAL}/d/{DATASET}",
    default_on=False,
)
SELECT = "program_number,program_type,siteclass,address1,county,latitude,longitude,contaminants"
GROUP = SELECT


def where() -> str:
    return "county in (" + ",".join(f"'{county}'" for county in COUNTIES) + ")"


def sites_from_rows(rows: list[dict]) -> list[dict]:
    """One dict per program number, in first-seen order, with its contaminants gathered and sorted."""
    sites: dict[str, dict] = {}
    for row in rows:
        number = str(row.get("program_number") or "").strip()
        if not number:
            continue
        site = sites.setdefault(number, {**row, "_contaminants": set()})
        for key in ("latitude", "longitude", "address1", "siteclass", "program_type", "county"):
            if not site.get(key) and row.get(key):
                site[key] = row[key]
        if str(row.get("contaminants") or "").strip():
            site["_contaminants"].add(str(row["contaminants"]).strip())
    return list(sites.values())


def features_from_rows(rows: list[dict]) -> tuple[list[dict], list[str]]:
    features, unplaced = [], 0
    sites = sites_from_rows(rows)
    for site in sites:
        number = str(site["program_number"]).strip()
        lon_lat = point(site.get("longitude"), site.get("latitude"))
        if not lon_lat:
            unplaced += 1
            continue
        code = str(site.get("program_type") or "").strip()
        program = PROGRAMS.get(code, f"program {code}" if code else "program not recorded")
        place = ", ".join(p for p in (str(site.get("address1") or "").strip(), COUNTIES.get(str(site.get("county") or "").strip(), "")) if p)
        listed = sorted(site["_contaminants"])
        more = len(listed) - MAX_CONTAMINANTS
        contaminants = "; ".join(listed[:MAX_CONTAMINANTS]) + (f"; and {more} more" if more > 0 else "")
        site_class = str(site.get("siteclass") or "").strip()
        meaning = SITE_CLASSES.get(site_class)
        parts = [
            f"{place or 'Address not recorded'}.",
            f"DEC site {number}" + (f", class {site_class}" + (f": {meaning}." if meaning else ".") if site_class else "."),
            f"Contaminants listed: {contaminants}." if contaminants else "No contaminants listed.",
        ]
        features.append(feature(
            INFO, number, point_geometry(lon_lat),
            hazard="contamination",
            severity=0,
            date=None,
            title=f"Remediation site: {program}",
            summary=" ".join(parts),
            bbl=None,
            record_id=number,
        ))
    return features, [n for n in [left_out(unplaced, len(sites), "sites", "no usable coordinates")] if n]


def pull(pulled_on: date | None = None) -> Pulled:
    # Grouping returns each distinct combination once, a fraction of the dataset's rows.
    rows, capped = source_rows.all_rows(
        DATASET, {"select": SELECT, "where": where(), "group": GROUP, "order": "program_number,contaminants"}, portal=PORTAL)
    features, notes = features_from_rows(rows)
    return Pulled(features, source_rows.rows_updated_at(DATASET, PORTAL), capped, notes)
