"""Config flow, options flow and notify entities."""

import pytest
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.exceptions import HomeAssistantError
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.kwtsms.config_flow import parse_numbers
from custom_components.kwtsms.const import DOMAIN

USER_INPUT = {
    "username": "ha_username",
    "password": "ha_password",
    "numbers": "+999 1234 5678, 0099912345679, +999 1234 5678",
    "sender": "KWT-SMS",
    "test_mode": True,
}


def test_parse_numbers():
    assert parse_numbers("+999 1234 5678, 0099912345679\n99912345678") == (["99912345678", "99912345679"], None)
    numbers, problem = parse_numbers("12")
    assert numbers == [] and "too short" in problem
    assert parse_numbers(" , ")[1] == "add at least one phone number"


async def test_flow_creates_entry(hass: HomeAssistant, mock_client) -> None:
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.flow.async_configure(result["flow_id"], USER_INPUT)
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {"username": "ha_username", "password": "ha_password"}
    assert result["options"]["numbers"] == "99912345678, 99912345679"
    await hass.async_block_till_done()
    states = hass.states.async_entity_ids("notify")
    assert len(states) == 2


async def test_flow_bad_login(hass: HomeAssistant, mock_client) -> None:
    mock_client.verify.return_value = (False, None, "Authentication error -> Check your API username and password")
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], USER_INPUT)
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_auth"}
    assert result["description_placeholders"]["detail"] == "Authentication error"


async def test_flow_bad_number(hass: HomeAssistant, mock_client) -> None:
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {**USER_INPUT, "numbers": "12"})
    assert result["errors"] == {"numbers": "invalid_number"}
    mock_client.verify.assert_not_called()


async def test_flow_duplicate_account(hass: HomeAssistant, mock_client) -> None:
    MockConfigEntry(domain=DOMAIN, unique_id="ha_username", data={}, options={}).add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], USER_INPUT)
    assert result["type"] is FlowResultType.ABORT


async def _setup(hass, numbers="99912345678"):
    entry = MockConfigEntry(
        domain=DOMAIN, unique_id="ha_username",
        data={"username": "ha_username", "password": "ha_password"},
        options={"numbers": numbers, "sender": "KWT-SMS", "test_mode": True},
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_send_message_with_title(hass: HomeAssistant, mock_client) -> None:
    await _setup(hass)
    entity_id = hass.states.async_entity_ids("notify")[0]
    await hass.services.async_call(
        "notify", "send_message", {"entity_id": entity_id, "title": "Alarm", "message": "Door open"}, blocking=True
    )
    mock_client.send.assert_awaited_once_with("99912345678", "Alarm\nDoor open")


async def test_send_error_is_raised(hass: HomeAssistant, mock_client) -> None:
    await _setup(hass)
    mock_client.send.return_value = {"result": "ERROR", "code": "ERR010", "description": "Zero balance", "action": "Recharge"}
    entity_id = hass.states.async_entity_ids("notify")[0]
    with pytest.raises(HomeAssistantError, match="ERR010"):
        await hass.services.async_call("notify", "send_message", {"entity_id": entity_id, "message": "x"}, blocking=True)


async def test_options_change_numbers(hass: HomeAssistant, mock_client) -> None:
    entry = await _setup(hass)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"numbers": "99912345678, 99912345670", "sender": "KWT-SMS", "test_mode": False}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    assert len(hass.states.async_entity_ids("notify")) == 2


async def test_unload(hass: HomeAssistant, mock_client) -> None:
    entry = await _setup(hass)
    assert await hass.config_entries.async_unload(entry.entry_id)
