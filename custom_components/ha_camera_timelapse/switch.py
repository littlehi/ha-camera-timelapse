"""Switch platform for Camera Timelapse."""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional, cast

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    CONF_CAMERA_ENTITY_ID,
    ATTR_STATUS,
    ATTR_PROGRESS,
    ATTR_FRAMES_CAPTURED,
    ATTR_TIME_REMAINING,
    ATTR_OUTPUT_FILE,
    ATTR_ERROR_MESSAGE,
    STATUS_IDLE,
    STATUS_RECORDING,
)
from .coordinator import TimelapseCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Camera Timelapse switch from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    # Add our switch entity
    async_add_entities([TimelapseSwitch(coordinator, entry)])


class TimelapseSwitch(CoordinatorEntity, SwitchEntity):
    """Switch to control timelapse recording."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: TimelapseCoordinator, entry: ConfigEntry) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self.coordinator = coordinator
        self.config_entry = entry
        
        self._camera_entity_id = entry.data.get(CONF_CAMERA_ENTITY_ID)
        camera_name = self._camera_entity_id.split(".")[1]
        
        # Set entity info
        self._attr_unique_id = f"{entry.entry_id}_timelapse_switch"
        self._attr_name = f"Timelapse {camera_name}"
        
        # Set device info
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=f"Camera Timelapse {camera_name}",
            manufacturer="Home Assistant Community",
            model="Timelapse Controller",
            sw_version="0.1.0",
        )
        
        # Set default icon
        self._attr_icon = "mdi:camera-iris"
        
    @property
    def is_on(self) -> bool:
        """Return true if timelapse is recording."""
        if self._camera_entity_id in self.coordinator.data:
            return self.coordinator.data[self._camera_entity_id].get("status") == STATUS_RECORDING
        return False

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Start timelapse recording."""
        await self.coordinator.start_timelapse(
            camera_entity_id=self._camera_entity_id
        )

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Stop timelapse recording."""
        await self.coordinator.stop_timelapse(
            entity_id=self._camera_entity_id
        )
    
    @property
    def extra_state_attributes(self) -> Optional[Dict[str, Any]]:
        """Return the state attributes."""
        attrs = {}
        
        if self._camera_entity_id in self.coordinator.data:
            timelapse_data = self.coordinator.data[self._camera_entity_id]
            attrs.update({
                ATTR_STATUS: timelapse_data.get("status", STATUS_IDLE),
                ATTR_PROGRESS: timelapse_data.get("progress", 0),
                ATTR_FRAMES_CAPTURED: timelapse_data.get("frames_captured", 0),
                ATTR_TIME_REMAINING: timelapse_data.get("time_remaining", 0),
            })
            
            # Add error message if present
            if "error_message" in timelapse_data and timelapse_data["error_message"]:
                attrs[ATTR_ERROR_MESSAGE] = timelapse_data["error_message"]
            
            if "output_file" in timelapse_data:
                attrs[ATTR_OUTPUT_FILE] = timelapse_data["output_file"]
                
            if "media_url" in timelapse_data:
                attrs[ATTR_MEDIA_URL] = timelapse_data["media_url"]
                
            # Add other useful attributes
            if "interval" in timelapse_data:
                attrs["interval"] = timelapse_data["interval"]
            if "duration" in timelapse_data:
                attrs["duration"] = timelapse_data["duration"]
            if "start_time" in timelapse_data:
                attrs["start_time"] = timelapse_data["start_time"]
            if "end_time" in timelapse_data:
                attrs["end_time"] = timelapse_data["end_time"]
            if "task_id" in timelapse_data:
                attrs["task_id"] = timelapse_data["task_id"]
            
            # Add task list attribute if available
            if ATTR_TASKS in self.coordinator.data:
                attrs[ATTR_TASKS] = self.coordinator.data[ATTR_TASKS]
        
        return attrs