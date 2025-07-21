"""Google Photos integration for Camera Timelapse."""
from __future__ import annotations

import logging
from typing import Optional

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

_LOGGER = logging.getLogger(__name__)

async def async_upload_to_google_photos(
    hass: HomeAssistant, 
    file_path: str, 
    album_name: Optional[str] = None
) -> bool:
    """Upload a file to Google Photos using the official integration.
    
    Args:
        hass: Home Assistant instance
        file_path: Path to the file to upload
        album_name: Optional album name to add the file to
        
    Returns:
        True if successful, False otherwise
    """
    try:
        _LOGGER.info("Uploading file to Google Photos: %s", file_path)
        
        # Check if Google Photos integration is configured
        if "google_photos" not in hass.config.components:
            _LOGGER.error("Google Photos integration is not configured in Home Assistant")
            return False
            
        # Import the upload function from the official integration
        try:
            from homeassistant.components.google_photos import async_upload_file
        except ImportError:
            _LOGGER.error("Failed to import Google Photos integration")
            return False
            
        # Use the Home Assistant Google Photos integration to upload the file
        result = await async_upload_file(hass, file_path, album_name)
        
        if result:
            _LOGGER.info("Successfully uploaded file to Google Photos")
            return True
        else:
            _LOGGER.error("Failed to upload file to Google Photos")
            return False
            
    except Exception as err:
        _LOGGER.error("Error uploading file to Google Photos: %s", err)
        return False