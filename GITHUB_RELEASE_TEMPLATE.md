# 🎯 v0.4.0 - State Change Trigger Mode

## 🚀 Major New Feature

Introducing **State Change Trigger Mode** - a revolutionary way to create timelapses based on real-world events instead of just time intervals!

### ✨ What's New

🔄 **Dual Trigger Modes**
- **Interval Mode**: Traditional time-based capture (unchanged)
- **State Change Mode**: Event-driven capture (NEW!)

🎛️ **Smart Home Integration**
- Motion sensor triggers
- Door/window state monitoring  
- Environmental change detection
- Device state tracking

🏠 **Perfect Use Cases**
- Security monitoring with motion detection
- Plant growth tracking with light sensors
- Weather change documentation
- Home automation event recording

### 🔧 How to Use

1. **Configure** your trigger mode in the integration settings
2. **Start** the timelapse using the switch (same as always!)
3. **Capture** frames automatically based on your chosen trigger
4. **Stop** and enjoy your event-driven timelapse video

### 📊 Example Configurations

**Motion-Triggered Security**
```
Trigger Mode: State Change
Trigger Entity: binary_sensor.motion_detector
Result: Captures only when motion is detected
```

**Traditional Time-lapse** (unchanged)
```
Trigger Mode: Interval  
Interval: 60 seconds
Result: Captures every minute
```

### 🔄 Backward Compatibility

✅ **100% compatible** with existing setups  
✅ **No breaking changes**  
✅ **Existing timelapses work unchanged**  
✅ **Default behavior preserved**

### 📚 Documentation

- [📖 Feature Guide](https://github.com/littlehi/ha-camera-timelapse/blob/main/STATE_CHANGE_TRIGGER_FEATURE.md)
- [💡 Usage Examples](https://github.com/littlehi/ha-camera-timelapse/blob/main/USAGE_EXAMPLES.md)
- [🔧 Implementation Details](https://github.com/littlehi/ha-camera-timelapse/blob/main/IMPLEMENTATION_SUMMARY.md)

### 🛠️ Installation

**Via HACS (Recommended)**
1. Update through HACS
2. Restart Home Assistant
3. Enjoy the new features!

**Manual Installation**
1. Download the latest release
2. Extract to `custom_components/ha_camera_timelapse/`
3. Restart Home Assistant

### 🐛 Bug Fixes

- Enhanced state monitoring reliability
- Improved error handling
- Better resource cleanup
- More detailed logging

---

**Full Changelog**: https://github.com/littlehi/ha-camera-timelapse/blob/main/CHANGELOG.md

## 💬 Support

- 🐛 [Report Issues](https://github.com/littlehi/ha-camera-timelapse/issues)
- 💭 [Discussions](https://github.com/littlehi/ha-camera-timelapse/discussions)
- 📖 [Documentation](https://github.com/littlehi/ha-camera-timelapse/blob/main/README.md)

## 🙏 Thanks

Special thanks to the Home Assistant community for the feature requests and feedback that made this release possible!