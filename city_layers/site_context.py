"""What the citywide sources say about one point or lot: flood zone, Sandy, soil, E-designation, weather.

    python3 -m city_layers.site_context 40.638718 -73.953869 --bbl 3052110073

The layers in data/layers/ are simplified for the map. These functions ask each source directly,
at full detail, for the site profile. Every answer is a dict with a `status`, as in data_pull:

    "ok"       asked and answered; a `value` of None means the source has nothing there
    "error"    the query failed, so nothing is known (never read this as "none")
    "skipped"  not asked, with the `reason`
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import date

from city_layers import arcgis_rows, e_designations, fema_flood_zones, sandy_inundation
from city_layers.layer_file import LayerPullError, iso_date, point
from data_pull import soda_client

SOIL_URL = "https://sdmdataaccess.sc.egov.usda.gov/Tabular/post.rest"
WEATHER_URL = "https://archive-api.open-meteo.com/v1/archive"
BEDROCK_TILES = "https://tiledimageservices.arcgis.com/v01gqwM5QqNysAAi/arcgis/rest/services/DTB_NewYorkCity/ImageServer"
# The early-warning rules call a day with more rain than this a heavy-rain day (BUILD.md, PR 7).
HEAVY_RAIN_MM = 25.0
_TIMEOUT_SECONDS = 60


def _site(lon: object, lat: object) -> tuple[float, float]:
    lon_lat = point(lon, lat)
    if lon_lat is None:
        raise ValueError(f"not a point in New York City: lon {lon!r}, lat {lat!r}")
    return lon_lat


def _answer(key: str, name: str, url: str, value=None, **detail) -> dict:
    return {"key": key, "name": name, "status": "ok", "value": value, "detail": detail, "source_url": url}


def _failed(key: str, name: str, url: str, error: Exception) -> dict:
    return {"key": key, "name": name, "status": "error", "value": None, "reason": str(error), "source_url": url}


def _skipped(key: str, name: str, url: str, reason: str) -> dict:
    return {"key": key, "name": name, "status": "skipped", "value": None, "reason": reason, "source_url": url}


def _get_json(url: str, body: bytes | None = None) -> dict:
    request = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"} if body else {})
    try:
        with urllib.request.urlopen(request, timeout=_TIMEOUT_SECONDS) as response:
            answer = json.load(response)
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as error:
        raise LayerPullError(f"{url.split('?')[0]}: {type(error).__name__}: {error}") from error
    if not isinstance(answer, dict):
        raise LayerPullError(f"{url.split('?')[0]}: the answer was not an object")
    return answer


def fema_zone(lon: float, lat: float) -> dict:
    """The zone on FEMA's effective flood map at the point; value None when the map has no zone there."""
    key, name, url = "fema_flood_zone", "FEMA National Flood Hazard Layer", fema_flood_zones.LAYER_URL
    lon, lat = _site(lon, lat)
    try:
        found = arcgis_rows.attributes_at(url, lon, lat, "FLD_ZONE,ZONE_SUBTY,SFHA_TF,STATIC_BFE")
    except LayerPullError as error:
        return _failed(key, name, url, error)
    if not found:
        return _answer(key, name, url)
    zone = found[0]
    elevation = zone.get("STATIC_BFE")
    return _answer(
        key, name, url, value=str(zone.get("FLD_ZONE") or "").strip() or None,
        subtype=str(zone.get("ZONE_SUBTY") or "").strip() or None,
        special_flood_hazard_area=zone.get("SFHA_TF") == "T",
        # -9999 is FEMA's "none"; it is never passed on as a number.
        base_flood_elevation_ft=elevation if isinstance(elevation, (int, float)) and elevation > fema_flood_zones.NO_ELEVATION else None,
    )


def sandy_flooded(lon: float, lat: float) -> dict:
    """True when the point is inside the surveyed Sandy inundation zone, asked of the full-detail polygons."""
    key, name = "sandy_inundation", "Sandy Inundation Zone"
    url = f"https://data.cityofnewyork.us/d/{sandy_inundation.DATASET}"
    lon, lat = _site(lon, lat)
    try:
        rows, _ = soda_client.query(sandy_inundation.DATASET, {
            "select": "count(*) as n", "where": f"intersects(the_geom, 'POINT ({lon:.6f} {lat:.6f})')"})
        return _answer(key, name, url, value=int(rows[0]["n"]) > 0)
    except (soda_client.SodaQueryError, LookupError, TypeError, ValueError) as error:
        return _failed(key, name, url, error)


def e_designation(bbl: str) -> dict:
    """Every E-designation on the lot (hazardous materials, air quality and noise); value None when there is none."""
    key, name = "e_designations", "E-Designations"
    url = f"https://data.cityofnewyork.us/d/{e_designations.DATASET}"
    soda_client.validate_bbl(bbl)
    try:
        rows, _ = soda_client.query(e_designations.DATASET, {
            "select": "enumber,effective_date,hazmat_code,air_code,noise_code,description",
            "where": f"bbl={bbl}", "order": "effective_date"})
    except soda_client.SodaQueryError as error:
        return _failed(key, name, url, error)
    found = []
    for row in rows:
        covers = [label for label, flag in (("hazardous materials", "hazmat_code"), ("air quality", "air_code"),
                                            ("noise", "noise_code")) if row.get(flag) is True]
        found.append({"number": row.get("enumber"), "effective": iso_date(row.get("effective_date")), "covers": covers,
                      "as_recorded": row.get("description")})
    value = "; ".join(f"{d['number']}: {', '.join(d['covers']) or 'type not recorded'}" for d in found) or None
    return _answer(key, name, url, value=value, designations=found)


