"""Constants for the Camera Timelapse integration."""

DOMAIN = "ha_camera_timelapse"

# Services
SERVICE_START_TIMELAPSE = "start_timelapse"
SERVICE_STOP_TIMELAPSE = "stop_timelapse"
SERVICE_LIST_TASKS = "list_tasks"

# Service attributes
ATTR_ENTITY_ID = "entity_id"
ATTR_INTERVAL = "interval"
ATTR_DURATION = "duration"
ATTR_OUTPUT_PATH = "output_path"
ATTR_TASK_ID = "task_id"

# Config flow attributes
CONF_CAMERA_ENTITY_ID = "camera_entity_id"
CONF_DEFAULT_INTERVAL = "default_interval"
CONF_DEFAULT_DURATION = "default_duration"
CONF_DEFAULT_OUTPUT_PATH = "default_output_path"
CONF_DEBUG_MODE = "debug_mode"

# Default values
DEFAULT_INTERVAL = 60  # seconds
DEFAULT_DURATION = 1440  # minutes (24 hours)
DEFAULT_OUTPUT_PATH = "/media/local/timelapses"  # Media directory for HA frontend access
DEFAULT_DEBUG = False  # Enable debug mode

# Performance settings
MAX_CONCURRENT_TASKS = 2  # 最大并发延时摄影任务数
MAX_FRAME_BATCH = 1000  # 最大处理帧数量限制
MAX_FFMPEG_THREADS = 2  # FFmpeg线程数限制

# Entity attributes
ATTR_STATUS = "status"
ATTR_PROGRESS = "progress"
ATTR_FRAMES_CAPTURED = "frames_captured"
ATTR_TIME_REMAINING = "time_remaining"
ATTR_OUTPUT_FILE = "output_file"
ATTR_MEDIA_URL = "media_url"
ATTR_ERROR_MESSAGE = "error_message"
ATTR_TASKS = "tasks"

# Status values
STATUS_IDLE = "idle"
STATUS_RECORDING = "recording"
STATUS_PROCESSING = "processing"
STATUS_UPLOADING = "uploading"
STATUS_ERROR = "error"

# Google Photos settings
CONF_UPLOAD_TO_GOOGLE_PHOTOS = "upload_to_google_photos"
CONF_GOOGLE_PHOTOS_ALBUM = "google_photos_album"
DEFAULT_UPLOAD_TO_GOOGLE_PHOTOS = False
DEFAULT_GOOGLE_PHOTOS_ALBUM = "Home Assistant Timelapses"