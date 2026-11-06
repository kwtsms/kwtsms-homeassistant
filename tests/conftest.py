"""Fixtures. Numbers use country code 999 (unassigned), so nobody can receive them; the kwtSMS client is mocked."""

from unittest.mock import AsyncMock, patch

import pytest


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield


@pytest.fixture
def mock_client():
    """Replace AsyncKwtSMS in both modules; returns the instance mock."""
    with patch("custom_components.kwtsms.config_flow.AsyncKwtSMS") as flow_cls, patch(
        "custom_components.kwtsms.notify.AsyncKwtSMS"
    ) as notify_cls:
        client = flow_cls.return_value
        client.verify = AsyncMock(return_value=(True, 100.0, None))
        client.send = AsyncMock(return_value={"result": "OK", "msg-id": "m1"})
        client.test_mode = True
        notify_cls.return_value = client
        yield client
