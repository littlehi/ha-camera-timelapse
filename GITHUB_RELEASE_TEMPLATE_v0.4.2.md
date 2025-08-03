# 🎯 v0.4.2 - Intelligent State Change Filtering

## 🧠 Smart State Change Detection

This release adds **intelligent filtering** for state change triggers, ensuring frames are only captured when state values actually change.

### 🔧 What's New

**Intelligent State Change Filtering**
- Only triggers when state **values** actually change, not just events
- Ignores changes to `unknown` or `unavailable` states
- Supports numeric value change detection
- Prevents unnecessary captures from duplicate events

### 🎯 The Problem We Solved

Previously, any state change event would trigger frame capture, even if:
- The value remained the same (`on` → `on`)
- Sensor went offline (`23.5` → `unknown`)
- Duplicate events fired with identical values

This caused unnecessary frame captures and wasted storage.

### ✅ The Solution

Smart filtering logic that checks:

1. **Value Actually Changed**: `old_value != new_value`
2. **Valid State**: Ignores changes to `unknown`/`unavailable`
3. **Numeric Precision**: Proper handling of numeric sensors
4. **State Recovery**: Triggers when sensors come back online

### 📊 Examples

#### ✅ Will Trigger Frame Capture
```
Motion Sensor: off → on (motion detected)
Door Sensor: closed → open (door opened)
Temperature: 23.5 → 24.1 (temperature changed)
Recovery: unknown → on (sensor back online)
```

#### ⏸️ Will Skip Frame Capture
```
Duplicate: on → on (same value)
Offline: on → unknown (sensor offline)
No Change: 23.5 → 23.5 (temperature unchanged)
Still Offline: unknown → unavailable (still invalid)
```

### 🧪 Real-World Impact

**Motion Detection Timelapse**:
- Before: Captures every motion event (including duplicates)
- After: Only captures when motion starts/stops

**Temperature Monitoring**:
- Before: Captures when sensor reports same temperature
- After: Only captures when temperature actually changes

**Door/Window Monitoring**:
- Before: Multiple captures for same door state
- After: Only captures when door opens/closes

### 🔍 Enhanced Logging

Debug logs now show filtering decisions:

```
State value changed from 'off' to 'on', triggering frame capture
State change detected but value unchanged (on -> on), skipping frame capture
Numeric change detected: 23.5 -> 24.1 (change: 0.6)
```

### 🚀 Update Instructions

**Via HACS:**
1. HACS → Integrations → Camera Timelapse → Update
2. Restart Home Assistant

**Manual:**
1. Download the release
2. Replace files in `custom_components/ha_camera_timelapse/`
3. Restart Home Assistant

### 🔄 Backward Compatibility

- ✅ No breaking changes
- ✅ Existing configurations work unchanged
- ✅ Interval mode unaffected
- ✅ All previous features preserved

### 📚 Documentation

- [State Change Filtering Guide](STATE_CHANGE_FILTERING.md)
- [Feature Documentation](STATE_CHANGE_TRIGGER_FEATURE.md)
- [Usage Examples](USAGE_EXAMPLES.md)

### 🧪 Testing Your Setup

1. Configure state change mode with a sensor
2. Turn on timelapse
3. Trigger the sensor multiple times quickly
4. Verify only meaningful changes capture frames
5. Check logs for filtering decisions

---

**Download**: [ha-camera-timelapse-v0.4.2.zip](../../releases/download/v0.4.2/ha-camera-timelapse-v0.4.2.zip)

**Full Changelog**: [v0.4.1...v0.4.2](../../compare/v0.4.1...v0.4.2)

## 💬 Support

- 🐛 [Report Issues](../../issues)
- 💭 [Discussions](../../discussions)
- 📖 [Documentation](../../blob/main/README.md)

This makes state change triggers much more efficient and practical! 🎯