import json
from warnings import warn

import pytest

from ckanfunctionaltests.api import validate_against_schema, extract_search_terms
from ckanfunctionaltests.api.comparisons import AnySupersetOf
from ckanfunctionaltests.api.conftest import clean_unstable_elements, get_dataset_search_json_response


def _get_limit_offset_params(base_url, variables={}):
    return ("rows", "start",) if base_url.endswith("/3") or variables.get("ckan_version") == "2.9"\
        else ("limit", "offset",)


def _validate_embedded_keys(response_json):
    for result in response_json["results"]:
        for key in ("data_dict", "validated_data_dict",):
            if key in result:
                # note this embedded json uses the "package" schema, despite being
                # in a "dataset".
                inner_package = json.loads(result[key])
                validate_against_schema(inner_package, "package_base")


def test_search_datasets_by_full_slug_general_term(
    subtests,
    inc_sync_sensitive,
    base_url_3,
    rsession,
    random_pkg_slug,
    variables
):
    limit_param, offset_param = _get_limit_offset_params(base_url_3, variables=variables)
    response = rsession.get(
        f"{base_url_3}/search/dataset?q={random_pkg_slug}&{limit_param}=100"
    )
    assert response.status_code == 200
    rj = get_dataset_search_json_response(response, base_url_3, variables)

    with subtests.test("response validity"):
        validate_against_schema(rj, "search_dataset")
        # check it's using the raw-string result format
        if variables.get('ckan_version') == "2.9":
            assert isinstance(rj["results"][0], dict)
        else:
            assert isinstance(rj["results"][0], str)
        assert len(rj["results"]) <= 100

    if inc_sync_sensitive:
        with subtests.test("desired result present"):
            results = [r["name"] for r in rj["results"]] if variables.get("ckan_version") == "2.9" else rj["results"]
            desired_result = tuple(
                name for name in results if name == random_pkg_slug
            )
            assert desired_result
            if len(desired_result) > 1:
                warn(f"Multiple results ({len(desired_result)}) with name = {random_pkg_slug!r})")


def test_search_datasets_by_full_slug_general_term_id_response(
    subtests,
    inc_sync_sensitive,
    base_url_3,
    rsession,
    random_pkg,
    variables
):
    limit_param, offset_param = _get_limit_offset_params(base_url_3, variables=variables)
    response = rsession.get(
        f"{base_url_3}/search/dataset?q={random_pkg['name']}&fl=id&{limit_param}=100"
    )
    assert response.status_code == 200
    rj = get_dataset_search_json_response(response, base_url_3, variables)

    with subtests.test("response validity"):
        validate_against_schema(rj, "search_dataset")

        if variables.get("ckan_version") == "2.9":
            # in CKAN 2.9, v1 dataset search has been dropped so results come back as v3
            assert isinstance(rj["results"][0], dict)
        else:
            # when "id" is chosen for the response, it is presented as raw strings
            assert isinstance(rj["results"][0], str)
        assert len(rj["results"]) <= 100

    if inc_sync_sensitive:
        with subtests.test("desired result present"):
            if variables.get("ckan_version") == "2.9":
                assert random_pkg["id"] in [r['id'] for r in rj["results"]]
            else:
                assert random_pkg["id"] in rj["results"]


def test_search_datasets_by_full_slug_general_term_revision_id_response(
    subtests,
    inc_sync_sensitive,
    base_url_3,
    rsession,
    random_pkg,
    variables
):
    if variables.get("ckan_version") == "2.9":
        pytest.skip("revision_id is not available in 2.9")

    limit_param, offset_param = _get_limit_offset_params(base_url_3)
    response = rsession.get(
        f"{base_url_3}/search/dataset?q={random_pkg['name']}&fl=revision_id&{limit_param}=100"
    )
    assert response.status_code == 200
    rj = response.json()

    with subtests.test("response validity"):
        validate_against_schema(rj, "search_dataset")
        # when "revision_id" is chosen for the response, it is presented object-wrapped items
        assert isinstance(rj["results"][0], dict)
        assert len(rj["results"]) <= 100

    if inc_sync_sensitive:
        with subtests.test("desired result present"):
            assert any(random_pkg["revision_id"] == dst["revision_id"] for dst in rj["results"])


@pytest.mark.parametrize("allfields_term", ("all_fields=1", "fl=*",))
def test_search_datasets_by_full_slug_specific_field_all_fields_response(
    subtests,
    inc_sync_sensitive,
    base_url_3,
    rsession,
    random_pkg,
    allfields_term,
    variables
):
    if allfields_term.startswith("all_fields") and base_url_3.endswith("/3"):
        pytest.skip("all_fields parameter not supported in v3 endpoint")

    limit_param, offset_param = _get_limit_offset_params(base_url_3, variables=variables)
    response = rsession.get(
        f"{base_url_3}/search/dataset?q=name:{random_pkg['name']}&{allfields_term}&{limit_param}=10"
    )
    assert response.status_code == 200
    rj = response.json()

    with subtests.test("response validity"):
        validate_against_schema(rj, "search_dataset")
        assert isinstance(rj["results"][0], dict)
        assert len(rj["results"]) <= 10

        _validate_embedded_keys(rj)

    if inc_sync_sensitive:
        with subtests.test("desired result present"):
            desired_result = tuple(
                dst for dst in rj["results"] if random_pkg["id"] == dst["id"]
            )
            assert len(desired_result) == 1

            assert desired_result[0]["title"] == random_pkg["title"]
            assert desired_result[0]["state"] == random_pkg["state"]
            assert desired_result[0]["organization"] == random_pkg["organization"]["name"]


