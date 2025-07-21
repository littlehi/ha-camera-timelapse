"""Data coordinator for Camera Timelapse integration."""
from __future__ import annotations

import asyncio
import logging
import os
import uuid
import sys
from datetime import datetime, timedelta
import aiofiles
import aiohttp
import aiofiles.os
import urllib.request
import requests
from typing import Any, Dict, List, Optional, Tuple
from functools import partial

from .google_photos import async_upload_to_google_photos

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
    STATUS_UPLOADING,
    STATUS_ERROR,
    ATTR_TASKS,
    MAX_CONCURRENT_TASKS,
    MAX_FRAME_BATCH,
    MAX_FFMPEG_THREADS,
    CONF_UPLOAD_TO_GOOGLE_PHOTOS,
    CONF_GOOGLE_PHOTOS_ALBUM,
    CONF_GOOGLE_PHOTOS_CONFIG_ENTRY_ID,
    DEFAULT_UPLOAD_TO_GOOGLE_PHOTOS,
    DEFAULT_GOOGLE_PHOTOS_ALBUM,
    DEFAULT_GOOGLE_PHOTOS_CONFIG_ENTRY_ID,
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
        self._task_registry = {}  # New task registry for management
        self._debug = entry.options.get("debug", DEFAULT_DEBUG)
        
        # Google Photos 上传设置
        self._upload_to_google_photos = entry.options.get(
            CONF_UPLOAD_TO_GOOGLE_PHOTOS, 
            entry.data.get(CONF_UPLOAD_TO_GOOGLE_PHOTOS, DEFAULT_UPLOAD_TO_GOOGLE_PHOTOS)
        )
        self._google_photos_album = entry.options.get(
            CONF_GOOGLE_PHOTOS_ALBUM, 
            entry.data.get(CONF_GOOGLE_PHOTOS_ALBUM, DEFAULT_GOOGLE_PHOTOS_ALBUM)
        )
        self._google_photos_config_entry_id = entry.options.get(
            CONF_GOOGLE_PHOTOS_CONFIG_ENTRY_ID, 
            entry.data.get(CONF_GOOGLE_PHOTOS_CONFIG_ENTRY_ID, DEFAULT_GOOGLE_PHOTOS_CONFIG_ENTRY_ID)
        )
        
        # 检查Python版本并实现to_thread兼容函数
        self.python_version = sys.version_info
        if self.python_version < (3, 9):
            # Python 3.8或更低版本，创建自己的to_thread函数
            _LOGGER.info("Running on Python %s.%s, using custom to_thread implementation", 
                        self.python_version.major, self.python_version.minor)
            self.to_thread = self._to_thread_compat
        else:
            # Python 3.9+，使用内置的to_thread
            self.to_thread = asyncio.to_thread
        
        # 减少更新频率以降低系统负载，从10秒改为30秒
        update_interval = timedelta(seconds=30)
        
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=update_interval,
        )

    async def _async_update_data(self) -> Dict[str, Any]:
        """Update data."""
        # Return the current state of all timelapses
        data = self._timelapse_data.copy()
        
        # Add task registry information
        task_list = []
        for task_id, task_info in self._task_registry.items():
            task_list.append({
                "task_id": task_id,
                "camera_entity_id": task_info.get("camera_entity_id"),
                "status": task_info.get("status"),
                "start_time": task_info.get("start_time"),
                "progress": task_info.get("progress", 0),
                "frames_captured": task_info.get("frames_captured", 0),
            })
        
        data[ATTR_TASKS] = task_list
        return data

    async def start_timelapse(
        self, 
        camera_entity_id: str,
        interval: Optional[int] = None, 
        duration: Optional[int] = None,
        output_path: Optional[str] = None
    ) -> str:
        """Start a timelapse recording. Returns task_id."""
        # 检查系统负载，限制并发任务数
        active_tasks = sum(1 for task in self._timelapse_tasks.values() if not task.done())
        if active_tasks >= MAX_CONCURRENT_TASKS:
            _LOGGER.error("Maximum number of concurrent timelapse tasks (%d) reached. Cannot start new task.", 
                         MAX_CONCURRENT_TASKS)
            raise HomeAssistantError(
                f"Maximum number of concurrent timelapse tasks ({MAX_CONCURRENT_TASKS}) reached. "
                "Please wait for an existing task to complete."
            )
        
        # Check if camera entity exists and is available
        try:
            camera_state = self.hass.states.get(camera_entity_id)
            if not camera_state:
                _LOGGER.error("Camera entity %s does not exist", camera_entity_id)
                raise HomeAssistantError(f"Camera entity {camera_entity_id} does not exist")
                
            if camera_state.state == "unavailable":
                _LOGGER.error("Camera entity %s is unavailable", camera_entity_id)
                raise HomeAssistantError(f"Camera entity {camera_entity_id} is unavailable")
                
            # Try to get a test image to verify camera access (使用更短的超时)
            _LOGGER.info("Testing camera access for %s", camera_entity_id)
            try:
                test_image = await async_get_image(self.hass, camera_entity_id, timeout=7)
                _LOGGER.info("Camera test successful: received image of %d bytes", 
                           len(test_image.content) if test_image and test_image.content else 0)
            except Exception as e:
                _LOGGER.error("Failed to access camera %s: %s", camera_entity_id, str(e))
                _LOGGER.warning("Will proceed with timelapse, but image capture may fail")
                
        except Exception as e:
            _LOGGER.error("Error checking camera %s: %s", camera_entity_id, str(e))
                
        # Cancel any existing timelapse for this entity
        if camera_entity_id in self._timelapse_tasks and not self._timelapse_tasks[camera_entity_id].done():
            _LOGGER.info("Canceling existing timelapse task for %s", camera_entity_id)
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
        
        # Generate a unique task ID
        task_id = str(uuid.uuid4())
        
        # Initialize timelapse data
        timelapse_data = {
            "task_id": task_id,
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
        
        # Register the task in the task registry
        self._task_registry[task_id] = {
            "camera_entity_id": camera_entity_id,
            "status": STATUS_RECORDING,
            "start_time": dt_util.now().isoformat(),
            "progress": 0,
            "frames_captured": 0,
            "output_file": output_file
        }
        
        # Start timelapse task
        task = self.hass.async_create_task(
            self._capture_timelapse(
                task_id,
                camera_entity_id, 
                interval, 
                duration, 
                frame_dir, 
                output_file
            )
        )
        self._timelapse_tasks[camera_entity_id] = task
        
        await self.async_request_refresh()
        
        return task_id
        
    async def stop_timelapse(self, entity_id: str, task_id: Optional[str] = None) -> None:
        """Stop timelapse recording and generate video with captured frames."""
        # If task_id is provided, verify it matches the entity_id
        if task_id:
            if task_id not in self._task_registry:
                _LOGGER.error("Task ID %s does not exist", task_id)
                raise HomeAssistantError(f"Task ID {task_id} does not exist")
                
            task_camera_id = self._task_registry[task_id].get("camera_entity_id")
            if task_camera_id != entity_id:
                _LOGGER.error("Task ID %s does not match camera entity %s", task_id, entity_id)
                raise HomeAssistantError(f"Task ID {task_id} does not match camera entity {entity_id}")
                
        if entity_id in self._timelapse_tasks and not self._timelapse_tasks[entity_id].done():
            # Get frame directory and output file path before cancelling task
            frame_dir = None
            output_file = None
            if entity_id in self._timelapse_data:
                frame_dir = self._timelapse_data[entity_id].get("frame_dir")
                output_file = self._timelapse_data[entity_id].get("output_file")
                task_id = self._timelapse_data[entity_id].get("task_id")
                
                # Update status to processing
                self._timelapse_data[entity_id]["status"] = STATUS_PROCESSING
                self._timelapse_data[entity_id]["time_remaining"] = 0
                
                # Update task registry
                if task_id and task_id in self._task_registry:
                    self._task_registry[task_id]["status"] = STATUS_PROCESSING
                    self._task_registry[task_id]["progress"] = 99  # Processing status
                
                await self.async_request_refresh()
            
            # Cancel the ongoing task
            self._timelapse_tasks[entity_id].cancel()
            
            # If we have captured frames, generate the video
            if frame_dir and output_file:
                _LOGGER.info("Generating timelapse video from manually stopped recording")
                try:
                    # Generate timelapse video with captured frames and clean up frames
                    media_url = await self._generate_timelapse(frame_dir, output_file, cleanup_frames=True)
                    
                    # Update status and add media URL for frontend playback
                    self._timelapse_data[entity_id]["status"] = STATUS_IDLE
                    self._timelapse_data[entity_id]["progress"] = 100
                    
                    # Update task registry
                    if task_id and task_id in self._task_registry:
                        self._task_registry[task_id]["status"] = STATUS_IDLE
                        self._task_registry[task_id]["progress"] = 100
                        self._task_registry[task_id]["media_url"] = media_url
                    
                    if media_url:
                        self._timelapse_data[entity_id]["media_url"] = media_url
                        _LOGGER.info("Timelapse completed and saved to: %s", output_file)
                    
                except Exception as e:
                    _LOGGER.error("Error generating timelapse after manual stop: %s", e)
                    _LOGGER.exception("Detailed timelapse error information")
                    self._timelapse_data[entity_id]["status"] = STATUS_ERROR
                    self._timelapse_data[entity_id]["error_message"] = str(e)
                    
                    # Update task registry
                    if task_id and task_id in self._task_registry:
                        self._task_registry[task_id]["status"] = STATUS_ERROR
                        self._task_registry[task_id]["error_message"] = str(e)
            else:
                # If no frames were captured or paths not available, just set to idle
                self._timelapse_data[entity_id]["status"] = STATUS_IDLE
                self._timelapse_data[entity_id]["progress"] = 0
                
                # Update task registry
                if task_id and task_id in self._task_registry:
                    self._task_registry[task_id]["status"] = STATUS_IDLE
                    self._task_registry[task_id]["progress"] = 0
            
            await self.async_request_refresh()
            
    
    async def get_task_info(self, task_id: str) -> Dict[str, Any]:
        """Get information about a task."""
        if task_id not in self._task_registry:
            raise HomeAssistantError(f"Task ID {task_id} does not exist")
            
        return self._task_registry[task_id]
    
    async def list_tasks(self) -> List[Dict[str, Any]]:
        """List all timelapse tasks."""
        tasks = []
        for task_id, task_info in self._task_registry.items():
            tasks.append({
                "task_id": task_id,
                "camera_entity_id": task_info.get("camera_entity_id"),
                "status": task_info.get("status"),
                "start_time": task_info.get("start_time"),
                "frames_captured": task_info.get("frames_captured", 0),
                "progress": task_info.get("progress", 0),
                "output_file": task_info.get("output_file", ""),
                "media_url": task_info.get("media_url", ""),
            })
        return tasks
    
    async def _capture_timelapse(
        self,
        task_id: str,
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
                    
                    # 优化重试机制，减少资源消耗
                    max_retries = 3
                    retry_count = 0
                    retry_delay = 2  # seconds
                    # 递增重试延迟以减少系统压力
                    retry_backoff = 1.5  # 每次重试增加1.5倍延迟
                    image = None
                    
                    # 使用信号量限制并发请求
                    camera_state = self.hass.states.get(camera_entity_id)
                    if not camera_state or camera_state.state == "unavailable":
                        _LOGGER.error("Camera %s is unavailable, skipping frame", camera_entity_id)
                    else:
                        while retry_count < max_retries:
                            try:
                                # 重新检查是否仍然可用，避免不必要的操作
                                if retry_count > 0:
                                    camera_state = self.hass.states.get(camera_entity_id)
                                    if not camera_state or camera_state.state == "unavailable":
                                        _LOGGER.error("Camera %s became unavailable, stopping retries", camera_entity_id)
                                        break
                                
                                # 标准方法: 使用Home Assistant API，但减少超时时间
                                try:
                                    # 减少超时时间，避免长时间阻塞
                                    image = await async_get_image(self.hass, camera_entity_id, timeout=7)
                                    if image and image.content:
                                        _LOGGER.debug("Successfully captured image using standard HA API")
                                        break
                                except Exception as e1:
                                    _LOGGER.warning("Standard HA API failed: %s", e1)
                                
                                # 备选方法: 直接访问摄像头流
                                if retry_count == max_retries - 1:  # 只在最后一次重试时尝试此方法，减少资源使用
                                    try:
                                        camera_data = self.hass.data.get("camera", {})
                                        camera_entity = camera_data.get(camera_entity_id.split(".")[1], None)
                                        
                                        if camera_entity and hasattr(camera_entity, "stream_source"):
                                            stream_source = camera_entity.stream_source
                                            if stream_source and stream_source.startswith(("http://", "https://")):
                                                _LOGGER.info("Trying direct stream access as last resort")
                                                
                                                # 使用更短的超时
                                                async with aiohttp.ClientSession() as session:
                                                    async with session.get(stream_source, timeout=7) as resp:
                                                        if resp.status == 200:
                                                            content = await resp.read()
                                                            if content:
                                                                from homeassistant.components.camera import Image
                                                                image = Image(content, "image/jpeg")
                                                                _LOGGER.info("Direct stream access successful")
                                                                break
                                    except Exception as e2:
                                        _LOGGER.warning("Direct stream access failed: %s", e2)
                                    
                                # 增加重试延迟
                                retry_count += 1
                                if retry_count < max_retries:
                                    current_delay = retry_delay * (retry_backoff ** (retry_count - 1))
                                    _LOGGER.warning("Image capture failed, retrying (%d/%d) in %.1f seconds", 
                                                  retry_count, max_retries, current_delay)
                                    await asyncio.sleep(current_delay)
                                else:
                                    _LOGGER.error("Failed to capture frame after %d retries", max_retries)
                            
                            except Exception as e:
                                retry_count += 1
                                if retry_count < max_retries:
                                    current_delay = retry_delay * (retry_backoff ** (retry_count - 1))
                                    _LOGGER.warning("Failed to capture frame (%d/%d), retrying in %.1f seconds: %s", 
                                                  retry_count, max_retries, current_delay, str(e))
                                    await asyncio.sleep(current_delay)
                                else:
                                    _LOGGER.error("Failed to capture frame after %d retries: %s", 
                                                max_retries, str(e))
                    
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
                    
                    # Update task registry
                    if task_id in self._task_registry:
                        self._task_registry[task_id].update({
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
            
            # Update task registry
            if task_id in self._task_registry:
                self._task_registry[task_id]["status"] = STATUS_PROCESSING
                self._task_registry[task_id]["progress"] = 95  # Processing status
            
            self.async_set_updated_data(self._timelapse_data)
            
            # Generate timelapse video
            _LOGGER.info("Starting timelapse generation from %d frames", frame_count)
            media_url = await self._generate_timelapse(frame_dir, output_file)
            
            # Add media URL for frontend playback if available
            if media_url:
                self._timelapse_data[camera_entity_id]["media_url"] = media_url
                
                # Update task registry
                if task_id in self._task_registry:
                    self._task_registry[task_id]["media_url"] = media_url
                
                # 如果启用了 Google Photos 上传，上传视频
                if self._upload_to_google_photos:
                    success = await self._upload_to_google_photos(output_file, task_id)
                    if success:
                        self._timelapse_data[camera_entity_id]["google_photos_uploaded"] = True
                        
                        # Update task registry
                        if task_id in self._task_registry:
                            self._task_registry[task_id]["google_photos_uploaded"] = True
            
            # Update status to completed
            self._timelapse_data[camera_entity_id]["status"] = STATUS_IDLE
            self._timelapse_data[camera_entity_id]["progress"] = 100
            self._timelapse_data[camera_entity_id]["time_remaining"] = 0
            
            # Update task registry
            if task_id in self._task_registry:
                self._task_registry[task_id]["status"] = STATUS_IDLE
                self._task_registry[task_id]["progress"] = 100
                self._task_registry[task_id]["time_remaining"] = 0
                
            _LOGGER.info("Timelapse processing complete for %s", camera_entity_id)
            
            # Log successful completion
            _LOGGER.info("Timelapse completed and saved to: %s", output_file)
            
            self.async_set_updated_data(self._timelapse_data)
            
        except asyncio.CancelledError:
            _LOGGER.debug("Timelapse canceled for %s", camera_entity_id)
            # Note: We don't raise here anymore to prevent propagation
            # The stop_timelapse method now handles video generation
            
        except Exception as e:
            _LOGGER.error("Error in timelapse: %s", e)
            _LOGGER.exception("Detailed timelapse error information")
            self._timelapse_data[camera_entity_id]["status"] = STATUS_ERROR
            self._timelapse_data[camera_entity_id]["error_message"] = str(e)
            
            # Update task registry
            if task_id in self._task_registry:
                self._task_registry[task_id]["status"] = STATUS_ERROR
                self._task_registry[task_id]["error_message"] = str(e)
                
            self.async_set_updated_data(self._timelapse_data)
    
    async def _generate_timelapse(self, frame_dir: str, output_file: str, cleanup_frames: bool = True) -> str:
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
            
            # 优化视频生成，限制使用资源
            # 确保帧按顺序排列
            frame_files = sorted(frame_files)
            first_frame = os.path.join(frame_dir, frame_files[0]) if frame_files else None
            
            if first_frame and os.path.exists(first_frame):
                _LOGGER.info("First frame exists: %s", first_frame)
                
                # 使用绝对路径
                output_file = os.path.abspath(output_file)
                frame_pattern = os.path.abspath(os.path.join(frame_dir, "frame_%06d.jpg"))
                
                _LOGGER.info("Output will be saved to: %s", output_file)
                _LOGGER.info("Using frame pattern: %s", frame_pattern)
                
                # 优化ffmpeg命令，提高兼容性和质量
                cmd = [
                    ffmpeg_path,
                    "-y",  # 覆盖现有文件
                    "-framerate", "10",  # 输入帧率
                    "-i", frame_pattern,  # 输入模式
                    "-c:v", "libx264",  # 视频编码器
                    "-preset", "medium",  # 使用更平衡的预设，提高兼容性
                    "-crf", "23",  # 使用更好的质量，提高兼容性
                    "-threads", str(MAX_FFMPEG_THREADS),  # 限制线程数，使用配置常量
                    "-pix_fmt", "yuv420p",  # 像素格式
                    "-movflags", "+faststart",  # 优化网络播放
                    "-profile:v", "high",  # 使用高配置文件提高兼容性
                    "-level", "4.0",  # 提高级别
                    "-metadata", f"creation_time={datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}",  # 添加创建时间元数据
                    "-metadata", "encoder=Home Assistant Camera Timelapse",  # 添加编码器信息
                    output_file
                ]
            else:
                _LOGGER.warning("Cannot find first frame, falling back to concat method")
                
                # 方法2：使用concat方法和显式文件列表
                input_list_path = os.path.join(frame_dir, "input_list.txt")
                
                # 使用异步IO写入文件列表，减少阻塞
                try:
                    # 使用配置常量限制帧数，避免内存问题
                    max_files = min(len(frame_files), MAX_FRAME_BATCH)
                    if len(frame_files) > max_files:
                        _LOGGER.warning("Too many frames (%d), limiting to %d frames", len(frame_files), max_files)
                        # 使用均匀采样，确保覆盖整个时间段
                        if max_files > 1:
                            step = len(frame_files) / max_files
                            frame_files = [frame_files[int(i * step)] for i in range(max_files)]
                        else:
                            frame_files = [frame_files[0]]
                    
                    async with aiofiles.open(input_list_path, "w") as f:
                        for frame in frame_files:
                            full_path = os.path.join(frame_dir, frame)
                            await f.write(f"file '{os.path.abspath(full_path)}'\n")
                    _LOGGER.info("Created input file list at %s with %d entries", input_list_path, len(frame_files))
                except Exception as e:
                    _LOGGER.error("Error creating input file list: %s", e)
                    raise HomeAssistantError(f"Error creating input file list: {str(e)}")
                
                # 优化ffmpeg命令，提高兼容性和质量
                cmd = [
                    ffmpeg_path,
                    "-y",  # 覆盖现有文件
                    "-f", "concat",
                    "-safe", "0",
                    "-i", input_list_path,
                    "-c:v", "libx264",  # 视频编码器
                    "-preset", "medium",  # 使用更平衡的预设，提高兼容性
                    "-crf", "23",  # 使用更好的质量，提高兼容性
                    "-threads", str(MAX_FFMPEG_THREADS),  # 使用配置常量限制线程数
                    "-pix_fmt", "yuv420p",  # 像素格式
                    "-r", "10",  # 输出帧率
                    "-movflags", "+faststart",  # 优化网络播放
                    "-profile:v", "high",  # 使用高配置文件提高兼容性
                    "-level", "4.0",  # 提高级别
                    "-metadata", f"creation_time={datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}",  # 添加创建时间元数据
                    "-metadata", "encoder=Home Assistant Camera Timelapse",  # 添加编码器信息
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
                                # Copy the file to media directory as fallback (使用异步IO来减少阻塞)
                                fallback_path = f"/media/local/timelapses/{filename}"
                                await self.to_thread(os.makedirs, os.path.dirname(fallback_path), exist_ok=True)
                                
                                _LOGGER.info("Copying file to media directory: %s", fallback_path)
                                try:
                                    # 使用异步拷贝提高性能，避免阻塞主线程
                                    async def async_copy_file(src, dst):
                                        async with aiofiles.open(src, 'rb') as fsrc:
                                            content = await fsrc.read()
                                            async with aiofiles.open(dst, 'wb') as fdst:
                                                await fdst.write(content)
                                    
                                    # 如果文件过大，可能需要限制内存使用
                                    file_size = os.path.getsize(output_file)
                                    if file_size > 50 * 1024 * 1024:  # 超过50MB时使用不同的拷贝方法
                                        _LOGGER.info("Large file detected (%d MB), using chunked copy", file_size/1024/1024)
                                        # 对于大文件，使用子进程进行复制，避免阻塞
                                        import shutil
                                        await self.to_thread(shutil.copy2, output_file, fallback_path)
                                    else:
                                        # 对于小文件，使用异步IO
                                        await async_copy_file(output_file, fallback_path)
                                    
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
                                
                                # 优化清理过程，避免阻塞主线程
                                if cleanup_frames:
                                    try:
                                        _LOGGER.info("Cleaning up temporary frame files in %s", frame_dir)
                                        
                                        # 使用异步批量操作，减少IO压力
                                        async def async_cleanup():
                                            # 使用列表推导更高效地获取文件列表
                                            frame_files = [f for f in await self.to_thread(os.listdir, frame_dir) 
                                                          if f.startswith("frame_") and f.endswith(".jpg")]
                                            
                                            # 批量删除文件，每批最多100个文件
                                            batch_size = 100
                                            for i in range(0, len(frame_files), batch_size):
                                                batch = frame_files[i:i+batch_size]
                                                delete_tasks = []
                                                for frame in batch:
                                                    file_path = os.path.join(frame_dir, frame)
                                                    delete_tasks.append(self.to_thread(os.remove, file_path))
                                                
                                                # 并行执行删除操作
                                                if delete_tasks:
                                                    await asyncio.gather(*delete_tasks)
                                            
                                            # 删除输入列表文件
                                            input_list_path = os.path.join(frame_dir, "input_list.txt")
                                            if await self.to_thread(os.path.exists, input_list_path):
                                                await self.to_thread(os.remove, input_list_path)
                                                
                                            # 尝试删除空目录
                                            try:
                                                await self.to_thread(os.rmdir, frame_dir)
                                                _LOGGER.info("Removed empty frame directory %s", frame_dir)
                                            except OSError:
                                                _LOGGER.warning("Could not remove frame directory %s, it may not be empty", frame_dir)
                                        
                                        # 执行异步清理
                                        await async_cleanup()
                                        
                                    except Exception as cleanup_err:
                                        _LOGGER.warning("Error cleaning up frame files: %s", cleanup_err)
                                
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
    
    async def _to_thread_compat(self, func, *args, **kwargs):
        """兼容Python 3.8的to_thread实现."""
        loop = asyncio.get_event_loop()
        func_call = partial(func, *args, **kwargs)
        return await loop.run_in_executor(None, func_call)
    
    async def _upload_to_google_photos(self, output_file: str, task_id: Optional[str] = None) -> bool:
        """上传视频到 Google Photos.
        
        Args:
            output_file: 视频文件路径
            task_id: 可选的任务ID
            
        Returns:
            成功时返回True，否则返回False
        """
        if not self._upload_to_google_photos:
            _LOGGER.debug("Google Photos upload not enabled")
            return False
            
        try:
            _LOGGER.info("Uploading timelapse to Google Photos: %s", output_file)
            
            # 更新状态为上传中
            camera_entity_id = None
            for entity_id, data in self._timelapse_data.items():
                if data.get("output_file") == output_file:
                    data["status"] = STATUS_UPLOADING
                    camera_entity_id = entity_id
                    if not task_id:
                        task_id = data.get("task_id")
                    break
                    
            if task_id and task_id in self._task_registry:
                self._task_registry[task_id]["status"] = STATUS_UPLOADING
                self._task_registry[task_id]["progress"] = 97  # 上传状态
            
            self.async_set_updated_data(self._timelapse_data)
            
            # 使用官方集成上传视频
            success = await async_upload_to_google_photos(
                self.hass,
                output_file, 
                self._google_photos_album,
                self._google_photos_config_entry_id
            )
            
            if success:
                _LOGGER.info("Successfully uploaded to Google Photos")
                
                # 更新状态
                if camera_entity_id and camera_entity_id in self._timelapse_data:
                    self._timelapse_data[camera_entity_id]["google_photos_uploaded"] = True
                    self._timelapse_data[camera_entity_id]["status"] = STATUS_IDLE
                    
                if task_id and task_id in self._task_registry:
                    self._task_registry[task_id]["google_photos_uploaded"] = True
                    self._task_registry[task_id]["status"] = STATUS_IDLE
                    
                self.async_set_updated_data(self._timelapse_data)
                return True
            else:
                _LOGGER.error("Failed to upload to Google Photos")
                
                # 更新状态
                if camera_entity_id and camera_entity_id in self._timelapse_data:
                    self._timelapse_data[camera_entity_id]["status"] = STATUS_IDLE
                    self._timelapse_data[camera_entity_id]["error_message"] = "Failed to upload to Google Photos"
                    
                if task_id and task_id in self._task_registry:
                    self._task_registry[task_id]["status"] = STATUS_IDLE
                    self._task_registry[task_id]["error_message"] = "Failed to upload to Google Photos"
                
                self.async_set_updated_data(self._timelapse_data)
                return False
                
        except Exception as upload_err:
            _LOGGER.error("Error uploading to Google Photos: %s", upload_err)
            _LOGGER.exception("Detailed upload error information")
            
            # 更新状态
            if camera_entity_id and camera_entity_id in self._timelapse_data:
                self._timelapse_data[camera_entity_id]["status"] = STATUS_IDLE
                self._timelapse_data[camera_entity_id]["error_message"] = f"Google Photos upload error: {str(upload_err)}"
                
            if task_id and task_id in self._task_registry:
                self._task_registry[task_id]["status"] = STATUS_IDLE
                self._task_registry[task_id]["error_message"] = f"Google Photos upload error: {str(upload_err)}"
            
            self.async_set_updated_data(self._timelapse_data)
            return False
    
    async def async_shutdown(self) -> None:
        """Cancel any active timelapse tasks."""
        for entity_id, task in self._timelapse_tasks.items():
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                    
    async def delete_task(self, task_id: str) -> None:
        """Delete a task from the registry."""
        if task_id not in self._task_registry:
            _LOGGER.error("Task ID %s does not exist", task_id)
            raise HomeAssistantError(f"Task ID {task_id} does not exist")
            
        # If the task is active, stop it first
        camera_entity_id = self._task_registry[task_id].get("camera_entity_id")
        if camera_entity_id and camera_entity_id in self._timelapse_tasks:
            if not self._timelapse_tasks[camera_entity_id].done():
                await self.stop_timelapse(camera_entity_id, task_id)
        
        # Remove from registry
        del self._task_registry[task_id]
        await self.async_request_refresh()