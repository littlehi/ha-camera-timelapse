"""Google Photos integration for Camera Timelapse."""
from __future__ import annotations

import logging
from typing import Optional

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er

_LOGGER = logging.getLogger(__name__)

async def async_upload_to_google_photos(
    hass: HomeAssistant, 
    file_path: str, 
    album_name: Optional[str] = None,
    config_entry_id: Optional[str] = None
) -> bool:
    """Upload a file to Google Photos using the official integration.
    
    Args:
        hass: Home Assistant instance
        file_path: Path to the file to upload
        album_name: Optional album name to add the file to
        config_entry_id: Optional config entry ID to specify which Google Photos account to use
        
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
        
        # 检查函数签名，看是否支持 config_entry_id 参数
        import inspect
        sig = inspect.signature(async_upload_file)
        supports_config_entry = "config_entry_id" in sig.parameters
        
        # 使用官方集成上传文件
        if supports_config_entry and config_entry_id:
            _LOGGER.info("Using specific Google Photos config entry: %s", config_entry_id)
            result = await async_upload_file(hass, file_path, album_name, config_entry_id=config_entry_id)
        else:
            if config_entry_id:
                _LOGGER.warning("Config entry ID specified but not supported by Google Photos integration")
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

async def async_get_google_photos_accounts(hass: HomeAssistant) -> list[dict]:
    """Get a list of configured Google Photos accounts.
    
    Args:
        hass: Home Assistant instance
        
    Returns:
        List of dicts with account info (entry_id, title)
    """
    accounts = []
    
    # Check if Google Photos integration is configured
    if "google_photos" not in hass.config.components:
        _LOGGER.warning("Google Photos integration is not configured in Home Assistant")
        return accounts
    
    # Get all config entries for Google Photos
    from homeassistant.components.google_photos.const import DOMAIN as GOOGLE_PHOTOS_DOMAIN
    
    for entry in hass.config_entries.async_entries(GOOGLE_PHOTOS_DOMAIN):
        account_info = {
            "entry_id": entry.entry_id,
            "title": entry.title or f"Google Photos ({entry.entry_id})"
        }
        accounts.append(account_info)
    
    return accounts