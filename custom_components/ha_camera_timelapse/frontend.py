"""Frontend resources for Camera Timelapse."""
from __future__ import annotations

import os
import logging
from typing import List

from homeassistant.components.frontend import (
    add_extra_js_url,
)
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_register_frontend(hass: HomeAssistant) -> None:
    """Register the frontend resources."""
    
    # Get the URL for the debug JS file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    debug_js_path = os.path.join(current_dir, "frontend_debug.js")
    
    if not os.path.exists(debug_js_path):
        _LOGGER.error("Debug JS file not found at %s", debug_js_path)
        return
    
    # Register the JS module
    base_url = f"/custom_components/{DOMAIN}"
    debug_url = f"{base_url}/frontend_debug.js"
    
    try:
        # Add the JS to frontend
        _LOGGER.debug("Registering frontend JS: %s", debug_url)
        add_extra_js_url(hass, debug_url)
        _LOGGER.info("Camera Timelapse debug tools registered")
    except Exception as e:
        _LOGGER.error("Failed to register frontend: %s", e)