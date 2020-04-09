from random import Random

import pytest
import requests


from ckanfunctionaltests.api import uuid_re


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
        name for name in response.json()["result"] if not uuid_re.fullmatch(name)
    )

    if not suitable_names:
        raise ValueError("No suitable package slugs found")

    return _random.choice(suitable_names)


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

    random_index = _random.randint(0, count_response.json()["result"]["count"])
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
