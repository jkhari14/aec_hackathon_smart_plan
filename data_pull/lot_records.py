"""The public record for one lot: seven NYC Open Data datasets, each reported honestly.

Each dataset comes back as one of three statuses, never blurred together:
- "ok": queried; `count` may be 0, which means "queried and none found";
- "error": the query failed, so nothing is known (never read this as zero);
- "skipped": not queried, with the reason (for example, no BIN to query by).
"""

from __future__ import annotations

from data_pull import soda_client

# key: (dataset id, display name, $select, $order)
DATASETS = {
    "pluto": (
        "64uk-42ks", "PLUTO (lot data)",
        "bbl,address,yearbuilt,numfloors,numbldgs,bldgclass,landuse,unitsres,lotfront,"
        "lotdepth,bldgarea,zonedist1,latitude,longitude,version",
        None,
    ),
    "dob_now_filings": (
        "w9ak-ipjd", "DOB NOW job filings",
        "job_filing_number,job_type,filing_status,filing_date,approved_date,first_permit_date,"
        "current_status_date,signoff_date,bin,bbl,house_no,street_name,job_description,"
        "earth_work_work_type_,foundation_work_type_,support_of_excavation_work_type_,"
        "structural_work_type_,full_demolition_work_type_,filing_review_type",
        "filing_date DESC",
    ),
    "dob_violations": (
        "3h2n-5cm9", "DOB violations",
        "isn_dob_bis_viol,boro,block,lot,bin,issue_date,violation_type,violation_category,"
        "violation_number,number,description,disposition_comments",
        "issue_date DESC",
    ),
    "ecb_violations": (
        "6bgk-3dad", "ECB violations",
        "ecb_violation_number,dob_violation_number,bin,issue_date,ecb_violation_status,"
        "violation_type,severity,section_law_description1,violation_description,"
        "infraction_code1,penality_imposed,balance_due,hearing_status,certification_status",
        "issue_date DESC",
    ),
    "dob_safety_violations": (
        "855j-jady", "DOB safety violations (newer civil-penalty set)",
        "violation_number,bbl,bin,violation_type,violation_status,violation_issue_date,"
        "violation_remarks,device_type",
        "violation_issue_date DESC",
    ),
    "hpd_violations": (
        "wvxf-dwi5", "HPD violations (housing agency)",
        "violationid,inspectiondate,novissueddate,class,violationstatus,currentstatus,"
        "currentstatusdate,novdescription,apartment,story",
        "inspectiondate DESC",
    ),
    "dob_complaints": (
        "eabe-havv", "DOB complaints",
        "complaint_number,bin,date_entered,complaint_category,status,disposition_date,"
        "disposition_code,inspection_date,unit",
        "complaint_number DESC",
    ),
}


def record_lot(record: dict) -> str | None:
    """The BBL a record states for itself, or None when it does not say."""
    bbl = str(record.get("bbl", "")).split(".")[0]
    if len(bbl) == 10 and bbl.isdigit():
        return bbl
    boro, block, lot = (str(record.get(k, "")) for k in ("boro", "block", "lot"))
    if boro.isdigit() and len(boro) == 1 and block.isdigit() and lot.isdigit():
        return f"{boro}{block.zfill(5)[-5:]}{lot.zfill(4)[-4:]}"
    return None


def _run(key: str, where: str, bbl: str) -> dict:
    dataset_id, _, select, order = DATASETS[key]
    params = {"select": select, "where": where}
    if order:
        params["order"] = order
    try:
        rows, url = soda_client.query(dataset_id, params)
    except soda_client.SodaQueryError as error:
        return {"status": "error", "error": str(error), "records": []}
    # A row reached through a BIN but stating a different lot is held back, not counted.
    placed = [row for row in rows if record_lot(row) in (None, bbl)]
    held_back = [row for row in rows if record_lot(row) not in (None, bbl)]
    return {
        "status": "ok",
        "count": len(placed),
        "truncated": len(rows) >= soda_client.ROW_LIMIT,
        "query_url": url,
        "records": placed,
        "held_back_other_lot": held_back,
    }


def _skipped(reason: str) -> dict:
    return {"status": "skipped", "reason": reason, "records": []}


def _block_lot_or_bins(bbl: str, bins: list[str]) -> str:
    boro, block, lot = soda_client.split_bbl(bbl)
    clause = (
        f"(boro='{boro}' AND block in {soda_client.soql_in(soda_client.block_variants(block))}"
        f" AND lot in {soda_client.soql_in(soda_client.lot_variants(lot))})"
    )
    return f"{clause} OR bin in {soda_client.soql_in(bins)}" if bins else clause


def pull_lot(bbl: str, seed_bins: list[str]) -> dict:
    """Every dataset for one lot. `seed_bins` are BINs already tied to this lot (from the
    address lookup and the footprints); DOB NOW filings on this BBL can add more."""
    soda_client.validate_bbl(bbl)
    bins = sorted({b for b in seed_bins if not soda_client.is_placeholder_bin(b)})
    datasets: dict[str, dict] = {}

    datasets["pluto"] = _run("pluto", f"bbl={bbl}", bbl)
    filings_where = f"bbl='{bbl}'" + (f" OR bin in {soda_client.soql_in(bins)}" if bins else "")
    datasets["dob_now_filings"] = _run("dob_now_filings", filings_where, bbl)
    # Only filings stating THIS lot may add a BIN: a BIN on another lot's filing is not evidence.
    for record in datasets["dob_now_filings"]["records"]:
        candidate = str(record.get("bin", ""))
        if record_lot(record) == bbl and candidate.isdigit() and len(candidate) == 7:
            if not soda_client.is_placeholder_bin(candidate):
                bins = sorted(set(bins) | {candidate})

    where_block_lot = _block_lot_or_bins(bbl, bins)
    datasets["dob_violations"] = _run("dob_violations", where_block_lot, bbl)
    datasets["ecb_violations"] = _run("ecb_violations", where_block_lot, bbl)
    safety_where = f"bbl='{bbl}'" + (f" OR bin in {soda_client.soql_in(bins)}" if bins else "")
    datasets["dob_safety_violations"] = _run("dob_safety_violations", safety_where, bbl)
    datasets["hpd_violations"] = _run("hpd_violations", f"bbl='{bbl}'", bbl)
    if bins:
        complaints_where = f"bin in {soda_client.soql_in(bins)}"
        datasets["dob_complaints"] = _run("dob_complaints", complaints_where, bbl)
    else:
        datasets["dob_complaints"] = _skipped("no BIN found for this lot; complaints join by BIN only")

    return {"bbl": bbl, "bins": bins, "datasets": datasets}
