import json
import os.path

import jsonschema
import pytest

from ckanfunctionaltests.api import validate_against_schema, get_example_response


@pytest.mark.parametrize("response_filename,schema_name", (
    ("organization_list.json", "organization_list",),
    ("package_list.json", "package_list",),
    ("organization_show.json", "organization_show",),
    ("package_show.json", "package_show",),
    ("package_search.json", "package_search",),
    ("search_dataset.all_fields.json", "search_dataset",),
    ("search_dataset.rawids.json", "search_dataset",),
    ("search_dataset.rawslugs.json", "search_dataset",),
    ("search_dataset.titles.json", "search_dataset",),
    ("format_autocomplete.json", "format_autocomplete",),
    ("i18n.json", "i18n",),
))
def test_responses_pass_respective_schemas(response_filename, schema_name):
    validate_against_schema(get_example_response(response_filename), schema_name)


@pytest.mark.parametrize("nonslug_value", (
    123,
    "One fine morning in the month of May",
))
def test_package_list_must_be_slugs(nonslug_value):
    example_response = get_example_response("package_list.json")
    example_response["result"][2] = nonslug_value

    with pytest.raises(jsonschema.ValidationError):
        validate_against_schema(example_response, "package_list")


def test_package_show_org_must_follow_org_schema():
    example_response = get_example_response("package_show.json")

    # note non-existent leap-day
    example_response["result"]["organization"]["created"] = "2019-02-29T16:00:00.123Z"

    with pytest.raises(jsonschema.ValidationError):
        validate_against_schema(example_response, "package_show")


def test_organization_show_is_organization():
    example_response = get_example_response("organization_show.json")

    example_response["result"]["is_organization"] = False

    with pytest.raises(jsonschema.ValidationError):
        validate_against_schema(example_response, "organization_show")


@pytest.mark.parametrize("endpoint", (
    "organization_show",
    "package_show",
))
def test_missing_ids(endpoint):
    example_response = get_example_response(f"{endpoint}.json")

    del example_response["result"]["id"]

    with pytest.raises(jsonschema.ValidationError):
        validate_against_schema(example_response, endpoint)


@pytest.mark.parametrize("endpoint", (
    "organization_show",
    "package_show",
))
def test_unknown_state(endpoint):
    example_response = get_example_response(f"{endpoint}.json")

    example_response["result"]["state"] = "lockdown"

    with pytest.raises(jsonschema.ValidationError):
        validate_against_schema(example_response, endpoint)


@pytest.mark.parametrize("endpoint", (
    "organization_show",
    "organization_list",
    "package_show",
    "package_list",
    "package_search",
))
def test_missing_success(endpoint):
    example_response = get_example_response(f"{endpoint}.json")

    del example_response["success"]

    with pytest.raises(jsonschema.ValidationError):
        validate_against_schema(example_response, endpoint)


def test_package_search_noninteger_facet():
    example_response = get_example_response("package_search.json")

    example_response["result"]["facets"]["organization"]["natural-england"] = "2"

    with pytest.raises(jsonschema.ValidationError):
        validate_against_schema(example_response, "package_search")


def test_package_search_empty_tag():
    example_response = get_example_response("package_search.json")

    example_response["result"]["results"][2]["tags"].append({})

    with pytest.raises(jsonschema.ValidationError):
        validate_against_schema(example_response, "package_search")


def test_format_autocomplete_result_missing_format():
    example_response = get_example_response("format_autocomplete.json")

    del example_response["ResultSet"]["Result"][1]["Format"]

    with pytest.raises(jsonschema.ValidationError):
        validate_against_schema(example_response, "format_autocomplete")


def test_i18n_non_dict():
    with pytest.raises(jsonschema.ValidationError):
        validate_against_schema(3.1415, "i18n")
