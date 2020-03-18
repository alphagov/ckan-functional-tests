import requests

def test_organization_list(variables):
    response = requests.get(f"{variables['base_url']}/action/organization_list")
    assert response.status_code == 200
    assert response.json()["success"] is True