def test_search_datasets_stable_package_by_title_general_term(
    subtests,
    base_url_3,
    rsession,
    stable_pkg,
    variables
):
    limit_param, offset_param = _get_limit_offset_params(base_url_3, variables=variables)
    name_terms = extract_search_terms(stable_pkg["name"], 3)
    response = rsession.get(
        f"{base_url_3}/search/dataset?q=name:{stable_pkg['name']}&fl=name&{limit_param}=100"
    )
    assert response.status_code == 200
    rj = get_dataset_search_json_response(response, base_url_3, variables=variables)

    with subtests.test("response validity"):
        validate_against_schema(rj, "search_dataset")
        if variables.get("ckan_version") == "2.9":
            # in CKAN 2.9, v1 dataset search has been dropped so results come back as v3
            assert isinstance(rj["results"][0], dict)
        else:
            # check it's using the raw-string result format
            assert isinstance(rj["results"][0], str)
        assert len(rj["results"]) <= 100

    with subtests.test("desired result present"):
        if variables.get("ckan_version") == "2.9":
            assert stable_pkg["name"] in [n['name'] for n in rj["results"]]
        else:
            assert stable_pkg["name"] in rj["results"]


@pytest.mark.parametrize("org_as_q", (False, True,))
def test_search_datasets_by_org_slug_specific_field_and_title_general_term(
    subtests,
    inc_sync_sensitive,
    base_url_3,
    rsession,
    stable_pkg,
    org_as_q,
    variables
):
    if base_url_3.endswith("/3") and not org_as_q:
        pytest.skip("field filtering as separate params not supported in v3 endpoint")

    limit_param, offset_param = _get_limit_offset_params(base_url_3, variables=variables)
    name_terms = "name:" + stable_pkg["name"]

    # it's possible to query specific fields in two different ways
    query_frag = f"q={name_terms}" + (
        f"+organization:{stable_pkg['organization']['name']}"
        if org_as_q else
        (
            f"&organization={stable_pkg['organization']['name']}" if variables.get("ckan_version") != "2.9" else 
            f"+organization:{stable_pkg['organization']['name']}"  # ckan 2.9 is stricter with search params
        )
    )
    response = rsession.get(
        f"{base_url_3}/search/dataset?{query_frag}"
        f"&fl=id,organization,title&{limit_param}=1000"
    )
    assert response.status_code == 200
    rj = get_dataset_search_json_response(response, base_url_3, variables=variables)

    with subtests.test("response validity"):
        validate_against_schema(rj, "search_dataset")
        assert isinstance(rj["results"][0], dict)
        assert len(rj["results"]) <= 1000

    with subtests.test("all results match criteria"):
        assert all(
            stable_pkg["organization"]["name"] == dst["organization"]
            for dst in rj["results"]
        )
        # we can't reliably test for the search terms because they may have been stemmed
        # and not correspond to exact matches

    if inc_sync_sensitive:
        with subtests.test("desired result present"):
            desired_result = tuple(
                dst for dst in rj["results"] if stable_pkg["id"] == dst["id"]
            )
            if rj["count"] > 1000 and not desired_result:
                # we don't have all results - it may well be on a latter page
                warn(f"Expected dataset id {stable_pkg['id']!r} not found on first page of results")
            else:
                assert len(desired_result) == 1
                assert desired_result[0]["title"] == stable_pkg["title"]


@pytest.mark.parametrize("allfields_term", ("all_fields=1", "fl=*",))
def test_search_datasets_by_full_slug_specific_field_all_fields_response(
    subtests,
    base_url_3,
    rsession,
    stable_dataset,
    allfields_term,
    variables
):
    if allfields_term.startswith("all_fields") and (base_url_3.endswith("/3") or variables.get('ckan_version') == '2.9'):
        pytest.skip("all_fields parameter not supported in v3 endpoint")

    limit_param, offset_param = _get_limit_offset_params(base_url_3, variables=variables)

    response = rsession.get(
        f"{base_url_3}/search/dataset?q=name:{stable_dataset['name']}"
        f"&{allfields_term}&{limit_param}=10"
    )
    assert response.status_code == 200
    rj = response.json().get('result') if variables.get('ckan_version') == '2.9' and base_url_3.endswith("/3")\
        else response.json()

    with subtests.test("response validity"):
        validate_against_schema(rj, "search_dataset")
        assert isinstance(rj["results"][0], dict)
        assert len(rj["results"]) <= 10

        _validate_embedded_keys(rj)

    desired_result = tuple(
        dst for dst in rj["results"] if stable_dataset["name"] == dst["name"]
    )
    assert len(desired_result) == 1

    with subtests.test("desired result equality"):
        clean_unstable_elements(stable_dataset, is_key_value=False)
        clean_unstable_elements(desired_result[0], is_key_value=False)
        assert desired_result[0] == AnySupersetOf(stable_dataset, recursive=True, seq_norm_order=True)
