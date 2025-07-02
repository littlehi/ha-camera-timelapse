"""Camera Timelapse integration for Home Assistant."""
from __future__ import annotations

import logging
import json
import os
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall, Event
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.dispatcher import async_dispatcher_connect, async_dispatcher_send
from homeassistant.components.websocket_api import websocket_command, event_message
import voluptuous as vol

from .const import (
    DOMAIN,
    SERVICE_START_TIMELAPSE,
    SERVICE_STOP_TIMELAPSE,
    SERVICE_TOGGLE_DEBUG,
    ATTR_ENTITY_ID,
    ATTR_INTERVAL,
    ATTR_DURATION,
    ATTR_OUTPUT_PATH,
    ATTR_DEBUG,
    DEBUG_SIGNAL,
    DEBUG_EVENT,
)
from .coordinator import TimelapseCoordinator
from .debug import setup_debug, enable_debug, disable_debug, debug_log
from .frontend import async_register_frontend

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["switch"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Camera Timelapse from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    coordinator = TimelapseCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    
    hass.data[DOMAIN][entry.entry_id] = coordinator
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    # Set up debug tools
    setup_debug(hass)
    
    # Register frontend resources
    await async_register_frontend(hass)
    
    # Set up debug event listener
    async def async_handle_debug_event(event: Event) -> None:
        """Handle debug events."""
        debug_data = event.data
        hass.components.websocket_api.async_register_command({
            "type": "browser_mod/debug",
            "message": debug_data.get("message", ""),
            "level": debug_data.get("level", "info"),
            "data": debug_data.get("data"),
        })
    
    hass.bus.async_listen(DEBUG_EVENT, async_handle_debug_event)
    
    async def start_timelapse(call: ServiceCall) -> None:
        """Handle the service call to start timelapse."""
        entity_id = call.data.get(ATTR_ENTITY_ID)
        interval = call.data.get(ATTR_INTERVAL)
        duration = call.data.get(ATTR_DURATION)
        output_path = call.data.get(ATTR_OUTPUT_PATH)
        
        debug_log(f"Service call: start_timelapse for {entity_id}")
        
        await coordinator.start_timelapse(
            camera_entity_id=entity_id,
            interval=interval,
            duration=duration,
            output_path=output_path,
        )
    
    async def stop_timelapse(call: ServiceCall) -> None:
        """Handle the service call to stop timelapse."""
        entity_id = call.data.get(ATTR_ENTITY_ID)
        debug_log(f"Service call: stop_timelapse for {entity_id}")
        await coordinator.stop_timelapse(entity_id=entity_id)
    
    async def toggle_debug(call: ServiceCall) -> None:
        """Handle the service call to toggle debug mode."""
        debug_enabled = call.data.get(ATTR_DEBUG, False)
        if debug_enabled:
            enable_debug()
            _LOGGER.warning("Debug mode enabled for Camera Timelapse")
        else:
            disable_debug()
        
        # Notify frontend about debug mode change
        hass.bus.async_fire(
            DEBUG_EVENT, 
            {
                "message": f"Debug mode {'enabled' if debug_enabled else 'disabled'}", 
                "level": "info"
            }
        )
    
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
    
    hass.services.async_register(
        DOMAIN,
        SERVICE_TOGGLE_DEBUG,
        toggle_debug,
        schema=vol.Schema({
            vol.Required(ATTR_DEBUG): cv.boolean,
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