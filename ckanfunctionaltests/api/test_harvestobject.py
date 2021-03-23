from urllib.parse import urlparse
from xml.etree.ElementTree import fromstring


import pytest


def test_harvestobject_xml(variables, inc_sync_sensitive, base_url, rsession, random_harvestobject_id):
    if not inc_sync_sensitive:
        pytest.skip("it's possible for some harvest objects to be missing")

    rsession.auth = (variables['username'], variables['password'])
    response = rsession.get(f"{base_url}/2/rest/harvestobject/{random_harvestobject_id}/xml")
    assert response.status_code == 200

    # no, these are not all xml - why would you think that?
    content_type = response.headers["content-type"].split(";")[0].strip()
    if content_type == "application/json":
        # check this parses
        response.json()
    elif content_type == "application/xml":
        # simply check well-formedness
        fromstring(response.text)


def test_harvestobject_html(inc_sync_sensitive, base_url, rsession, random_harvestobject_id):
    if not inc_sync_sensitive:
        pytest.skip("it's possible for some harvest objects to be missing")

    response = rsession.get(
        f"{base_url}/2/rest/harvestobject/{random_harvestobject_id}/html",
        allow_redirects=False,
    )
    assert response.status_code in [301, 302]
    assert urlparse(response.headers["location"]).path == \
        f"/harvest/object/{random_harvestobject_id}/html"
