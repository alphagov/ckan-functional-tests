from ckanfunctionaltests.api import validate_against_schema


def test_i18n(base_url, rsession, subtests):
    response = rsession.get(f"{base_url}/i18n/en_GB")
    assert response.status_code == 200
    rj = response.json()

    with subtests.test("response validity"):
        validate_against_schema(rj, "i18n")
