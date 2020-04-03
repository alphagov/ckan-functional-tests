from ckanfunctionaltests.api import validate_against_schema


def test_organization_list(base_url_3, rsession):
    response = rsession.get(f"{base_url_3}/action/organization_list")
    assert response.status_code == 200
    validate_against_schema(response.json(), "organization_list")

    assert response.json()["success"] is True


def test_organization_show_404(base_url_3, rsession):
    response = rsession.get(f"{base_url_3}/action/organization_show?id=number-three-group")
    assert response.status_code == 404

    assert response.json()["success"] is False


def test_organization_show(subtests, base_url_3, rsession, random_org_slug):
    response = rsession.get(f"{base_url_3}/action/organization_show?id={random_org_slug}")
    assert response.status_code == 200
    rj = response.json()

    with subtests.test("response validity"):
        validate_against_schema(rj, "organization_show")

        assert rj["success"] is True
        assert rj["result"]["name"] == random_org_slug

    with subtests.test("uuid lookup consistency"):
        # we should be able to look up this same organization by its uuid and get an identical response
        uuid_response = rsession.get(f"{base_url_3}/action/organization_show?id={rj['result']['id']}")
        assert uuid_response.status_code == 200
        assert uuid_response.json() == rj
