import typing

import homeassistant.config_entries
import homeassistant.core
import saures_api_client.exceptions
import voluptuous
from homeassistant.helpers import config_validation
from homeassistant.helpers.entity_registry import async_entries_for_config_entry, async_get_registry
from saures_api_client import SauresAPIClient, types

from . import const

AUTH_SCHEMA = voluptuous.Schema(
    {
        voluptuous.Required(const.EMAIL): config_validation.string,
        voluptuous.Required(const.PASSWORD): config_validation.string,
    }
)


async def validate_auth(
    email: str, password: str, hass: homeassistant.core.HomeAssistant
) -> types.User:
    """Validates passed user credentials."""

    user = SauresAPIClient.get_user(email, password)

    try:
        await user.client.authenticate()
        return user
    except saures_api_client.exceptions.WrongCredsException:
        raise ValueError


class SauresConfigFlow(homeassistant.config_entries.ConfigFlow, domain=const.DOMAIN):

    data: typing.Optional[typing.Dict[str, typing.Any]]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.saures_user: typing.Optional[types.User] = None

    async def async_step_user(
        self,
        user_input: typing.Optional[typing.Dict[str, str]] = None,
    ):
        """Authenticates user via UI."""

        errors: typing.Dict[str, str] = {}

        if user_input is not None:
            try:
                self.saures_user = await validate_auth(
                    user_input[const.EMAIL], user_input[const.PASSWORD], self.hass
                )
            except ValueError:
                errors["base"] = "auth"

            if not errors:
                self.data = user_input

                return await self.async_step_locations(user_input)

        return self.async_show_form(step_id="user", data_schema=AUTH_SCHEMA, errors=errors)

    async def async_step_locations(self, user_input: typing.Optional[typing.Dict[str, str]] = None):

        errors: typing.Dict[str, str] = {}

        # if user_input is not None:
        #     self.data[const.LOCATIONS].append(
        #         {"label": user_input[const.LOCATION_LABEL], "id": user_input[const.LOCATION_ID]}
        #     )

        locations_schema = voluptuous.Schema(
            {
                voluptuous.Optional(loc.id, msg=loc.label, default=True): config_validation.boolean
                for loc in await self.saures_user.get_locations()
            }
        )

        return self.async_show_form(
            step_id=const.LOCATIONS, data_schema=locations_schema, errors=errors
        )

    @staticmethod
    @homeassistant.core.callback
    def async_get_options_flow(
        config_entry: homeassistant.config_entries.ConfigEntry,
    ) -> homeassistant.config_entries.OptionsFlow:
        """Returns options flow for saures config."""

        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(homeassistant.config_entries.OptionsFlow):
    def __init__(self, config_entry: homeassistant.config_entries.ConfigEntry):
        self.config_entry = config_entry

    async def async_step_init(self):
        """Manages options for custom component."""

        errors: typing.Dict[str, str] = {}

        entity_registry = await async_get_registry(self.hass)

        entries = async_entries_for_config_entry(entity_registry, self.config_entry.entry_id)

        # all_locations =
