import pytest

import requests


@pytest.fixture()
def rsession(variables):
    with requests.Session() as session:
        session.headers = {"user-agent": variables["api_user_agent"]}
        yield session
