from functools import lru_cache
from glob import glob
import json
import os.path
import re

from jsonschema import draft7_format_checker
from jsonschema.validators import RefResolver, validator_for


uuid_re = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.I)


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


# grab a reference to the checker draft7_format_checker is using by default
_is_datetime, _is_datetime_raises = draft7_format_checker.checkers["date-time"]


# this could be considered monkeypatching, could perhaps use a deepcopy to mitigate that...
@draft7_format_checker.checks("date-time", raises=_is_datetime_raises)
def _lenient_is_datetime(instance):
    """
    A more lenient version of jsonschema's is_datetime checker needed because CKAN's
    timestamps aren't completely rfc3339 compliant. if a string first fails to validate
    alone, see if appending a "Z" allows it to pass
    """
    return _is_datetime(instance) or (
        isinstance(instance, str) and _is_datetime(instance + "Z")
    )


# jsonschema doesn't currently validate uuids
@draft7_format_checker.checks("uuid")
def _is_uuid(instance):
    return bool(isinstance(instance, str) and uuid_re.fullmatch(instance))


@lru_cache()
def get_validator(schema_name: str):
    store = _get_schema_store()
    schema = store[_schema_id_base + schema_name]
    return validator_for(schema)(
        schema,
        resolver=RefResolver("", schema, store),
        format_checker=draft7_format_checker,
    )


def validate_against_schema(candidate, schema_name: str) -> None:
    get_validator(schema_name).validate(candidate)


_all_alpha_re = re.compile(r"[a-z]+", re.I)


def extract_search_terms(source_text: str, n: int) -> str:
    """
    choose n longest "clean" words from the source_text as our search terms (longer words
    are more likely to be distinctive) and format them for use in a url
    """
    return "+".join(sorted(
        (token for token in source_text.split() if _all_alpha_re.fullmatch(token)),
        key=lambda t: len(t),
        reverse=True,
    )[:n])
