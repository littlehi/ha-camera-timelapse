# 🐛 v0.4.1 - Critical Bug Fix

## 🚨 Important Fix for State Change Trigger Mode

This hotfix release addresses a critical issue in v0.4.0 where **State Change Trigger Mode** was not working correctly.

### 🔧 What's Fixed

**State Change Trigger Not Working**
- Users who selected "State Change" mode were still getting interval-based captures
- Fixed configuration reading logic that was causing trigger mode to default to "interval"
- Added robust validation and fallback handling

### 🎯 The Problem

In v0.4.0, even when users configured:
```
Trigger Mode: 实体状态变化 (State Change)
Trigger Entity: binary_sensor.motion_detector
```

The system was still capturing frames every 60 seconds instead of on motion detection.

### ✅ The Solution

v0.4.1 fixes the configuration reading logic:
- Proper priority handling between initial config and options
- Enhanced validation for trigger mode values  
- Comprehensive debug logging for troubleshooting

### 🧪 How to Verify the Fix

After updating, check your Home Assistant logs for:

```
=== Trigger Mode Configuration Debug ===
Final values: trigger_mode=state_change, trigger_entity_id=sensor.motion
```

```
Setting up state change listener for entity: sensor.motion
State change mode: waiting for X minutes or until stopped
```

### 🚀 Update Instructions

**Via HACS:**
1. HACS → Integrations → Camera Timelapse → Update
2. Restart Home Assistant

**Manual:**
1. Download the release zip
2. Replace files in `custom_components/ha_camera_timelapse/`
3. Restart Home Assistant

### 🔄 No Breaking Changes

- ✅ Existing configurations preserved
- ✅ Interval mode works as before  
- ✅ All previous features intact
- ✅ 100% backward compatible

### 📋 Test Your Setup

1. Configure state change mode in integration settings
2. Turn on timelapse switch
3. Trigger your sensor (motion, door, etc.)
4. Verify frames are captured only on state changes

### 🆘 Still Having Issues?

If state change mode still doesn't work:
1. Check logs for debug messages
2. Try reconfiguring the integration
3. Report on GitHub with log details

---

**Download**: [ha-camera-timelapse-v0.4.1.zip](../../releases/download/v0.4.1/ha-camera-timelapse-v0.4.1.zip)

**Full Changelog**: [v0.4.0...v0.4.1](../../compare/v0.4.0...v0.4.1)

## 💬 Support

- 🐛 [Report Issues](../../issues)
- 💭 [Discussions](../../discussions)  
- 📖 [Documentation](../../blob/main/README.md)

Thanks for your patience with this critical fix! 🙏