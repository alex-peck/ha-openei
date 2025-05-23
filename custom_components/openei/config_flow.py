"""Adds config flow for Blueprint."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import openeihttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.components.sensor import DOMAIN as SENSORS_DOMAIN
from homeassistant.core import HomeAssistant

from .const import (
    CONF_API_KEY,
    CONF_LOCATION,
    CONF_MANUAL_PLAN,
    CONF_PLAN,
    CONF_RADIUS,
    CONF_SENSOR,
    CONF_UTILITY,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class OpenEIFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Blueprint."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self):
        """Initialize."""
        self._data = {}
        self._errors = {}
        self._entry = {}

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        self._errors = {}

        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_user_2()

        return await self._show_config_form(user_input)

    async def async_step_user_2(self, user_input=None):
        """Handle a flow initialized by the user."""
        self._errors = {}

        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_user_3()

        return await self._show_config_form_2(user_input)

    async def async_step_user_3(self, user_input=None):
        """Handle a flow initialized by the user."""
        self._errors = {}

        if user_input is not None:
            if user_input[CONF_SENSOR] == "(none)":
                user_input.pop(CONF_SENSOR, None)
            self._data.update(user_input)
            return self.async_create_entry(
                title=self._data[CONF_UTILITY], data=self._data
            )

        return await self._show_config_form_3(user_input)

    # @staticmethod
    # @callback
    # def async_get_options_flow(config_entry):
    #     """Enable option flow."""
    #     return OpenEIOptionsFlowHandler(config_entry)

    async def _show_config_form(self, user_input):  # pylint: disable=unused-argument
        """Show the configuration form to edit location data."""
        defaults = {}
        return self.async_show_form(
            step_id="user",
            data_schema=_get_schema_step_1(user_input, defaults),
            errors=self._errors,
        )

    async def _show_config_form_2(self, user_input):  # pylint: disable=unused-argument
        """Show the configuration form to edit location data."""
        defaults = {}
        utility_list = await _get_utility_list(self.hass, self._data)
        return self.async_show_form(
            step_id="user_2",
            data_schema=_get_schema_step_2(self._data, defaults, utility_list),
            errors=self._errors,
        )

    async def _show_config_form_3(self, user_input):  # pylint: disable=unused-argument
        """Show the configuration form to edit location data."""
        defaults = {}
        plan_list = await _get_plan_list(self.hass, self._data)
        return self.async_show_form(
            step_id="user_3",
            data_schema=_get_schema_step_3(self.hass, self._data, defaults, plan_list),
            errors=self._errors,
        )

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None):
        """Add reconfigure step to allow to reconfigure a config entry."""
        self._entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        assert self._entry
        self._data = dict(self._entry.data)
        self._errors = {}

        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_reconfig_2()
        return await self._show_reconfig_form(user_input)

    async def _show_reconfig_form(self, user_input):
        """Show the configuration form to edit configuration data."""
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=_get_schema_step_1(user_input, self._data),
            errors=self._errors,
        )

    async def async_step_reconfig_2(self, user_input: dict[str, Any] | None = None):
        """Add reconfigure step to allow to reconfigure a config entry."""
        self._errors = {}

        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_reconfig_3()
        return await self._show_reconfig_2()

    async def _show_reconfig_2(self):
        """Show the configuration form to edit configuration data."""
        defaults = {}
        utility_list = await _get_utility_list(self.hass, self._data)
        _LOGGER.debug("Utility list: %s", utility_list)
        return self.async_show_form(
            step_id="reconfig_2",
            data_schema=_get_schema_step_2(self._data, defaults, utility_list),
            errors=self._errors,
        )

    async def async_step_reconfig_3(self, user_input: dict[str, Any] | None = None):
        """Add reconfigure step to allow to reconfigure a config entry."""
        self._errors = {}

        if user_input is not None:
            if user_input[CONF_SENSOR] == "(none)":
                user_input.pop(CONF_SENSOR, None)
            self._data.update(user_input)
            self.hass.config_entries.async_update_entry(self._entry, data=self._data)
            await self.hass.config_entries.async_reload(self._entry.entry_id)
            _LOGGER.debug("%s reconfigured.", DOMAIN)
            return self.async_abort(reason="reconfigure_successful")
        return await self._show_reconfig_3()

    async def _show_reconfig_3(self):
        """Show the configuration form to edit configuration data."""
        defaults = {}
        plan_list = await _get_plan_list(self.hass, self._data)
        return self.async_show_form(
            step_id="reconfig_3",
            data_schema=_get_schema_step_3(self.hass, self._data, defaults, plan_list),
            errors=self._errors,
        )


def _get_schema_step_1(
    user_input: Optional[Dict[str, Any]],
    default_dict: Dict[str, Any],
) -> vol.Schema:
    """Get a schema using the default_dict as a backup."""
    if user_input is None:
        user_input = {}

    if CONF_LOCATION in user_input.keys() and user_input[CONF_LOCATION] == '""':
        user_input[CONF_LOCATION] = ""

    if CONF_LOCATION in default_dict.keys() and default_dict[CONF_LOCATION] == '""':
        default_dict[CONF_LOCATION] = ""

    def _get_default(key: str, fallback_default: Any = None) -> None:
        """Get default value for key."""
        return user_input.get(key, default_dict.get(key, fallback_default))

    return vol.Schema(
        {
            vol.Required(CONF_API_KEY, default=_get_default(CONF_API_KEY)): str,
            vol.Optional(CONF_LOCATION, default=_get_default(CONF_LOCATION, "")): str,
            vol.Required(CONF_RADIUS, default=_get_default(CONF_RADIUS, 0)): vol.All(
                vol.Coerce(int), vol.Range(min=0, max=200)
            ),
        },
    )


def _get_schema_step_2(
    user_input: Optional[Dict[str, Any]],
    default_dict: Dict[str, Any],
    utility_list: list,
) -> vol.Schema:
    """Get a schema using the default_dict as a backup."""
    if user_input is None:
        user_input = {}

    def _get_default(key: str, fallback_default: Any = None) -> None:
        """Get default value for key."""
        return user_input.get(key, default_dict.get(key, fallback_default))

    return vol.Schema(
        {
            vol.Required(CONF_UTILITY, default=_get_default(CONF_UTILITY, "")): vol.In(
                utility_list
            ),
        },
    )


def _get_schema_step_3(
    hass: HomeAssistant,
    user_input: Optional[Dict[str, Any]],
    default_dict: Dict[str, Any],
    plan_list: list,
) -> vol.Schema:
    """Get a schema using the default_dict as a backup."""
    if user_input is None:
        user_input = {}

    if CONF_SENSOR in default_dict.keys() and default_dict[CONF_SENSOR] == "(none)":
        default_dict.pop(CONF_SENSOR, None)

    def _get_default(key: str, fallback_default: Any = None) -> Any | None:
        """Get default value for key."""
        return user_input.get(key, default_dict.get(key, fallback_default))

    return vol.Schema(
        {
            vol.Optional(CONF_PLAN, default=_get_default(CONF_PLAN)): vol.In(plan_list),
            vol.Optional(
                CONF_MANUAL_PLAN, default=_get_default(CONF_MANUAL_PLAN, "")
            ): str,
            vol.Required(
                CONF_SENSOR, default=_get_default(CONF_SENSOR, "(none)")
            ): vol.In(_get_entities(hass, SENSORS_DOMAIN, "energy", "(none)")),
        },
    )


async def _get_utility_list(hass, user_input) -> list | None:
    """Return list of utilities by lat/lon."""
    lat = None
    lon = None
    api = user_input[CONF_API_KEY]
    address = user_input[CONF_LOCATION]
    radius = user_input[CONF_RADIUS]

    if not bool(address):
        lat = hass.config.latitude
        lon = hass.config.longitude
        address = None

    plans = openeihttp.Rates(api=api, lat=lat, lon=lon, radius=radius, address=address)
    plans = await _lookup_plans(plans)
    utilities = []

    for utility in plans:
        utilities.append(utility)

    _LOGGER.debug("get_utility_list: %s", utilities)
    return utilities


async def _get_plan_list(hass, user_input) -> list | None:
    """Return list of rate plans by lat/lon."""
    lat = None
    lon = None
    address = user_input[CONF_LOCATION]
    api = user_input[CONF_API_KEY]
    radius = user_input[CONF_RADIUS]
    utility = user_input[CONF_UTILITY]

    if not bool(address):
        lat = hass.config.latitude
        lon = hass.config.longitude
        address = None

    plans = openeihttp.Rates(api=api, lat=lat, lon=lon, radius=radius, address=address)
    plans = await _lookup_plans(plans)
    value = {}

    for plan in plans[utility]:
        value[plan["label"]] = plan["name"]

    _LOGGER.debug("get_plan_list: %s", value)
    return value


async def _lookup_plans(handler) -> list:
    """Return list of utilities and plans."""
    response = await handler.lookup_plans()
    _LOGGER.debug("lookup_plans: %s", response)
    return response


def _get_entities(
    hass: HomeAssistant,
    domain: str,
    search: List[str] = None,
    extra_entities: List[str] = None,
) -> List[str]:
    data = []
    if domain not in hass.data:
        return data

    for entity in hass.data[domain].entities:
        if not hasattr(entity, "device_class"):
            continue
        if search is not None and not entity.device_class == search:
            continue
        data.append(entity.entity_id)

    if extra_entities:
        data.insert(0, extra_entities)
    data.sort  # pylint: disable=pointless-statement
    return data
