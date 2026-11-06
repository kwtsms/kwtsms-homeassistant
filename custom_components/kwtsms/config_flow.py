"""Config and options flow for kwtSMS."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import callback

from kwtsms import AsyncKwtSMS, validate_phone_input

from .const import (
    CONF_NUMBERS,
    CONF_SENDER,
    CONF_TEST_MODE,
    DEFAULT_SENDER,
    DOMAIN,
    VERSION,
)


def parse_numbers(raw: str) -> tuple[list[str], str | None]:
    """Comma or new line separated numbers -> unique normalized numbers, or the first problem found."""
    numbers: list[str] = []
    for part in raw.replace("\n", ",").split(","):
        if not part.strip():
            continue
        ok, error, normalized = validate_phone_input(part.strip())
        if not ok:
            return [], f"{part.strip()}: {error}"
        if normalized not in numbers:
            numbers.append(normalized)
    if not numbers:
        return [], "add at least one phone number"
    return numbers, None


def _options_schema(defaults: dict[str, Any]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_NUMBERS, default=defaults.get(CONF_NUMBERS, "")): str,
            vol.Optional(CONF_SENDER, default=defaults.get(CONF_SENDER, DEFAULT_SENDER)): str,
            vol.Optional(CONF_TEST_MODE, default=defaults.get(CONF_TEST_MODE, False)): bool,
        }
    )


class KwtSmsConfigFlow(ConfigFlow, domain=DOMAIN):
    """Ask for the API login and the numbers, check the login against kwtSMS."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        placeholders = {"detail": ""}
        if user_input is not None:
            numbers, problem = parse_numbers(user_input[CONF_NUMBERS])
            if problem:
                errors[CONF_NUMBERS] = "invalid_number"
                placeholders["detail"] = problem
            else:
                client = AsyncKwtSMS(
                    user_input[CONF_USERNAME], user_input[CONF_PASSWORD], log_file="",
                    app_name=f"kwtsms-homeassistant/{VERSION}",
                )
                try:
                    ok, _balance, error = await client.verify()
                except Exception as exc:  # noqa: BLE001 - any network failure is shown to the user
                    ok, error = False, f"cannot connect: {exc}"
                if not ok:
                    errors["base"] = "cannot_connect" if str(error).startswith(("cannot connect", "Network")) else "invalid_auth"
                    # The library adds a developer hint after " -> " (env variable names): not useful in this UI.
                    placeholders["detail"] = str(error).split(" -> ")[0]
                else:
                    await self.async_set_unique_id(user_input[CONF_USERNAME].strip().lower())
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(
                        title=f"kwtSMS ({user_input[CONF_USERNAME].strip()})",
                        data={CONF_USERNAME: user_input[CONF_USERNAME].strip(), CONF_PASSWORD: user_input[CONF_PASSWORD]},
                        options={
                            CONF_NUMBERS: ", ".join(numbers),
                            CONF_SENDER: user_input.get(CONF_SENDER) or DEFAULT_SENDER,
                            CONF_TEST_MODE: user_input.get(CONF_TEST_MODE, False),
                        },
                    )
        schema = vol.Schema(
            {
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str,
            }
        ).extend(_options_schema(user_input or {}).schema)
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors, description_placeholders=placeholders)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return KwtSmsOptionsFlow()


class KwtSmsOptionsFlow(OptionsFlow):
    """Change the numbers, the Sender ID and test mode."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        placeholders = {"detail": ""}
        if user_input is not None:
            numbers, problem = parse_numbers(user_input[CONF_NUMBERS])
            if problem:
                errors[CONF_NUMBERS] = "invalid_number"
                placeholders["detail"] = problem
            else:
                return self.async_create_entry(
                    data={
                        CONF_NUMBERS: ", ".join(numbers),
                        CONF_SENDER: user_input.get(CONF_SENDER) or DEFAULT_SENDER,
                        CONF_TEST_MODE: user_input.get(CONF_TEST_MODE, False),
                    }
                )
        return self.async_show_form(
            step_id="init",
            data_schema=_options_schema(user_input or dict(self.config_entry.options)),
            errors=errors,
            description_placeholders=placeholders,
        )
