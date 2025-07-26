# Camera Timelapse for Home Assistant

A Home Assistant custom component that creates timelapse videos from camera entities with Google Photos integration and smart storage management.

## ✨ Features

### Core Functionality
- 📹 Create timelapse videos from any camera entity
- ⏯️ Full control over timelapse process (start/stop/monitor)
- ⚙️ Configurable parameters (interval, duration, output path)
- 📊 Real-time progress tracking and status monitoring

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
   - **Default Interval**: Time between captures (seconds)
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
| `interval` | integer | Capture interval in seconds (optional, default: 60) |
| `duration` | integer | Total timelapse duration in minutes (optional, default: 1440 - 24 hours) |
| `output_path` | string | Where to save the timelapse file (optional) |

### `ha_camera_timelapse.stop_timelapse`

Stops the current timelapse recording.

| Parameter | Type | Description |
|-----------|------|-------------|
| `entity_id` | string | The timelapse entity to stop |