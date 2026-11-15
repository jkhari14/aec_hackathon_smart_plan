"""The site as the app's own routes serve it: each part is read through the function its route uses,
so the chat and the page cannot disagree about what is on record.

While a part is still the labelled sample (its owner's module has not landed), it describes the sample
site only. For any other lot that part is "not available": sample data is never shown as another site's.
A part that fails to load is a failure with its reason, never an empty list.
"""

from typing import Any, Optional

from pydantic import BaseModel

from api.routers.chat.chat_fixture_context import datasets_from_profile, similar_entries
from api.routers.chat.chat_site_context import Loaded, SiteContext, SiteContextUnavailable
from api.routers.layers_router import load_layer_catalog
from api.routers.router_data import DataUnavailable, data_root
from api.routers.sites_router import load_site_part
from api.stubs import fixture

SAMPLE_OF_ANOTHER_SITE = "only sample data is available, and it describes another site"


def _plain(value: Any) -> Any:
    """Contract models as the plain dicts and lists the chat reads."""
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, list):
        return [_plain(entry) for entry in value]
    return value


def app_context(bbl: str, job_type: Optional[str], stage: Optional[str], as_of: Optional[str]) -> SiteContext:
    """Raises SiteContextUnavailable when the site's profile cannot be had, and fastapi.HTTPException(422)
    for a lot or an option the site routes refuse."""
    is_sample_site = bbl == str(fixture("site_profile").get("bbl"))
    used_sample = False

    def part(name: str, **options: Optional[str]) -> Loaded:
        nonlocal used_sample
        try:
            loaded = load_site_part(name, bbl, **options)
        except DataUnavailable as error:
            return Loaded.failed(str(error))
        if loaded.sample and not is_sample_site:
            return Loaded.not_available(SAMPLE_OF_ANOTHER_SITE)
        used_sample = used_sample or loaded.sample
        return Loaded.ok(_plain(loaded.data))

    profile = part("profile", job_type=job_type, stage=stage, as_of=as_of)
    if profile.status != "ok":
        raise SiteContextUnavailable(profile.reason or "the site profile could not be loaded")
    try:
        layers = Loaded.ok(_plain(load_layer_catalog(data_root()).data))
    except DataUnavailable as error:
        layers = Loaded.failed(str(error))
    return SiteContext(
        bbl=bbl, as_of=as_of, profile=profile, records=[], datasets=datasets_from_profile(profile.value, bbl),
        similar=similar_entries(part("similar")), warnings=part("warnings", as_of=as_of),
        actions=part("actions", stage=stage), layers=layers, sample=used_sample)
