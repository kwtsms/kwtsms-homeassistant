"""The entity id the README shows."""

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.kwtsms.const import DOMAIN


async def test_entity_id(hass: HomeAssistant, mock_client) -> None:
    entry = MockConfigEntry(domain=DOMAIN, unique_id="u", data={"username": "u", "password": "p"},
                            options={"numbers": "99912345678", "sender": "KWT-SMS", "test_mode": True})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.async_entity_ids("notify") == ["notify.sms_99912345678"]
