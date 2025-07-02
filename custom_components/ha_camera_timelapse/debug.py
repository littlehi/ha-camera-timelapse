"""Debug tools for Camera Timelapse."""
from __future__ import annotations

import logging
import json
from typing import Any, Dict, Optional, Union

from homeassistant.components import websocket_api
from homeassistant.components.websocket_api import (
    async_register_command,
    ActiveConnection,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .const import DOMAIN, DEBUG_SIGNAL

_LOGGER = logging.getLogger(__name__)

DEBUG_MODE = False

def enable_debug() -> None:
    """Enable debug mode."""
    global DEBUG_MODE
    DEBUG_MODE = True
    _LOGGER.debug("Debug mode enabled for camera timelapse")

def disable_debug() -> None:
    """Disable debug mode."""
    global DEBUG_MODE
    DEBUG_MODE = False
    _LOGGER.debug("Debug mode disabled for camera timelapse")

def is_debug_enabled() -> bool:
    """Return if debug mode is enabled."""
    return DEBUG_MODE

def debug_log(message: str, data: Optional[Dict[str, Any]] = None) -> None:
    """Log debug message and send to frontend if debug is enabled."""
    if DEBUG_MODE:
        if data:
            _LOGGER.debug("%s: %s", message, json.dumps(data))
        else:
            _LOGGER.debug("%s", message)
            
def debug_console(hass: HomeAssistant, message: str, level: str = "info", data: Optional[Dict[str, Any]] = None) -> None:
    """Send debug message to frontend console."""
    if DEBUG_MODE:
        payload = {
            "type": "debug",
            "message": message,
            "level": level,
            "data": data,
        }
        async_dispatcher_send(hass, DEBUG_SIGNAL, payload)

def setup_debug(hass: HomeAssistant) -> None:
    """Set up debug commands."""
    
    @callback
    @websocket_api.websocket_command({
        "type": "ha_camera_timelapse/debug/toggle",
        "enable": bool,
    })
    async def websocket_toggle_debug(
        hass: HomeAssistant, connection: ActiveConnection, msg: Dict[str, Any]
    ) -> None:
        """Toggle debug mode on or off."""
        global DEBUG_MODE
        DEBUG_MODE = msg["enable"]
        _LOGGER.debug("Camera timelapse debug mode set to %s", DEBUG_MODE)
        connection.send_result(msg["id"], {"success": True, "debug_enabled": DEBUG_MODE})
        
    @callback
    @websocket_api.websocket_command({
        "type": "ha_camera_timelapse/debug/status",
    })
    async def websocket_debug_status(
        hass: HomeAssistant, connection: ActiveConnection, msg: Dict[str, Any]
    ) -> None:
        """Report current debug status."""
        connection.send_result(msg["id"], {"debug_enabled": DEBUG_MODE})
    
    # Register websocket commands
    async_register_command(hass, websocket_toggle_debug)
    async_register_command(hass, websocket_debug_status)