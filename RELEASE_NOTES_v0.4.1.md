# Release Notes v0.4.1 - Bug Fix Release

## 🐛 Critical Bug Fix

This is a hotfix release to address a critical issue where the **State Change Trigger Mode** was not working correctly in v0.4.0.

### 🔧 Fixed Issues

#### State Change Trigger Not Working
- **Problem**: Users who selected "State Change" trigger mode found that timelapses were still capturing frames at fixed intervals instead of on entity state changes
- **Root Cause**: Configuration reading logic had incorrect priority handling between `entry.data` and `entry.options`
- **Solution**: Improved configuration reading with proper fallback logic and validation

#### Enhanced Debugging
- Added comprehensive debug logging to help diagnose configuration issues
- Improved error messages and validation for trigger mode settings
- Better logging for troubleshooting state change listener setup

### 🔍 What Was Fixed

```python
# Before (v0.4.0) - Could fail to read user configuration
self._trigger_mode = entry.options.get(CONF_TRIGGER_MODE, 
    entry.data.get(CONF_TRIGGER_MODE, DEFAULT_TRIGGER_MODE))

# After (v0.4.1) - Robust configuration reading
trigger_mode_from_options = entry.options.get(CONF_TRIGGER_MODE)
trigger_mode_from_data = entry.data.get(CONF_TRIGGER_MODE)
self._trigger_mode = trigger_mode_from_options or trigger_mode_from_data or DEFAULT_TRIGGER_MODE
```

### 📊 Verification Steps

After updating to v0.4.1, you should see these logs when starting a timelapse:

**Configuration Loading:**
```
=== Trigger Mode Configuration Debug ===
From options: trigger_mode=state_change, trigger_entity_id=sensor.motion
From data: trigger_mode=interval, trigger_entity_id=None  
Final values: trigger_mode=state_change, trigger_entity_id=sensor.motion
```

**Switch Activation:**
```
=== Switch Turn On Debug ===
Coordinator trigger_mode: state_change
Coordinator trigger_entity_id: sensor.motion
```

**State Change Mode Active:**
```
Setting up state change listener for entity: sensor.motion
State change mode: waiting for 60 minutes or until stopped
```

### 🚀 How to Update

#### Via HACS
1. Go to HACS → Integrations
2. Find "Camera Timelapse" 
3. Click "Update"
4. Restart Home Assistant

#### Manual Installation
1. Download the latest release
2. Replace files in `custom_components/ha_camera_timelapse/`
3. Restart Home Assistant

### 🔄 Backward Compatibility

- ✅ Fully compatible with existing configurations
- ✅ No breaking changes
- ✅ Interval mode continues to work as before
- ✅ All previous features preserved

### 🧪 Testing Your Setup

1. **Configure State Change Mode**:
   - Go to Settings → Devices & Services → Camera Timelapse → Configure
   - Select "实体状态变化" (State Change) as trigger mode
   - Choose your trigger entity (e.g., motion sensor)

2. **Start Timelapse**:
   - Turn on the timelapse switch
   - Check logs for "Setting up state change listener"

3. **Trigger State Change**:
   - Activate your trigger entity (e.g., trigger motion sensor)
   - Check logs for "State change detected, capturing frame"

4. **Verify Frame Capture**:
   - Frames should only be captured when the trigger entity state changes
   - No frames should be captured at fixed intervals

### 🆘 If You Still Have Issues

If state change mode still doesn't work after updating:

1. **Check the logs** for the debug messages above
2. **Try reconfiguring** the integration (remove and re-add)
3. **Report the issue** with log details on GitHub

### 📚 Documentation

- [State Change Feature Guide](STATE_CHANGE_TRIGGER_FEATURE.md)
- [Usage Examples](USAGE_EXAMPLES.md)
- [Troubleshooting Guide](HOTFIX_INSTRUCTIONS.md)

## 🙏 Thanks

Thanks to users who reported this issue quickly, allowing us to provide a fast fix!

---

**Important**: This release includes debug logging that will be removed in the next version once we confirm the fix works for all users.