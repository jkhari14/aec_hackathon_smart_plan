"""The case library from data/cases/cases.json, checked against the Case contract; the labelled fixture until it lands."""

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import TypeAdapter

from api.contracts import Case
from api.routers.router_data import LoadedData, data_root, read_contract_file, served
from api.stubs import fixture

_CASES = TypeAdapter(list[Case])

cases_router = APIRouter(prefix="/api/cases")


def load_cases(root: Path) -> LoadedData:
    """The case library for a Python caller (the chat); a broken file is DataUnavailable, never an empty list."""
    path = root / "cases" / "cases.json"
    if not path.is_file():
        return LoadedData(_CASES.validate_python(fixture("cases")), True)
    return LoadedData(read_contract_file(path, _CASES, root), False)


def _one_case(case_id: str, root: Path) -> LoadedData:
    loaded = load_cases(root)
    for case in loaded.data:
        if case.id == case_id:
            return LoadedData(case, loaded.sample)
    raise HTTPException(404, f"no case {case_id!r}")


@cases_router.get("", response_model=list[Case])
def list_cases(response: Response, root: Path = Depends(data_root)):
    return served(response, load_cases, root)


@cases_router.get("/{case_id}", response_model=Case)
def get_case(case_id: str, response: Response, root: Path = Depends(data_root)):
    return served(response, _one_case, case_id, root)
