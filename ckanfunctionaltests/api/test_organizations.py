from warnings import warn


from dmtestutils.comparisons import AnySupersetOf


from ckanfunctionaltests.api import validate_against_schema


def test_organization_list(base_url_3, rsession):
    response = rsession.get(f"{base_url_3}/action/organization_list")
    assert response.status_code == 200
    rj = response.json()
    validate_against_schema(rj, "organization_list")

    assert rj["success"] is True
    # assert this is the correct variant of the response
    assert isinstance(rj["result"][0], str)


def test_organization_list_all_fields(subtests, base_url_3, rsession):
    response = rsession.get(f"{base_url_3}/action/organization_list?all_fields=1&limit=5")
    assert response.status_code == 200
    rj = response.json()

    with subtests.test("response validity"):
        validate_against_schema(rj, "organization_list")
        assert rj["success"] is True
        # assert this is the correct variant of the response schema
        assert isinstance(rj["result"][0], dict)

    with subtests.test("consistency with organization_show"):
        os_response = rsession.get(f"{base_url_3}/action/organization_show?id={rj['result'][0]['id']}")
        assert os_response.status_code == 200

        assert os_response.json()["result"] == AnySupersetOf(rj['result'][0])


def test_organization_list_all_fields_inc_optional(subtests, base_url_3, rsession):
    response = rsession.get(
        f"{base_url_3}/action/organization_list?all_fields=1&include_extras=1&include_tags=1"
        "&include_groups=1&limit=5"
    )
    assert response.status_code == 200
    rj = response.json()

    with subtests.test("response validity"):
        validate_against_schema(rj, "organization_list")
        assert rj["success"] is True
        # assert this is the correct variant of the response schema
        assert isinstance(rj["result"][0], dict)
        assert "extras" in rj["result"][0]
        assert "tags" in rj["result"][0]
        assert "groups" in rj["result"][0]

    with subtests.test("consistency with organization_show"):
        os_response = rsession.get(f"{base_url_3}/action/organization_show?id={rj['result'][0]['id']}")
        assert os_response.status_code == 200

        assert os_response.json()["result"] == AnySupersetOf(rj['result'][0])


def test_organization_list_all_fields_inc_users_no_effect(subtests, base_url_3, rsession):
    incusers_response = rsession.get(
        f"{base_url_3}/action/organization_list?all_fields=1&include_users=1&limit=5"
    )
    assert incusers_response.status_code == 200

    excusers_response = rsession.get(
        f"{base_url_3}/action/organization_list?all_fields=1&include_users=0&limit=5"
    )
    assert excusers_response.status_code == 200

    assert incusers_response.json() == excusers_response.json()


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


def test_organization_show_inc_datasets(subtests, base_url_3, rsession, random_pkg):
    response = rsession.get(
        f"{base_url_3}/action/organization_show?id={random_pkg['owner_org']}&include_datasets=1"
    )
    assert response.status_code == 200
    rj = response.json()

    with subtests.test("response validity"):
        validate_against_schema(rj, "organization_show")

    desired_result = tuple(
        pkg for pkg in rj["result"]["packages"] if pkg["id"] == random_pkg["id"]
    )
    if rj["result"]["package_count"] > 1000 and not desired_result:
        # this view only shows the first 1000 packages - it may have missed the cut
        warn(f"Expected package id {random_pkg['id']!r} not found in first 1000 listed packages")
    else:
        assert len(desired_result) == 1
