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
from homeassistant.components.camera import Image, async_get_image
import homeassistant.util.dt as dt_util

from .const import (
    DOMAIN,
    CONF_CAMERA_ENTITY_ID,
    DEFAULT_INTERVAL,
    DEFAULT_DURATION,
    DEFAULT_OUTPUT_PATH,
    DEFAULT_DEBUG,
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
        self._debug = entry.options.get("debug", DEFAULT_DEBUG)
        
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
        
        # Ensure output directory exists and check permissions
        try:
            os.makedirs(output_path, exist_ok=True)
            
            # Test write permissions by creating a test file
            test_file = os.path.join(output_path, ".permission_test")
            try:
                with open(test_file, "w") as f:
                    f.write("test")
                os.remove(test_file)
                _LOGGER.debug("Output directory has write permissions: %s", output_path)
            except PermissionError:
                _LOGGER.warning("No write permission for output directory: %s", output_path)
                _LOGGER.warning("Timelapse video may fail to save. Check directory permissions.")
        except Exception as e:
            _LOGGER.error("Error creating output directory %s: %s", output_path, e)
        
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
            "error_message": "",  # Will be populated if an error occurs
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
            
            _LOGGER.info("Starting timelapse capture for camera %s, frames every %d seconds for %d minutes", 
                      camera_entity_id, interval, duration)
            _LOGGER.info("Frames will be saved to %s", frame_dir)
            _LOGGER.info("Final timelapse will be saved as %s", output_file)
            
            while dt_util.now() < end_time:
                try:
                    # Capture frame
                    if self._debug:
                        _LOGGER.debug("Capturing frame from camera: %s", camera_entity_id)
                    else:
                        # Even in non-debug mode, log frame captures less frequently
                        if frame_count % 10 == 0:
                            _LOGGER.info("Capturing frame %d for %s", frame_count, camera_entity_id)
                    try:
                        # Use the correct way to get camera image
                        image = await async_get_image(self.hass, camera_entity_id)
                    except AttributeError as attr_err:
                        _LOGGER.error("Error with camera API call: %s", attr_err)
                        _LOGGER.error("This may indicate a version mismatch or API change in Home Assistant")
                        raise HomeAssistantError(f"Cannot access camera: {attr_err}")
                    
                    if not image or not image.content:
                        _LOGGER.error("No image content received from camera %s", camera_entity_id)
                        continue
                    
                    if self._debug:
                        _LOGGER.debug("Image captured, size: %d bytes", len(image.content))
                    
                    # Save frame to file
                    frame_path = os.path.join(frame_dir, f"frame_{frame_count:06d}.jpg")
                    if self._debug:
                        _LOGGER.debug("Saving frame to %s", frame_path)
                    
                    async with aiofiles.open(frame_path, "wb") as f:
                        await f.write(image.content)
                    
                    # Verify file was written
                    if os.path.exists(frame_path) and os.path.getsize(frame_path) > 0:
                        if self._debug:
                            _LOGGER.debug("Frame saved successfully: %s (%d bytes)", 
                                         frame_path, os.path.getsize(frame_path))
                        frame_count += 1
                    else:
                        _LOGGER.error("Failed to save frame or file is empty: %s", frame_path)
                    
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
                    
                except HomeAssistantError as ha_err:
                    _LOGGER.error("Home Assistant error: %s", ha_err)
                    _LOGGER.exception("Home Assistant error details")
                    # If we have a Home Assistant error, wait a bit longer before retrying
                    await asyncio.sleep(min(interval, 10))
                    continue
                except Exception as e:
                    _LOGGER.error("Error capturing frame: %s", e)
                    _LOGGER.exception("Detailed exception information")
                    # Try to continue with next frame after a short delay
                    await asyncio.sleep(2)
                    continue
                
                # Wait for next interval
                if self._debug:
                    _LOGGER.debug("Waiting %d seconds until next frame capture", interval)
                await asyncio.sleep(interval)
            
            # Log completion of frame capture
            _LOGGER.info("Finished capturing frames for %s. Total frames: %d", 
                      camera_entity_id, frame_count)
            
            # Update status to processing
            self._timelapse_data[camera_entity_id]["status"] = STATUS_PROCESSING
            self.async_set_updated_data(self._timelapse_data)
            
            # Generate timelapse video
            _LOGGER.info("Starting timelapse generation from %d frames", frame_count)
            media_url = await self._generate_timelapse(frame_dir, output_file)
            
            # Update status to completed
            self._timelapse_data[camera_entity_id]["status"] = STATUS_IDLE
            self._timelapse_data[camera_entity_id]["progress"] = 100
            self._timelapse_data[camera_entity_id]["time_remaining"] = 0
            
            # Add media URL for frontend playback if available
            if media_url:
                self._timelapse_data[camera_entity_id]["media_url"] = media_url
            
            # Log successful completion
            _LOGGER.info("Timelapse completed and saved to: %s", output_file)
            
            self.async_set_updated_data(self._timelapse_data)
            
        except asyncio.CancelledError:
            _LOGGER.debug("Timelapse canceled for %s", camera_entity_id)
            raise
            
        except Exception as e:
            _LOGGER.error("Error in timelapse: %s", e)
            _LOGGER.exception("Detailed timelapse error information")
            self._timelapse_data[camera_entity_id]["status"] = STATUS_ERROR
            self._timelapse_data[camera_entity_id]["error_message"] = str(e)
            self.async_set_updated_data(self._timelapse_data)
    
    async def _generate_timelapse(self, frame_dir: str, output_file: str) -> None:
        """Generate timelapse video from frames."""
        # Use ffmpeg to generate timelapse
        try:
            # Check if we have frames to process
            frame_files = [f for f in os.listdir(frame_dir) if f.startswith("frame_") and f.endswith(".jpg")]
            if not frame_files:
                _LOGGER.error("No frames found in %s, cannot create timelapse", frame_dir)
                raise HomeAssistantError(f"No frames found in {frame_dir}, cannot create timelapse")
            
            _LOGGER.info("Found %d frames in %s", len(frame_files), frame_dir)
            
            # Verify ffmpeg is available - with enhanced checking
            import shutil
            import subprocess
            
            ffmpeg_path = shutil.which("ffmpeg")
            if not ffmpeg_path:
                _LOGGER.error("ffmpeg not found in PATH, cannot create timelapse")
                
                # Try to find ffmpeg in common locations
                common_paths = [
                    "/usr/bin/ffmpeg", 
                    "/usr/local/bin/ffmpeg",
                    "/bin/ffmpeg",
                    "/opt/bin/ffmpeg",
                    "/usr/sbin/ffmpeg"
                ]
                
                for path in common_paths:
                    if os.path.exists(path) and os.access(path, os.X_OK):
                        _LOGGER.info("Found ffmpeg at alternate location: %s", path)
                        ffmpeg_path = path
                        break
                
                if not ffmpeg_path:
                    _LOGGER.error("ffmpeg not found in any common locations")
                    raise HomeAssistantError("ffmpeg not found, cannot create timelapse")
            
            _LOGGER.info("Using ffmpeg at %s", ffmpeg_path)
            
            # Verify ffmpeg works
            try:
                version_process = await asyncio.create_subprocess_exec(
                    ffmpeg_path, "-version",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await version_process.communicate()
                
                if version_process.returncode == 0:
                    version_info = stdout.decode().splitlines()[0]
                    _LOGGER.info("FFmpeg version: %s", version_info)
                else:
                    _LOGGER.warning("FFmpeg version check failed: %s", stderr.decode() if stderr else "Unknown error")
            except Exception as e:
                _LOGGER.error("Error checking FFmpeg version: %s", e)
            
            # Try a simpler, more compatible FFmpeg command - using direct file input
            # Create input file list for ffmpeg
            input_list_path = os.path.join(frame_dir, "input_list.txt")
            try:
                with open(input_list_path, "w") as f:
                    for frame in sorted(frame_files):
                        f.write(f"file '{os.path.join(frame_dir, frame)}'\n")
                _LOGGER.info("Created input file list at %s", input_list_path)
            except Exception as e:
                _LOGGER.error("Error creating input file list: %s", e)
                
            # Command with explicit file list instead of glob pattern
            cmd = [
                ffmpeg_path,
                "-y",  # Overwrite output file if exists
                "-f", "concat",
                "-safe", "0",
                "-i", input_list_path,
                "-c:v", "libx264",
                "-preset", "ultrafast",  # Fastest encoding
                "-pix_fmt", "yuv420p",
                "-r", "10",  # Output framerate
                output_file
            ]
            
            # Log the frames before processing
            _LOGGER.info("Frame files found (first 5):")
            for frame in frame_files[:5]:
                file_path = os.path.join(frame_dir, frame)
                file_size = os.path.getsize(file_path)
                _LOGGER.info("  - %s (%d bytes)", frame, file_size)
            
            _LOGGER.debug("Executing ffmpeg command: %s", " ".join(cmd))
            
            _LOGGER.info("Starting FFmpeg process to generate timelapse video...")
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                stderr_text = stderr.decode() if stderr else "Unknown error"
                _LOGGER.error("Error generating timelapse (return code %d): %s", 
                              process.returncode, stderr_text)
                
                # Log more detailed debug info
                if stderr:
                    stderr_lines = stderr_text.splitlines()
                    for line in stderr_lines[:20]:  # Log first 20 lines at most
                        _LOGGER.error("FFmpeg error detail: %s", line)
                
                raise HomeAssistantError(f"Failed to generate timelapse: {stderr_text}")
            
            if stdout:
                stdout_text = stdout.decode()
                _LOGGER.debug("FFmpeg stdout: %s", stdout_text)
            
            # Verify the output file exists and has content
            if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                _LOGGER.info("Timelapse generated successfully: %s (%d bytes)", 
                             output_file, os.path.getsize(output_file))
                
                # Create media source URL for frontend playback
                try:
                    filename = os.path.basename(output_file)
                    # If output path starts with /media/local, strip it to get relative path
                    if output_file.startswith("/media/local/"):
                        relative_path = output_file[len("/media/local/"):]
                        media_source_url = f"media-source://media_source/local/{relative_path}"
                    else:
                        # For other paths, just use the basename
                        media_source_url = f"media-source://media_source/local/timelapses/{filename}"
                    
                    _LOGGER.info("Media source URL for playback: %s", media_source_url)
                    return media_source_url
                except Exception as e:
                    _LOGGER.error("Error creating media URL: %s", e)
                    
            else:
                _LOGGER.error("Output file does not exist or is empty: %s", output_file)
                raise HomeAssistantError(f"Output file does not exist or is empty: {output_file}")
            
        except Exception as e:
            _LOGGER.error("Error generating timelapse: %s", e)
            _LOGGER.exception("Detailed exception information")
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