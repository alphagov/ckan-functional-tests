from itertools import count

import pytest


@pytest.mark.parametrize("endpoint_path", (
    "/action/package_list?",
    "/action/organization_list?",
    # currently too slow to work
    #"/action/harvest_source_list?",
))
def test_list_paging_equivalence(subtests, base_url_3, rsession, endpoint_path):
    full_response = rsession.get(f"{base_url_3}{endpoint_path}")
    assert full_response.status_code == 200
    assert full_response.json()["success"] is True

    accumulated_results = []
    for log_limit in count():
        # increasing the page size exponentially should allow us to perform meaningful
        # tests for both heavily populated and sparsely populated instances
        limit = int(10 ** log_limit)
        response = rsession.get(
            f"{base_url_3}{endpoint_path}&limit={limit}&offset={len(accumulated_results)}"
        )
        assert response.status_code == 200
        rj = response.json()
        assert rj["success"] is True

        assert 0 < len(rj["result"]) <= limit

        if len(rj["result"]) < limit:
            # this will have been the final request: performing the last request again with
            # no limit should return an equal result
            with subtests.test("offset no limit"):
                response_no_lim = rsession.get(
                    f"{base_url_3}{endpoint_path}&offset={len(accumulated_results)}"
                )
                assert response_no_lim.status_code == 200
                assert rj == response_no_lim.json()

        accumulated_results += rj["result"]

        if len(rj["result"]) < limit:
            # we've requested more results than exist
            break

    with subtests.test("accumulated results equal"):
        assert accumulated_results == full_response.json()["result"]

    with subtests.test("no results past end"):
        overrun_response = rsession.get(
            f"{base_url_3}{endpoint_path}&limit={limit}&offset={len(accumulated_results)+10}"
        )
        assert overrun_response.status_code == 200
        assert overrun_response.json()["success"] is True
        assert overrun_response.json()["result"] == []


@pytest.mark.parametrize("endpoint_path,results_getter,count_getter,limit_param,offset_param", (
    (
        "/action/package_search?q=data",
        lambda r: r["result"]["results"],
        lambda r: r["result"]["count"],
        "rows",
        "start",
    ),
    (
        "/3/action/package_search?q=data",
        lambda r: r["result"]["results"],
        lambda r: r["result"]["count"],
        "rows",
        "start",
    ),
    (
        "/search/dataset?q=data",
        lambda r: r["results"],
        lambda r: r["count"],
        "limit",
        "offset",
    ),
    (
        "/3/search/dataset?q=data",
        lambda r: r["results"],
        lambda r: r["count"],
        "rows",
        "start",
    ),
))
def test_search_paging_equivalence(
    subtests,
    base_url,
    rsession,
    endpoint_path,
    results_getter,
    count_getter,
    limit_param,
    offset_param,
):
    # in these tests the "full" response is actually also limited to the approx
    # max size the endpoints will tend to allow
    full_response_limit = 1000
    full_response = rsession.get(f"{base_url}{endpoint_path}&{limit_param}={full_response_limit}")
    assert full_response.status_code == 200

    frj = full_response.json()
    full_response_complete = count_getter(frj) <= full_response_limit
    if not full_response_complete:
        assert len(results_getter(frj)) == full_response_limit

    accumulated_results = []
    for log_limit in count():
        # increasing the page size exponentially should allow us to perform meaningful
        # tests for both heavily populated and sparsely populated instances
        limit = int(10 ** log_limit)
        response = rsession.get(
            f"{base_url}{endpoint_path}&{limit_param}={limit}&{offset_param}={len(accumulated_results)}"
        )
        assert response.status_code == 200
        rj = response.json()

        assert 0 < len(results_getter(rj)) <= limit

        accumulated_results += results_getter(rj)

        if len(accumulated_results) >= len(results_getter(frj)):
            if len(accumulated_results) > len(results_getter(frj)):
                # this should only have been possible if we didn't actually have the
                # complete results in full_response
                assert not full_response_complete
                # trim to full_response_limit
                accumulated_results = accumulated_results[:full_response_limit]

            break

    with subtests.test("accumulated results equal"):
        assert accumulated_results == results_getter(frj)

    with subtests.test("no results past end"):
        overrun_response = rsession.get(
            f"{base_url}{endpoint_path}&{limit_param}=10&{offset_param}={count_getter(frj)+10}"
        )
        assert overrun_response.status_code == 200
        assert results_getter(overrun_response.json()) == []
