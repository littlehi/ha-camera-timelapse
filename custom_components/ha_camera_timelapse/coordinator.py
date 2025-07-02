"""Data coordinator for Camera Timelapse integration."""
from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timedelta
import aiofiles
import aiohttp
from typing import Any, Dict, Optional

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.exceptions import HomeAssistantError
from homeassistant.components.camera import Image
import homeassistant.util.dt as dt_util

from .const import (
    DOMAIN,
    CONF_CAMERA_ENTITY_ID,
    DEFAULT_INTERVAL,
    DEFAULT_DURATION,
    DEFAULT_OUTPUT_PATH,
    STATUS_IDLE,
    STATUS_RECORDING,
    STATUS_PROCESSING,
    STATUS_ERROR,
)

_LOGGER = logging.getLogger(__name__)

class TimelapseCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize."""
        self.hass = hass
        self.config_entry = entry
        self.camera_entity_id = entry.data.get(CONF_CAMERA_ENTITY_ID)
        self._timelapse_tasks = {}
        self._timelapse_data = {}
        
        update_interval = timedelta(seconds=10)
        
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=update_interval,
        )

    async def _async_update_data(self) -> Dict[str, Any]:
        """Update data."""
        # Return the current state of all timelapses
        return self._timelapse_data

    async def start_timelapse(
        self, 
        camera_entity_id: str,
        interval: Optional[int] = None, 
        duration: Optional[int] = None,
        output_path: Optional[str] = None
    ) -> None:
        """Start a timelapse recording."""
        # Cancel any existing timelapse for this entity
        if camera_entity_id in self._timelapse_tasks and not self._timelapse_tasks[camera_entity_id].done():
            self._timelapse_tasks[camera_entity_id].cancel()
            
        # Use defaults from config if not specified
        if interval is None:
            interval = self.config_entry.options.get(
                "default_interval", 
                self.config_entry.data.get("default_interval", DEFAULT_INTERVAL)
            )
        if duration is None:
            duration = self.config_entry.options.get(
                "default_duration", 
                self.config_entry.data.get("default_duration", DEFAULT_DURATION)
            )
        if output_path is None:
            output_path = self.config_entry.options.get(
                "default_output_path", 
                self.config_entry.data.get("default_output_path", DEFAULT_OUTPUT_PATH)
            )
        
        # Ensure output directory exists
        os.makedirs(output_path, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        camera_name = camera_entity_id.split(".")[1]
        frame_dir = os.path.join(output_path, f"timelapse_{camera_name}_{timestamp}")
        os.makedirs(frame_dir, exist_ok=True)
        
        output_file = os.path.join(output_path, f"timelapse_{camera_name}_{timestamp}.mp4")
        
        # Initialize timelapse data
        timelapse_data = {
            "status": STATUS_RECORDING,
            "camera_entity_id": camera_entity_id,
            "interval": interval,
            "duration": duration,
            "output_path": output_path,
            "frame_dir": frame_dir,
            "output_file": output_file,
            "start_time": dt_util.now().isoformat(),
            "end_time": (dt_util.now() + timedelta(minutes=duration)).isoformat(),
            "frames_captured": 0,
            "progress": 0,
            "time_remaining": duration * 60,  # in seconds
        }
        
        self._timelapse_data[camera_entity_id] = timelapse_data
        
        # Start timelapse task
        task = self.hass.async_create_task(
            self._capture_timelapse(
                camera_entity_id, 
                interval, 
                duration, 
                frame_dir, 
                output_file
            )
        )
        self._timelapse_tasks[camera_entity_id] = task
        
        await self.async_request_refresh()
        
    async def stop_timelapse(self, entity_id: str) -> None:
        """Stop timelapse recording."""
        if entity_id in self._timelapse_tasks and not self._timelapse_tasks[entity_id].done():
            self._timelapse_tasks[entity_id].cancel()
            
            # Update status
            if entity_id in self._timelapse_data:
                self._timelapse_data[entity_id]["status"] = STATUS_IDLE
                self._timelapse_data[entity_id]["progress"] = 0
                self._timelapse_data[entity_id]["time_remaining"] = 0
            
            await self.async_request_refresh()
            
    async def _capture_timelapse(
        self, 
        camera_entity_id: str, 
        interval: int, 
        duration: int, 
        frame_dir: str,
        output_file: str
    ) -> None:
        """Capture frames for timelapse."""
        try:
            start_time = dt_util.now()
            end_time = start_time + timedelta(minutes=duration)
            
            frame_count = 0
            
            while dt_util.now() < end_time:
                try:
                    # Capture frame
                    image = await self.hass.components.camera.async_get_image(camera_entity_id)
                    
                    # Save frame to file
                    frame_path = os.path.join(frame_dir, f"frame_{frame_count:06d}.jpg")
                    async with aiofiles.open(frame_path, "wb") as f:
                        await f.write(image.content)
                    
                    frame_count += 1
                    
                    # Update timelapse data
                    elapsed = (dt_util.now() - start_time).total_seconds()
                    total_duration = (end_time - start_time).total_seconds()
                    progress = min(100, int(elapsed / total_duration * 100))
                    time_remaining = max(0, total_duration - elapsed)
                    
                    self._timelapse_data[camera_entity_id].update({
                        "frames_captured": frame_count,
                        "progress": progress,
                        "time_remaining": int(time_remaining),
                    })
                    
                    self.async_set_updated_data(self._timelapse_data)
                    
                except Exception as e:
                    _LOGGER.error("Error capturing frame: %s", e)
                
                # Wait for next interval
                await asyncio.sleep(interval)
            
            # Update status to processing
            self._timelapse_data[camera_entity_id]["status"] = STATUS_PROCESSING
            self.async_set_updated_data(self._timelapse_data)
            
            # Generate timelapse video
            await self._generate_timelapse(frame_dir, output_file)
            
            # Update status to completed
            self._timelapse_data[camera_entity_id]["status"] = STATUS_IDLE
            self._timelapse_data[camera_entity_id]["progress"] = 100
            self._timelapse_data[camera_entity_id]["time_remaining"] = 0
            
            self.async_set_updated_data(self._timelapse_data)
            
        except asyncio.CancelledError:
            _LOGGER.debug("Timelapse canceled for %s", camera_entity_id)
            raise
            
        except Exception as e:
            _LOGGER.error("Error in timelapse: %s", e)
            self._timelapse_data[camera_entity_id]["status"] = STATUS_ERROR
            self.async_set_updated_data(self._timelapse_data)
    
    async def _generate_timelapse(self, frame_dir: str, output_file: str) -> None:
        """Generate timelapse video from frames."""
        # Use ffmpeg to generate timelapse
        try:
            cmd = [
                "ffmpeg",
                "-y",  # Overwrite output file if exists
                "-framerate", "30",  # Output framerate
                "-pattern_type", "glob",
                "-i", f"{frame_dir}/frame_*.jpg",
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                output_file
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                _LOGGER.error("Error generating timelapse: %s", stderr.decode())
                raise HomeAssistantError(f"Failed to generate timelapse: {stderr.decode()}")
            
            _LOGGER.info("Timelapse generated: %s", output_file)
            
        except Exception as e:
            _LOGGER.error("Error generating timelapse: %s", e)
            raise HomeAssistantError(f"Failed to generate timelapse: {str(e)}")
    
    async def async_shutdown(self) -> None:
        """Cancel any active timelapse tasks."""
        for entity_id, task in self._timelapse_tasks.items():
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass