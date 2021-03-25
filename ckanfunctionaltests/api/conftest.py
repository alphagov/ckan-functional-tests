from collections.abc import Mapping, Sequence
from functools import wraps
import json
from random import Random

import pytest
import requests


from ckanfunctionaltests.api import get_example_response, uuid_re


# we will want to be able to seed this at some point
_random = Random()


@pytest.fixture()
def rsession(variables):
    with requests.Session() as session:
        session.headers = {"user-agent": variables["api_user_agent"]}
        yield session


@pytest.fixture()
def base_url(variables):
    return variables["api_base_url"]


@pytest.fixture(params=("", "/3"))
def base_url_3(request, base_url):
    "For endpoints published both under an /api and /api/3 endpoint"
    return base_url + request.param


def get_dataset_search_json_response(response, base_url_3, variables=None):
    return response.json().get('result') if variables.get('ckan_version') == '2.9' and base_url_3.endswith("/3")\
        else response.json()



@pytest.fixture()
def inc_sync_sensitive(variables):
    """
    A variable controlling whether to include tests that are sensitive to whether the target
    instance has consistent data across e.g. its database and search index
    """
    # we would normally use pytest.mark for this kind of thing, but it doesn't allow you to
    # mark & skip individual subtests
    return bool(variables.get("inc_sync_sensitive", True))


@pytest.fixture()
def inc_fixed_data(variables):
    """
    A variable controlling whether to include tests that use fixed data usually considered
    "stable" to compare with results from the target. you may want to skip these if e.g. your
    target instance is only filled with sparse demo data.
    """
    # again we would normally use pytest.mark for this kind of thing, but we may as well match
    # the mechanism used for inc_sync_sensitive
    if not bool(variables.get("inc_fixed_data", True)):
        # the thinking here is that only tests which use fixed data will be asking for this
        # value so we may as well do the skipping here.
        pytest.skip("Skipping fixed data test")
    return True


@pytest.fixture()
def random_org_slug(base_url, rsession):
    response = rsession.get(f"{base_url}/action/organization_list")
    assert response.status_code == 200
    return _random.choice(response.json()["result"])


@pytest.fixture()
def random_pkg_slug(base_url, rsession):
    # make do with one of the first 200 because the full list is big & slow
    response = rsession.get(f"{base_url}/action/package_list?limit=200")
    assert response.status_code == 200

    suitable_names = tuple(
        name for name in response.json()["result"] if not uuid_re.fullmatch(name) and not 'harvest' in name
    )

    if not suitable_names:
        raise ValueError("No suitable package slugs found")

    return _random.choice(suitable_names)


@pytest.fixture()
def stable_pkg_slug():
    return "example-dataset-number-one"


@pytest.fixture()
def random_pkg(base_url, rsession, random_pkg_slug):
    response = rsession.get(f"{base_url}/action/package_show?id={random_pkg_slug}")
    assert response.status_code == 200

    return response.json()["result"]


@pytest.fixture()
def random_harvestobject_id(base_url, rsession):
    # in this initial request, we only care about the count so we know the range in which
    # to make our random selection from
    count_response = rsession.get(f"{base_url}/action/package_search?q=harvest_object_id:*&rows=1")
    assert count_response.status_code == 200

    random_index = _random.randint(0, count_response.json()["result"]["count"] - 1)
    detail_response = rsession.get(
        f"{base_url}/action/package_search?q=harvest_object_id:*&rows=1&start={random_index}"
    )
    assert detail_response.status_code == 200

    # find the harvest_object_id
    return next((
        kv["value"]
        for kv in detail_response.json()["result"]["results"][0]["extras"]
        if kv["key"] == "harvest_object_id"
    ))


_unstable_keys = frozenset((
    "_version_",
    "created",
    "creator_user_id",
    "data_dict",
    "harvest_source_reference",
    "id",
    "import_source",
    "indexed_ts",
    "metadata_created",
    "metadata_modified",
    "owner_org",
    "package_count",
    "package_id",
    "revision_id",
    "validated_data_dict",
    "index_id",
    "site_id",
    "harvest_object_id",
    "harvest_source_id"
))


def _strip_unstable_data(obj):
    if isinstance(obj, Mapping):
        return {
            k: _strip_unstable_data(v)
            for k, v in obj.items()
            if k not in _unstable_keys
        }
    elif isinstance(obj, Sequence) and not isinstance(obj, str):
        return [
            _strip_unstable_data(element) for element in obj
            if not (
                isinstance(element, Mapping)
                and element.keys() == {"key", "value"}
                and element["key"] in _unstable_keys
            )
        ]
    else:
        return obj


# this function sets the value of the key to a specified value from ckan-vars.conf
# some tests expects the ID from the file to match a value from a request
# staging and production have the same IDs as there is a data sync but data generated 
# on a dev stack does not have the same ID, so put in the expected ID in the ckan-vars.conf
# to substitute the value in the expected response file.
def set_ckan_vars(json_data):
    ckan_vars = {}
    with open(f"ckan-vars.conf") as ckan_vars_file:
        for line in ckan_vars_file:
            name, val = line.partition("=")[::2]
            ckan_vars[name.strip()] = val.strip()

    str_data = json.dumps(json_data)

    for key in ckan_vars:
        str_data = str_data.replace(f'<<{key}>>', ckan_vars[key])
    
    return json.loads(str_data)


_key_value_keys = ['harvest', 'extras']


# to use this decorator you will need to add in the variables fixture to access the ckan_version:
#
# @update_for_ckan_version
# def test(variables):
#   return some_dataset_json
def update_for_ckan_version(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        data = f(*args, **kwargs)

        if kwargs.get('variables').get('ckan_version') == "2.9":
            # revisions have been removed from 2.9  
            data = remove_element(data, ['revision_id'])

            # introduction of metadata modified in resources list
            for key in data.keys():
                if key == 'resources':
                    for item in data[key]:
                        item['metadata_modified'] = None

        return data
    return decorated


def remove_element(in_data, removed_elements=[]):
    data = {}
    for key in in_data.keys():
        if key not in removed_elements:
            if isinstance(in_data[key], list):
                data[key] = []
                for item in in_data[key]:
                    data[key].append(remove_element(item, removed_elements))
            elif isinstance(in_data[key], dict):
                data[key] = remove_element(in_data[key], removed_elements)
            else:
                data[key] = in_data[key]
    return data


# rather than remove unstable elements from a response, this function cleans the unstable elements
# so that the values are identical to the expected values in the expected response files.
# it uses the _unstable_keys as a guide to which elements it should clean and it is possible to pass in 
# other key value args to:
# parent - used to determine whether the element is at root level where the id key is used to identify a package
# is_key_value - some packages do not have key_value pairs, so process those differently
def clean_unstable_elements(json_data, parent=None, is_key_value=True):
    if isinstance(json_data, str):
        return
    for key in json_data.keys():
        if key in _key_value_keys:
            if is_key_value:
                for item in json_data[key]:
                    item_key = item["key"]
                    item["value"] = f"<<{item_key}-value>>"
            else:
                json_data[key] = f"<<{key}>>"
        elif isinstance(json_data[key], list):
            for item in json_data[key]:
                clean_unstable_elements(item, key)
        elif isinstance(json_data[key], dict):
            clean_unstable_elements(json_data[key], key)
        elif key in _unstable_keys and not str(json_data[key]).startswith("<<"):
            if not (key == "id" and not parent):
                json_data[key] = f"<<{key}>>"
    return json_data


@pytest.fixture()
@update_for_ckan_version
def stable_pkg(variables, inc_fixed_data):
    json_data = get_example_response(
        "stable/package_show.inner.test.json"
    )
    return set_ckan_vars(json_data)


@pytest.fixture()
@update_for_ckan_version
def stable_pkg_search(variables, inc_fixed_data):
    return set_ckan_vars(
        clean_unstable_elements(
            get_example_response("stable/package_search.inner.test.json")
        )
    )


@pytest.fixture()
@update_for_ckan_version
def stable_pkg_default_schema(variables, inc_fixed_data):
    json_data = get_example_response(
        "stable/package_show.default_schema.inner.test.json"
    )

    return set_ckan_vars(json_data)


@pytest.fixture()
def stable_org(inc_fixed_data):
    return _strip_unstable_data(
        clean_unstable_elements(
            get_example_response(
                "stable/organization_show.inner.test.json"
            )
        )
    )


@pytest.fixture()
@update_for_ckan_version
def stable_org_with_datasets(variables, inc_fixed_data):
    return set_ckan_vars(get_example_response(
        "stable/organization_show_with_datasets.inner.test.json"
    ))


@pytest.fixture()
def stable_dataset(variables, inc_fixed_data):
    return set_ckan_vars(
        get_example_response(
        "stable/search_dataset{}.inner.test.json".format('-2.9' if variables['ckan_version'] == '2.9' else '')
        )
    )
