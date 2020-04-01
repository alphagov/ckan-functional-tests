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
