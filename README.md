# Camera Timelapse for Home Assistant

A Home Assistant custom component that creates timelapse videos from camera entities with Google Photos integration and smart storage management.

## ✨ Features

### Core Functionality
- 📹 Create timelapse videos from any camera entity
- ⏯️ Full control over timelapse process (start/stop/monitor)
- ⚙️ Configurable parameters (interval, duration, output path)
- 📊 Real-time progress tracking and status monitoring
- 🎯 **NEW**: State change trigger mode - capture frames when entity states change

### Google Photos Integration
- ☁️ Automatic upload to Google Photos
- 📁 Custom album organization
- 🔄 Multiple account support
- 🛡️ Robust error handling and retry logic

### Smart Storage Management
- 🗑️ **NEW**: Auto-delete local files after successful upload
- 💾 Configurable storage behavior
- 📈 File size tracking and logging
- 🔒 Safe deletion with permission checks

### User Experience
- 🌐 Multi-language support (English/Chinese)
- 🎛️ Easy configuration through Home Assistant UI
- 📝 Detailed logging and troubleshooting
- 🔄 Task management and history

## Installation

### HACS (Recommended)

1. Make sure [HACS](https://hacs.xyz/) is installed in your Home Assistant instance
2. Add this repository to HACS as a custom repository:
   - HACS → Integrations → Three dots in top right → Custom repositories
   - URL: `https://github.com/yourusername/ha-camera-timelapse`
   - Category: Integration
3. Click "Download" on the Camera Timelapse integration
4. Restart Home Assistant

### Manual Installation

1. Download the latest release from GitHub
2. Extract the contents to your Home Assistant `custom_components` directory
3. Restart Home Assistant

## Configuration

### Initial Setup

1. Go to Home Assistant Settings → Devices & Services
2. Click "Add Integration" and search for "Camera Timelapse"
3. Select your camera entity and configure default settings:
   - **Camera Entity**: Choose the camera to use for timelapses
   - **Trigger Mode**: Choose between "固定时间间隔" (interval) or "实体状态变化" (state change)
   - **Trigger Entity**: Entity whose state changes trigger frame capture (for state change mode)
   - **Default Interval**: Time between captures in seconds (for interval mode)
   - **Default Duration**: How long to record (minutes)
   - **Default Output Path**: Where to save videos
   - **Debug Mode**: Enable detailed logging

### Google Photos Setup (Optional)

4. Configure Google Photos integration:
   - **Upload to Google Photos**: Enable automatic upload
   - **Google Photos Album**: Specify album name (default: "Home Assistant Timelapses")
   - **Google Photos Account**: Select which account to use (if multiple)
   - **Delete after upload**: 🆕 Remove local files after successful upload

### Advanced Options

You can modify these settings anytime by going to the integration options:
- Settings → Devices & Services → Camera Timelapse → Configure

## Usage

Once configured, you can:
- Start a timelapse via the service `ha_camera_timelapse.start_timelapse`
- Stop a timelapse via the service `ha_camera_timelapse.stop_timelapse`
- View timelapse status in the entity attributes

## Services

### `ha_camera_timelapse.start_timelapse`

Starts recording a timelapse from the selected camera.

| Parameter | Type | Description |
|-----------|------|-------------|
| `entity_id` | string | The camera entity to use for the timelapse |
| `trigger_mode` | string | Trigger mode: "interval" or "state_change" (optional, default: "interval") |
| `trigger_entity_id` | string | Entity whose state changes trigger capture (required for state_change mode) |
| `interval` | integer | Capture interval in seconds (optional, default: 60, for interval mode) |
| `duration` | integer | Total timelapse duration in minutes (optional, default: 1440 - 24 hours) |
| `output_path` | string | Where to save the timelapse file (optional) |

### `ha_camera_timelapse.stop_timelapse`

Stops the current timelapse recording.

| Parameter | Type | Description |
|-----------|------|-------------|
| `entity_id` | string | The timelapse entity to stop |

## 🎯 New Feature: State Change Trigger Mode

**Important**: Timelapse recording is still controlled by the switch entity. The new feature only changes HOW frames are captured, not how the timelapse is started.

The integration now supports two trigger modes for frame capture:

### 1. Interval Mode (Original)
- Captures frames at fixed time intervals
- Perfect for regular time-based recordings
- Example: Every 60 seconds for 24 hours

### 2. State Change Mode (New)
- Captures frames when specified entity state changes
- Event-driven timelapse creation
- Perfect for motion detection, door sensors, temperature changes, etc.

### How it works:
1. **Configure** the trigger mode and trigger entity in the integration settings
2. **Start** the timelapse by turning ON the switch entity
3. **Capture** frames based on your configured trigger mode:
   - Interval mode: captures every N seconds
   - State change mode: captures when the trigger entity state changes
4. **Stop** the timelapse by turning OFF the switch entity

#### Example Usage:

**Method 1: Using the Switch (Recommended)**
1. Configure trigger mode in integration settings:
   - Trigger Mode: "实体状态变化" (State Change)
   - Trigger Entity: `binary_sensor.front_door_motion`
2. Turn on the switch: `switch.timelapse_front_door`
3. The timelapse will capture frames when motion is detected
4. Turn off the switch to stop and generate video

**Method 2: Using Service Calls**
```yaml
# Motion-triggered timelapse
service: ha_camera_timelapse.start_timelapse
data:
  entity_id: camera.front_door
  trigger_mode: state_change
  trigger_entity_id: binary_sensor.front_door_motion
  duration: 120  # 2 hours

# Temperature change timelapse
service: ha_camera_timelapse.start_timelapse
data:
  entity_id: camera.garden
  trigger_mode: state_change
  trigger_entity_id: sensor.outdoor_temperature
  duration: 480  # 8 hours
```

For more examples and advanced usage, see [USAGE_EXAMPLES.md](USAGE_EXAMPLES.md) and [STATE_CHANGE_TRIGGER_FEATURE.md](STATE_CHANGE_TRIGGER_FEATURE.md).