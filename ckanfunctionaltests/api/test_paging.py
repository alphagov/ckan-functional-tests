from itertools import count

import pytest


@pytest.mark.parametrize("endpoint_path", (
    "/action/package_list?",
    "/action/organization_list?",
    # currently too slow to work
    #"/action/harvest_source_list?",
))
def test_paging_equivalence(subtests, base_url, rsession, endpoint_path):
    full_response = rsession.get(f"{base_url}{endpoint_path}")
    assert full_response.status_code == 200
    assert full_response.json()["success"] is True

    accumulated_results = []
    for log_limit in count():
        # increasing the page size exponentially should allow us to perform meaningful
        # tests for both heavily populated and sparsely populated instances
        limit = int(10 ** log_limit)
        response = rsession.get(
            f"{base_url}{endpoint_path}&limit={limit}&offset={len(accumulated_results)}"
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
                    f"{base_url}{endpoint_path}&offset={len(accumulated_results)}"
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
            f"{base_url}{endpoint_path}&limit={limit}&offset={len(accumulated_results)+10}"
        )
        assert overrun_response.status_code == 200
        assert overrun_response.json()["success"] is True
        assert overrun_response.json()["result"] == []
