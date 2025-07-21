"""Config flow for Camera Timelapse integration."""
from __future__ import annotations

import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry

from .const import (
    DOMAIN,
    CONF_CAMERA_ENTITY_ID,
    CONF_DEFAULT_INTERVAL,
    CONF_DEFAULT_DURATION,
    CONF_DEFAULT_OUTPUT_PATH,
    CONF_DEBUG_MODE,
    CONF_UPLOAD_TO_GOOGLE_PHOTOS,
    CONF_GOOGLE_PHOTOS_ALBUM,
    CONF_GOOGLE_PHOTOS_CONFIG_ENTRY_ID,
    DEFAULT_INTERVAL,
    DEFAULT_DURATION,
    DEFAULT_OUTPUT_PATH,
    DEFAULT_DEBUG,
    DEFAULT_UPLOAD_TO_GOOGLE_PHOTOS,
    DEFAULT_GOOGLE_PHOTOS_ALBUM,
    DEFAULT_GOOGLE_PHOTOS_CONFIG_ENTRY_ID,
)

_LOGGER = logging.getLogger(__name__)

async def validate_input(hass: HomeAssistant, data: dict) -> dict[str, str]:
    """Validate the user input allows us to connect."""
    # Verify that the selected entity is a camera
    registry = async_get_entity_registry(hass)
    entity_id = data[CONF_CAMERA_ENTITY_ID]
    entity = registry.async_get(entity_id)
    
    if not entity or entity.domain != "camera":
        return {"base": "not_a_camera"}
    
    return {}

@callback
def get_google_photos_entries(hass):
    """Get Google Photos config entries."""
    entries = []
    for entry in hass.config_entries.async_entries("google_photos"):
        if entry.state == "loaded":
            entries.append({
                "value": entry.entry_id,
                "label": f"{entry.title or 'Google Photos'} ({entry.entry_id})"
            })
    return entries

class CameraTimelapseConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Camera Timelapse."""

    VERSION = 1
    
    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> CameraTimelapseOptionsFlow:
        """Get the options flow for this handler."""
        return CameraTimelapseOptionsFlow(config_entry)

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle the initial step."""
        errors = {}
        
        # Get a list of all camera entities
        camera_entities = []
        entity_registry = async_get_entity_registry(self.hass)
        for entity in entity_registry.entities.values():
            if entity.domain == "camera":
                camera_entities.append(entity.entity_id)
                
        if not camera_entities:
            return self.async_abort(reason="no_cameras")
        
        if user_input is not None:
            try:
                errors = await validate_input(self.hass, user_input)
                
                if not errors:
                    # Create a unique ID based on the camera entity
                    await self.async_set_unique_id(user_input[CONF_CAMERA_ENTITY_ID])
                    self._abort_if_unique_id_configured()
                    
                    return self.async_create_entry(
                        title=f"Timelapse for {user_input[CONF_CAMERA_ENTITY_ID]}",
                        data=user_input,
                    )
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        # Generate schema with dropdown for camera selection
        # 获取所有可用的 Google Photos 配置条目
        google_photos_entries = get_google_photos_entries(self.hass)
        
        schema = vol.Schema(
            {
                vol.Required(CONF_CAMERA_ENTITY_ID): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="camera")
                ),
                vol.Optional(CONF_DEFAULT_INTERVAL, default=DEFAULT_INTERVAL): cv.positive_int,
                vol.Optional(CONF_DEFAULT_DURATION, default=DEFAULT_DURATION): cv.positive_int,
                vol.Optional(CONF_DEFAULT_OUTPUT_PATH, default=DEFAULT_OUTPUT_PATH): cv.string,
                vol.Optional(CONF_DEBUG_MODE, default=DEFAULT_DEBUG): cv.boolean,
                vol.Optional(CONF_UPLOAD_TO_GOOGLE_PHOTOS, default=DEFAULT_UPLOAD_TO_GOOGLE_PHOTOS): cv.boolean,
                vol.Optional(CONF_GOOGLE_PHOTOS_ALBUM, default=DEFAULT_GOOGLE_PHOTOS_ALBUM): cv.string,
            }
        )
        
        # 如果有可用的 Google Photos 配置条目，添加选择器
        if google_photos_entries:
            schema = schema.extend({
                vol.Optional(CONF_GOOGLE_PHOTOS_CONFIG_ENTRY_ID): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=google_photos_entries,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                        translation_key="google_photos_account"
                    )
                ),
            })

        return self.async_show_form(
            step_id="user", data_schema=schema, errors=errors
        )

class CameraTimelapseOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Camera Timelapse."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # 获取所有可用的 Google Photos 配置条目
        google_photos_entries = get_google_photos_entries(self.hass)
        
        options = {
            vol.Optional(
                CONF_DEFAULT_INTERVAL,
                default=self.config_entry.options.get(
                    CONF_DEFAULT_INTERVAL, 
                    self.config_entry.data.get(CONF_DEFAULT_INTERVAL, DEFAULT_INTERVAL)
                ),
            ): cv.positive_int,
            vol.Optional(
                CONF_DEFAULT_DURATION,
                default=self.config_entry.options.get(
                    CONF_DEFAULT_DURATION,
                    self.config_entry.data.get(CONF_DEFAULT_DURATION, DEFAULT_DURATION)
                ),
            ): cv.positive_int,
            vol.Optional(
                CONF_DEFAULT_OUTPUT_PATH,
                default=self.config_entry.options.get(
                    CONF_DEFAULT_OUTPUT_PATH,
                    self.config_entry.data.get(CONF_DEFAULT_OUTPUT_PATH, DEFAULT_OUTPUT_PATH)
                ),
            ): cv.string,
            vol.Optional(
                CONF_DEBUG_MODE,
                default=self.config_entry.options.get(
                    CONF_DEBUG_MODE,
                    self.config_entry.data.get(CONF_DEBUG_MODE, DEFAULT_DEBUG)
                ),
            ): cv.boolean,
            vol.Optional(
                CONF_UPLOAD_TO_GOOGLE_PHOTOS,
                default=self.config_entry.options.get(
                    CONF_UPLOAD_TO_GOOGLE_PHOTOS,
                    self.config_entry.data.get(CONF_UPLOAD_TO_GOOGLE_PHOTOS, DEFAULT_UPLOAD_TO_GOOGLE_PHOTOS)
                ),
            ): cv.boolean,
            vol.Optional(
                CONF_GOOGLE_PHOTOS_ALBUM,
                default=self.config_entry.options.get(
                    CONF_GOOGLE_PHOTOS_ALBUM,
                    self.config_entry.data.get(CONF_GOOGLE_PHOTOS_ALBUM, DEFAULT_GOOGLE_PHOTOS_ALBUM)
                ),
            ): cv.string,
        }
        
        # 如果有可用的 Google Photos 配置条目，添加选择器
        if google_photos_entries:
            current_entry_id = self.config_entry.options.get(
                CONF_GOOGLE_PHOTOS_CONFIG_ENTRY_ID,
                self.config_entry.data.get(CONF_GOOGLE_PHOTOS_CONFIG_ENTRY_ID)
            )
            
            options[vol.Optional(
                CONF_GOOGLE_PHOTOS_CONFIG_ENTRY_ID,
                default=current_entry_id,
            )] = selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=google_photos_entries,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                    translation_key="google_photos_account"
                )
            )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(options),
        )