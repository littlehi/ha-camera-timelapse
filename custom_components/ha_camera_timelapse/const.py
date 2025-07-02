"""Constants for the Camera Timelapse integration."""

DOMAIN = "ha_camera_timelapse"

# Services
SERVICE_START_TIMELAPSE = "start_timelapse"
SERVICE_STOP_TIMELAPSE = "stop_timelapse"

# Service attributes
ATTR_ENTITY_ID = "entity_id"
ATTR_INTERVAL = "interval"
ATTR_DURATION = "duration"
ATTR_OUTPUT_PATH = "output_path"

# Config flow attributes
CONF_CAMERA_ENTITY_ID = "camera_entity_id"
CONF_DEFAULT_INTERVAL = "default_interval"
CONF_DEFAULT_DURATION = "default_duration"
CONF_DEFAULT_OUTPUT_PATH = "default_output_path"

# Default values
DEFAULT_INTERVAL = 60  # seconds
DEFAULT_DURATION = 1440  # minutes (24 hours)
DEFAULT_OUTPUT_PATH = "/config/timelapses"
DEFAULT_DEBUG = False  # Enable debug mode

# Entity attributes
ATTR_STATUS = "status"
ATTR_PROGRESS = "progress"
ATTR_FRAMES_CAPTURED = "frames_captured"
ATTR_TIME_REMAINING = "time_remaining"
ATTR_OUTPUT_FILE = "output_file"

# Status values
STATUS_IDLE = "idle"
STATUS_RECORDING = "recording"
STATUS_PROCESSING = "processing"
STATUS_ERROR = "error"