from functools import lru_cache
from glob import glob
import json
import os.path

from jsonschema.validators import RefResolver, validator_for


def _get_schema(schema_path: str) -> dict:
    with open(schema_path, "rb") as f:
        return json.load(f)


_schema_id_base = "http://github.com/alphagov/ckan-functional-tests/api/"
_schema_store = None


def _get_schema_store() -> dict:
    global _schema_store
    if _schema_store is None:
        _schema_store = {
            _schema_id_base + os.path.basename(
                ".".join(schema_path.split(".")[:-2])
            ): _get_schema(schema_path)
            for schema_path in glob(
                os.path.join(os.path.dirname(__file__), "schemas", "*.schema.json")
            )
        }
    return _schema_store


@lru_cache()
def get_validator(schema_name: str):
    store = _get_schema_store()
    schema = store[_schema_id_base + schema_name]
    return validator_for(schema)(schema, resolver=RefResolver("", schema, store))


def validate_against_schema(candidate, schema_name: str) -> None:
    get_validator(schema_name).validate(candidate)
