import pytest
from hypothesis import given
from hypothesis_jsonschema import from_schema
from pydantic import ValidationError

from cpack import Manifest


@pytest.mark.fuzzing
@given(data=from_schema(Manifest.schema()))
def test_schema_fuzzing(data):
    for field in ("compilers", "dependencies", "sources", "types", "name", "metadata"):
        if field in data and not data[field]:
            # NOTE: Skip empty fields
            del data[field]

    try:
        manifest = Manifest.parse_obj(data)
    except (ValidationError, ValueError):
        pass
    assert manifest.dict() == data
