# Camera Timelapse for Home Assistant

A Home Assistant custom component that creates timelapse videos from camera entities.

## Features

- Select any camera entity to create a timelapse
- Control the timelapse creation process (start/stop)
- Configure timelapse parameters (interval, duration, etc.)

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

1. Go to Home Assistant Settings → Devices & Services
2. Click "Add Integration" and search for "Camera Timelapse"
3. Follow the on-screen instructions to set up your timelapse

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