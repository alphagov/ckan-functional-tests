from ckanfunctionaltests.api import validate_against_schema
import requests

def test_organization_list(variables):
    response = requests.get(f"{variables['base_url']}/action/organization_list")
    assert response.status_code == 200
    validate_against_schema(response.json(), "organization_list.schema.json")

    assert response.json()["success"] is True