def soil_unit(lon: float, lat: float) -> dict:
    """The USDA soil survey map unit at the point. A survey unit, not a boring: it says nothing of one lot's fill."""
    key, name = "soil_map_unit", "USDA Soil Survey (Soil Data Access)"
    lon, lat = _site(lon, lat)
    sql = ("SELECT mu.mukey, mu.musym, mu.muname FROM mapunit mu INNER JOIN "
           f"SDA_Get_Mukey_from_intersection_with_WktWgs84('point({lon:.6f} {lat:.6f})') k ON mu.mukey = k.mukey")
    try:
        table = _get_json(SOIL_URL, json.dumps({"format": "JSON+COLUMNNAME", "query": sql}).encode()).get("Table") or []
    except LayerPullError as error:
        return _failed(key, name, SOIL_URL, error)
    if len(table) < 2:
        return _answer(key, name, SOIL_URL)
    unit = dict(zip(table[0], table[1]))
    return _answer(key, name, SOIL_URL, value=unit.get("muname"), map_unit_key=unit.get("mukey"), symbol=unit.get("musym"))


def weather(lon: float, lat: float, start: date, end: date) -> dict:
    """Daily rain and temperatures for the dates, with the heavy-rain and freeze-thaw days picked out.

    Open-Meteo answers for a grid cell a few km across (its centre is in `detail`), from a weather
    model, not a gauge on the site. Its free service is for non-commercial use.
    """
    key, name = "weather", "Open-Meteo historical weather"
    lon, lat = _site(lon, lat)
    query = urllib.parse.urlencode({
        "latitude": lat, "longitude": lon, "start_date": start.isoformat(), "end_date": end.isoformat(),
        "daily": "precipitation_sum,temperature_2m_max,temperature_2m_min", "timezone": "America/New_York"})
    try:
        answer = _get_json(f"{WEATHER_URL}?{query}")
        daily = answer["daily"]
        days = [{"date": d, "rain_mm": rain, "max_c": high, "min_c": low} for d, rain, high, low in zip(
            daily["time"], daily["precipitation_sum"], daily["temperature_2m_max"], daily["temperature_2m_min"])]
    except (LayerPullError, LookupError, TypeError) as error:
        return _failed(key, name, WEATHER_URL, error)
    heavy = [d["date"] for d in days if d["rain_mm"] is not None and d["rain_mm"] > HEAVY_RAIN_MM]
    # A freeze-thaw day went below freezing and back above it.
    freeze_thaw = [d["date"] for d in days if None not in (d["min_c"], d["max_c"]) and d["min_c"] < 0 < d["max_c"]]
    return _answer(key, name, WEATHER_URL, value=days, heavy_rain_days=heavy, freeze_thaw_days=freeze_thaw,
                   heavy_rain_mm=HEAVY_RAIN_MM, grid_cell={"lat": answer.get("latitude"), "lon": answer.get("longitude")})


def bedrock_depth(lon: float, lat: float) -> dict:
    """Not read yet: USGS publishes depth to bedrock as map tiles only, with no point lookup."""
    return _skipped("bedrock_depth", "USGS depth to bedrock, New York City", BEDROCK_TILES,
                    "USGS serves this raster as tiles only (depth in feet, about 30 m cells); reading a point "
                    "needs the raster download and a raster library, which is not in the build yet")


def stormwater_flood(lon: float, lat: float) -> dict:
    """Not read yet: the city's stormwater flood maps are a zip of GIS files, not a queryable dataset."""
    return _skipped("stormwater_flood", "NYC Stormwater Flood Maps", "https://data.cityofnewyork.us/d/9i7c-xyvv",
                    "published as a 34 MB zip of GIS files and as map tiles, with no point lookup")


def site_context(lon: float, lat: float, bbl: str | None = None) -> dict:
    """Every answer for one site, shaped for `SiteProfile`: its flood, soil and E-designation fields, and
    one entry per source for its `datasets` list (an error stays an error there, never a blank)."""
    samples = [fema_zone(lon, lat), sandy_flooded(lon, lat), stormwater_flood(lon, lat), soil_unit(lon, lat),
               bedrock_depth(lon, lat),
               e_designation(bbl) if bbl else _skipped("e_designations", "E-Designations",
                                                       f"https://data.cityofnewyork.us/d/{e_designations.DATASET}", "no BBL given")]
    by_key = {sample["key"]: sample for sample in samples}
    return {
        "flood": {"fema_zone": by_key["fema_flood_zone"]["value"], "stormwater": None,
                  "sandy_inundation": by_key["sandy_inundation"]["value"]},
        "soil": by_key["soil_map_unit"]["value"],
        "bedrock_depth_ft": None,
        "e_designation": by_key["e_designations"]["value"],
        "samples": samples,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("lat", type=float)
    parser.add_argument("lon", type=float)
    parser.add_argument("--bbl")
    args = parser.parse_args()
    print(json.dumps(site_context(args.lon, args.lat, args.bbl), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
