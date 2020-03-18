from functools import lru_cache
import json
import os.path

import jsonschema


@lru_cache()
def get_schema(schema_name: str) -> dict:
    with open(os.path.join(os.path.dirname(__file__), "schemas", schema_name), "rb") as f:
        return json.load(f)

def validate_against_schema(candidate, schema_name: str) -> None:
    jsonschema.validate(candidate, schema=get_schema(schema_name))
