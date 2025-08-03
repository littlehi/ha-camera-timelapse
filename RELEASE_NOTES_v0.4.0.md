# Release Notes v0.4.0 - State Change Trigger Mode

## 🎯 Major New Feature: State Change Trigger Mode

This release introduces a powerful new way to capture timelapse frames - **State Change Trigger Mode**! Now you can capture frames based on entity state changes instead of just fixed time intervals.

### ✨ What's New

#### 🔄 Dual Trigger Modes
- **Interval Mode** (Original): Capture frames at fixed time intervals
- **State Change Mode** (NEW): Capture frames when specified entity states change

#### 🎛️ Enhanced Configuration
- New trigger mode selector in configuration UI
- Entity selector for choosing trigger entities
- Seamless integration with existing settings

#### 🏠 Perfect for Smart Home Integration
- **Motion Detection**: Capture when motion sensors trigger
- **Door/Window Monitoring**: Record when doors/windows open/close  
- **Environmental Changes**: Capture on temperature/humidity changes
- **Device State Monitoring**: Record when switches/devices change state

### 🔧 How It Works

1. **Configure**: Choose your trigger mode and trigger entity in settings
2. **Start**: Turn on the timelapse switch (same as before!)
3. **Capture**: Frames are captured based on your chosen trigger mode
4. **Stop**: Turn off the switch to generate your timelapse video

### 📋 Usage Examples

#### Motion-Triggered Security Monitoring
```yaml
# Configuration
Trigger Mode: State Change
Trigger Entity: binary_sensor.front_door_motion
Duration: 2 hours
```

#### Plant Growth with Light Changes
```yaml  
# Configuration
Trigger Mode: State Change
Trigger Entity: sensor.plant_light_level
Duration: 12 hours
```

#### Traditional Time-lapse (Unchanged)
```yaml
# Configuration  
Trigger Mode: Interval
Interval: 60 seconds
Duration: 24 hours
```

### 🔄 Backward Compatibility

- **100% backward compatible** with existing configurations
- Existing timelapses will continue to work exactly as before
- Default mode is "Interval" to maintain current behavior
- All existing features and settings preserved

### 🛠️ Technical Improvements

- Efficient state change monitoring using Home Assistant's event system
- Automatic cleanup of state listeners to prevent memory leaks
- Enhanced error handling and logging
- Improved resource management

### 📊 Enhanced Switch Entity

The timelapse switch now displays additional information:
- Current trigger mode (interval/state_change)
- Trigger entity ID (for state change mode)
- Real-time frame count updates
- Enhanced status reporting

## 🚀 Installation & Upgrade

### New Installation
1. Install via HACS or manually
2. Add the integration through Home Assistant UI
3. Configure your camera and trigger preferences

### Upgrading from Previous Versions
1. Update through HACS or replace files manually
2. Restart Home Assistant
3. Your existing configurations will work unchanged
4. Optionally reconfigure to use new trigger modes

## 📚 Documentation

- [Detailed Feature Guide](STATE_CHANGE_TRIGGER_FEATURE.md)
- [Usage Examples](USAGE_EXAMPLES.md)
- [Implementation Details](IMPLEMENTATION_SUMMARY.md)
- [Workflow Diagram](WORKFLOW_DIAGRAM.md)

## 🐛 Bug Fixes & Improvements

- Enhanced state monitoring reliability
- Improved error handling for edge cases
- Better resource cleanup on task cancellation
- More detailed logging for troubleshooting

## 🔮 What's Next

This release lays the foundation for even more advanced triggering capabilities:
- Multiple trigger entities
- Complex trigger conditions
- Time-based trigger constraints
- Advanced filtering options

## 💬 Feedback & Support

- [GitHub Issues](https://github.com/littlehi/ha-camera-timelapse/issues)
- [Discussions](https://github.com/littlehi/ha-camera-timelapse/discussions)

## 🙏 Acknowledgments

Thanks to the Home Assistant community for feature requests and feedback that made this release possible!

---

**Full Changelog**: [v0.3.2...v0.4.0](https://github.com/littlehi/ha-camera-timelapse/compare/v0.3.2...v0.4.0)