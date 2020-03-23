from dmtestutils.comparisons import AnySupersetOf

from ckanfunctionaltests.api import validate_against_schema


def test_package_list(base_url, rsession):
    response = rsession.get(f"{base_url}/action/package_list")
    assert response.status_code == 200
    validate_against_schema(response.json(), "package_list.schema.json")

    assert response.json()["success"] is True


def test_package_show_404(base_url, rsession):
    response = rsession.get(f"{base_url}/action/package_show?id=plates-knives-and-forks")
    assert response.status_code == 404

    assert response.json()["success"] is False


def test_package_show(subtests, base_url, rsession, random_pkg_slug):
    response = rsession.get(f"{base_url}/action/package_show?id={random_pkg_slug}")
    assert response.status_code == 200
    rj = response.json()

    with subtests.test("response validity"):
        validate_against_schema(rj, "package_show.schema.json")
        assert rj["success"] is True
        assert rj["result"]["name"] == random_pkg_slug
        assert all(res["package_id"] == rj['result']['id'] for res in rj["result"]["resources"])

    with subtests.test("uuid lookup consistency"):
        # we should be able to look up this same package by its uuid and get an identical response
        uuid_response = rsession.get(f"{base_url}/action/package_show?id={rj['result']['id']}")
        assert uuid_response.status_code == 200
        assert uuid_response.json() == rj

    with subtests.test("organization consistency"):
        org_response = rsession.get(
            f"{base_url}/action/organization_show?id={rj['result']['organization']['id']}"
        )
        assert org_response.status_code == 200
        assert org_response.json()["result"] == AnySupersetOf(rj['result']['organization'])
