"""One notify entity per phone number: notify.send_message with entity_id notify.sms_<number>."""

from __future__ import annotations

from homeassistant.components.notify import NotifyEntity, NotifyEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from kwtsms import AsyncKwtSMS

from .const import (
    CONF_NUMBERS,
    CONF_SENDER,
    CONF_TEST_MODE,
    DEFAULT_SENDER,
    VERSION,
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    client = AsyncKwtSMS(
        entry.data[CONF_USERNAME],
        entry.data[CONF_PASSWORD],
        sender_id=entry.options.get(CONF_SENDER) or DEFAULT_SENDER,
        test_mode=bool(entry.options.get(CONF_TEST_MODE, False)),
        log_file="",
        app_name=f"kwtsms-homeassistant/{VERSION}",
    )
    numbers = [n.strip() for n in entry.options.get(CONF_NUMBERS, "").split(",") if n.strip()]
    async_add_entities(KwtSmsNotifyEntity(entry, client, n) for n in numbers)


class KwtSmsNotifyEntity(NotifyEntity):
    """Sends an SMS to one phone number."""

    _attr_supported_features = NotifyEntityFeature.TITLE
    _attr_has_entity_name = True

    def __init__(self, entry: ConfigEntry, client: AsyncKwtSMS, number: str) -> None:
        self._client = client
        self._number = number
        self._attr_unique_id = f"{entry.entry_id}_{number}"
        self._attr_name = f"SMS {number}"
        self._attr_extra_state_attributes = {"phone_number": number, "test_mode": client.test_mode}

    async def async_send_message(self, message: str, title: str | None = None) -> None:
        text = f"{title}\n{message}" if title else message
        result = await self._client.send(self._number, text)
        if result.get("result") != "OK":
            raise HomeAssistantError(
                f"kwtSMS {result.get('code', 'ERROR')}: {result.get('description', 'send failed')}"
                + (f" ({result['action']})" if result.get("action") else "")
            )
