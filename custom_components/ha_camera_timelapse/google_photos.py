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
            
        # Try to use the Google Photos service to upload the file
        try:
            # Check if the upload service is available
            service_domain = "google_photos"
            service_name = "upload"
            
            if not hass.services.has_service(service_domain, service_name):
                _LOGGER.error("Google Photos upload service is not available")
                _LOGGER.info("Available Google Photos services: %s", 
                           [s for s in hass.services.async_services().get(service_domain, {}).keys()])
                return False
            
            # Prepare service data
            service_data = {
                "filename": file_path,
            }
            
            if album_name:
                service_data["album"] = album_name
                
            if config_entry_id:
                service_data["config_entry_id"] = config_entry_id
            
            _LOGGER.info("Calling Google Photos upload service with data: %s", service_data)
            
            # Call the service
            await hass.services.async_call(
                service_domain,
                service_name,
                service_data,
                blocking=True
            )
            
            _LOGGER.info("Successfully uploaded file to Google Photos via service")
            return True
            
        except Exception as service_err:
            _LOGGER.error("Failed to upload via Google Photos service: %s", service_err)
            
            # Fallback: Try direct import approach (for older versions)
            try:
                from homeassistant.components.google_photos import async_upload_file
                _LOGGER.info("Trying direct function call as fallback")
                
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
                    _LOGGER.info("Successfully uploaded file to Google Photos via direct function")
                    return True
                else:
                    _LOGGER.error("Failed to upload file to Google Photos via direct function")
                    return False
                    
            except ImportError as import_err:
                _LOGGER.error("Failed to import Google Photos integration: %s", import_err)
                _LOGGER.error("The Google Photos integration may not support direct file uploads from custom components")
                _LOGGER.info("Please check if the Google Photos integration is properly installed and configured")
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