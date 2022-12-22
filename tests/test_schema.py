import pytest
from hypothesis import given
from hypothesis_jsonschema import from_schema
from pydantic import ValidationError

from cpack import Manifest, Source


def clean_data(data):
    for field in list(data.keys()):
        if field not in Manifest.__fields__:
            del data[field]

    if "sources" in data:
        for source in list(data["sources"]):
            if source and isinstance(data["sources"][source], dict):
                for key in list(data["sources"][source]):
                    if key not in Source.__fields__:
                        del data["sources"][source][key]

            if not source or not isinstance(data["sources"][source], dict):
                del data["sources"][source]

    if "compilers" in data:
        for compiler in list(data["compilers"]):
            if not data["compilers"][compiler]:
                del data["compilers"][compiler]
                continue

            else:
                for key in list(data["compilers"][compiler]):
                    if not data["compilers"][compiler][key]:
                        del data["compilers"][compiler][key]

    for field in ("compilers", "dependencies", "sources", "types", "name", "metadata"):
        if field in data and not data[field]:
            # NOTE: Skip empty fields
            del data[field]

    return data


@pytest.mark.fuzzing
@given(data=from_schema(Manifest.schema()))
def test_schema_fuzzing(data):
    data = clean_data(data)

    try:
        manifest = Manifest.parse_obj(data)
        assert manifest.dict() == data

    except (ValidationError, ValueError):
        pass
