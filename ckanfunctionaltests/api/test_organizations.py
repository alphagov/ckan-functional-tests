from ckanfunctionaltests.api import validate_against_schema


def test_organization_list(base_url, rsession):
    response = rsession.get(f"{base_url}/action/organization_list")
    assert response.status_code == 200
    validate_against_schema(response.json(), "organization_list.schema.json")

    assert response.json()["success"] is True
