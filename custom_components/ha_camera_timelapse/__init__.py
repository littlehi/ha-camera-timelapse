"""Camera Timelapse integration for Home Assistant."""
from __future__ import annotations

import logging
import sys
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
import homeassistant.helpers.config_validation as cv
import voluptuous as vol

from .const import (
    DOMAIN,
    SERVICE_START_TIMELAPSE,
    SERVICE_STOP_TIMELAPSE,
    ATTR_ENTITY_ID,
    ATTR_INTERVAL,
    ATTR_DURATION,
    ATTR_OUTPUT_PATH,
)
from .coordinator import TimelapseCoordinator

# Set up logging
_LOGGER = logging.getLogger(__name__)

# Log startup information
_LOGGER.debug("Camera Timelapse module loading with Python %s", sys.version)

PLATFORMS = ["switch"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Camera Timelapse from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    coordinator = TimelapseCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    
    hass.data[DOMAIN][entry.entry_id] = coordinator
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    async def start_timelapse(call: ServiceCall) -> None:
        """Handle the service call to start timelapse."""
        entity_id = call.data.get(ATTR_ENTITY_ID)
        interval = call.data.get(ATTR_INTERVAL)
        duration = call.data.get(ATTR_DURATION)
        output_path = call.data.get(ATTR_OUTPUT_PATH)
        
        await coordinator.start_timelapse(
            camera_entity_id=entity_id,
            interval=interval,
            duration=duration,
            output_path=output_path,
        )
    
    async def stop_timelapse(call: ServiceCall) -> None:
        """Handle the service call to stop timelapse."""
        entity_id = call.data.get(ATTR_ENTITY_ID)
        await coordinator.stop_timelapse(entity_id=entity_id)
    
    
    # Register services
    hass.services.async_register(
        DOMAIN,
        SERVICE_START_TIMELAPSE,
        start_timelapse,
        schema=vol.Schema({
            vol.Required(ATTR_ENTITY_ID): cv.entity_id,
            vol.Optional(ATTR_INTERVAL): cv.positive_int,
            vol.Optional(ATTR_DURATION): cv.positive_int,
            vol.Optional(ATTR_OUTPUT_PATH): cv.string,
        }),
    )
    
    hass.services.async_register(
        DOMAIN,
        SERVICE_STOP_TIMELAPSE,
        stop_timelapse,
        schema=vol.Schema({
            vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        }),
    )
    
    
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        coordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.async_shutdown()
    
    return unload_ok

async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)