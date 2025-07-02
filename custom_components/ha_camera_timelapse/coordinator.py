"""Data coordinator for Camera Timelapse integration."""
from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timedelta
import aiofiles
import aiohttp
import aiofiles.os
import urllib.request
import requests
from typing import Any, Dict, Optional, Tuple

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
        # Check if camera entity exists and is available
        try:
            camera_state = self.hass.states.get(camera_entity_id)
            if not camera_state:
                _LOGGER.error("Camera entity %s does not exist", camera_entity_id)
                raise HomeAssistantError(f"Camera entity {camera_entity_id} does not exist")
                
            if camera_state.state == "unavailable":
                _LOGGER.error("Camera entity %s is unavailable", camera_entity_id)
                raise HomeAssistantError(f"Camera entity {camera_entity_id} is unavailable")
                
            # Try to get a test image to verify camera access
            _LOGGER.info("Testing camera access for %s", camera_entity_id)
            try:
                test_image = await async_get_image(self.hass, camera_entity_id, timeout=10)
                _LOGGER.info("Camera test successful: received image of %d bytes", 
                           len(test_image.content) if test_image and test_image.content else 0)
            except Exception as e:
                _LOGGER.error("Failed to access camera %s: %s", camera_entity_id, str(e))
                _LOGGER.warning("Will proceed with timelapse, but image capture may fail")
                
        except Exception as e:
            _LOGGER.error("Error checking camera %s: %s", camera_entity_id, str(e))
                
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
                    # Capture frame with retry mechanism
                    if self._debug:
                        _LOGGER.debug("Capturing frame from camera: %s", camera_entity_id)
                    else:
                        # Even in non-debug mode, log frame captures less frequently
                        if frame_count % 10 == 0:
                            _LOGGER.info("Capturing frame %d for %s", frame_count, camera_entity_id)
                    
                    # Implement retry mechanism
                    max_retries = 3
                    retry_count = 0
                    retry_delay = 2  # seconds
                    image = None
                    
                    while retry_count < max_retries:
                        try:
                            # First check if camera is still available
                            camera_state = self.hass.states.get(camera_entity_id)
                            if not camera_state or camera_state.state == "unavailable":
                                _LOGGER.error("Camera %s is unavailable, skipping frame", camera_entity_id)
                                break
                            
                            # Try different methods of getting the camera image
                            # Method 1: Try the standard Home Assistant API
                            try:
                                image = await async_get_image(self.hass, camera_entity_id, timeout=10)
                                if image and image.content:
                                    _LOGGER.debug("Successfully captured image using standard HA API")
                                    break
                            except Exception as e1:
                                _LOGGER.warning("Standard HA API failed: %s", e1)
                            
                            # Method 2: Try getting the camera stream URL and fetch directly
                            try:
                                camera_data = self.hass.data.get("camera", {})
                                camera_entity = camera_data.get(camera_entity_id.split(".")[1], None)
                                
                                if camera_entity and hasattr(camera_entity, "stream_source"):
                                    stream_source = camera_entity.stream_source
                                    if stream_source:
                                        _LOGGER.info("Trying direct stream access: %s", stream_source)
                                        
                                        # For http streams
                                        if stream_source.startswith(("http://", "https://")):
                                            async with aiohttp.ClientSession() as session:
                                                async with session.get(stream_source, timeout=10) as resp:
                                                    if resp.status == 200:
                                                        content = await resp.read()
                                                        if content:
                                                            from homeassistant.components.camera import Image
                                                            image = Image(content, "image/jpeg")
                                                            _LOGGER.info("Direct stream access successful")
                                                            break
                            except Exception as e2:
                                _LOGGER.warning("Direct stream access failed: %s", e2)
                                
                            # If we got here, we failed to get an image this attempt
                            retry_count += 1
                            if retry_count < max_retries:
                                _LOGGER.warning("All image capture methods failed, retrying (%d/%d) in %d seconds", 
                                              retry_count, max_retries, retry_delay)
                                await asyncio.sleep(retry_delay)
                            else:
                                _LOGGER.error("Failed to capture frame after %d retries and all methods", 
                                            max_retries)
                        
                        except Exception as e:
                            retry_count += 1
                            if retry_count < max_retries:
                                _LOGGER.warning("Failed to capture frame (%d/%d), retrying in %d seconds: %s", 
                                              retry_count, max_retries, retry_delay, str(e))
                                await asyncio.sleep(retry_delay)
                            else:
                                _LOGGER.error("Failed to capture frame after %d retries: %s", 
                                            max_retries, str(e))
                                if isinstance(e, AttributeError):
                                    _LOGGER.error("This may indicate a version mismatch or API change in Home Assistant")
                    
                    if not image or not image.content:
                        _LOGGER.error("No image content received from camera %s after retries", camera_entity_id)
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
            
            # Try multiple methods for generating the video
            # Method 1: Direct pattern approach
            _LOGGER.info("Trying to generate video using direct pattern method...")
            
            # Ensure frames are properly sorted
            frame_files = sorted(frame_files)
            first_frame = os.path.join(frame_dir, frame_files[0]) if frame_files else None
            
            if first_frame and os.path.exists(first_frame):
                _LOGGER.info("First frame exists: %s", first_frame)
                
                # Make absolute paths for inputs and outputs
                output_file = os.path.abspath(output_file)
                frame_pattern = os.path.abspath(os.path.join(frame_dir, "frame_%06d.jpg"))
                
                _LOGGER.info("Output will be saved to: %s", output_file)
                _LOGGER.info("Using frame pattern: %s", frame_pattern)
                
                # Command using direct pattern instead of glob
                cmd = [
                    ffmpeg_path,
                    "-y",  # Overwrite output file if exists
                    "-framerate", "10",  # Input framerate
                    "-i", frame_pattern,  # Input pattern
                    "-c:v", "libx264",
                    "-preset", "ultrafast",  # Fastest encoding
                    "-pix_fmt", "yuv420p",
                    output_file
                ]
            else:
                _LOGGER.warning("Cannot find first frame, falling back to concat method")
                
                # Method 2: Concat method with explicit file list
                input_list_path = os.path.join(frame_dir, "input_list.txt")
                try:
                    with open(input_list_path, "w") as f:
                        for frame in frame_files:
                            full_path = os.path.join(frame_dir, frame)
                            f.write(f"file '{os.path.abspath(full_path)}'\n")
                    _LOGGER.info("Created input file list at %s", input_list_path)
                except Exception as e:
                    _LOGGER.error("Error creating input file list: %s", e)
                    raise HomeAssistantError(f"Error creating input file list: {str(e)}")
                
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
            
            # Create a short delay to ensure file system operations complete
            await asyncio.sleep(2)
            
            # Verify the output file exists and has content
            try:
                if os.path.exists(output_file):
                    file_size = os.path.getsize(output_file)
                    if file_size > 0:
                        _LOGGER.info("Timelapse generated successfully: %s (%d bytes)", 
                                    output_file, file_size)
                        
                        # Additional verification - try to open the file
                        try:
                            with open(output_file, 'rb') as f:
                                # Read first few bytes to verify file is accessible
                                header = f.read(16)
                                _LOGGER.debug("File header verification: %s", header.hex())
                        except Exception as e:
                            _LOGGER.warning("File exists but cannot be opened: %s", e)
                            
                        # Create media source URL for frontend playback
                        try:
                            filename = os.path.basename(output_file)
                            
                            # Try both media locations
                            media_source_url = None
                            
                            # 1. If output path starts with /media/local
                            if output_file.startswith("/media/local/"):
                                relative_path = output_file[len("/media/local/"):]
                                media_source_url = f"media-source://media_source/local/{relative_path}"
                                _LOGGER.info("Using relative media path: %s", relative_path)
                                
                            # 2. If using /media directory
                            elif output_file.startswith("/media/"):
                                relative_path = output_file[len("/media/"):]
                                media_source_url = f"media-source://media_source/{relative_path}"
                                _LOGGER.info("Using media path: %s", relative_path)
                                
                            # 3. Fallback to direct filename
                            else:
                                # Copy the file to media directory as fallback
                                fallback_path = f"/media/local/timelapses/{filename}"
                                os.makedirs(os.path.dirname(fallback_path), exist_ok=True)
                                
                                _LOGGER.info("Copying file to media directory: %s", fallback_path)
                                try:
                                    import shutil
                                    shutil.copy2(output_file, fallback_path)
                                    media_source_url = f"media-source://media_source/local/timelapses/{filename}"
                                    
                                    # Update output_file to the new path
                                    output_file = fallback_path
                                    _LOGGER.info("File copied successfully to media directory")
                                except Exception as copy_err:
                                    _LOGGER.error("Failed to copy file to media directory: %s", copy_err)
                                    # Still use the original output file
                                    media_source_url = f"media-source://media_source/local/timelapses/{filename}"
                            
                            if media_source_url:
                                _LOGGER.info("Media source URL for playback: %s", media_source_url)
                                return media_source_url
                        except Exception as e:
                            _LOGGER.error("Error creating media URL: %s", e)
                    else:
                        _LOGGER.error("Output file exists but is empty: %s", output_file)
                        raise HomeAssistantError(f"Output file exists but is empty: {output_file}")
                else:
                    _LOGGER.error("Output file does not exist: %s", output_file)
                    
                    # Check if directory exists and is writable
                    output_dir = os.path.dirname(output_file)
                    if not os.path.exists(output_dir):
                        _LOGGER.error("Output directory does not exist: %s", output_dir)
                    elif not os.access(output_dir, os.W_OK):
                        _LOGGER.error("Output directory is not writable: %s", output_dir)
                    
                    raise HomeAssistantError(f"Output file does not exist: {output_file}")
            except Exception as check_err:
                _LOGGER.error("Error checking output file: %s", check_err)
                raise HomeAssistantError(f"Error checking output file: {str(check_err)}")
            
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