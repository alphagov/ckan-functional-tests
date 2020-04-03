from ckanfunctionaltests.api import validate_against_schema


def test_csv(base_url, rsession, subtests):
    response = rsession.get(f"{base_url}/2/util/resource/format_autocomplete?incomplete=cs")
    assert response.status_code == 200
    rj = response.json()

    with subtests.test("response validity"):
        validate_against_schema(rj, "format_autocomplete")

    with subtests.test("expected result present"):
        assert any(result["Format"].lower().strip() == "csv" for result in rj["ResultSet"]["Result"])


def test_no_results(base_url, rsession, subtests):
    response = rsession.get(f"{base_url}/2/util/resource/format_autocomplete?incomplete=telegrams")
    assert response.status_code == 200
    rj = response.json()

    with subtests.test("response validity"):
        validate_against_schema(rj, "format_autocomplete")

    with subtests.test("no results"):
        assert rj["ResultSet"]["Result"] == []
