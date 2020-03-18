from ckanfunctionaltests.api import validate_against_schema


def test_organization_list(base_url, rsession):
    response = rsession.get(f"{base_url}/action/organization_list")
    assert response.status_code == 200
    validate_against_schema(response.json(), "organization_list.schema.json")

    assert response.json()["success"] is True


def test_organization_show_404(base_url, rsession):
    response = rsession.get(f"{base_url}/action/organization_show?id=number-three-group")
    assert response.status_code == 404

    assert response.json()["success"] is False


def test_organization_show(base_url, rsession, random_org_slug):
    response = rsession.get(f"{base_url}/action/organization_show?id={random_org_slug}")
    assert response.status_code == 200
    validate_against_schema(response.json(), "organization_show.schema.json")

    assert response.json()["success"] is True

