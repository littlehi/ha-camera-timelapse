# 状态变化过滤改进

## 问题描述

在 v0.4.1 中，状态变化触发模式存在一个问题：只要实体有状态变化事件就会触发拍照，即使新值和旧值相同。这会导致不必要的图片捕获。

## 改进方案

### 🔍 智能状态变化检测

现在系统会检查状态值是否真正改变，只有在以下情况下才触发拍照：

1. **值确实改变**：新值与旧值不同
2. **有效状态**：忽略变为 `unknown` 或 `unavailable` 的变化
3. **数值变化**：支持数值类型的精确比较
4. **状态恢复**：从 `unknown`/`unavailable` 恢复到有效值时触发

### 📊 过滤逻辑

```python
def _is_significant_change(old_value: str, new_value: str) -> bool:
    # 1. 基本检查：值是否相同
    if old_value == new_value:
        return False
    
    # 2. 忽略变为无效状态
    if new_value in ["unknown", "unavailable", "None", None]:
        return False
        
    # 3. 从无效状态恢复
    if old_value in ["unknown", "unavailable", "None", None]:
        return True
    
    # 4. 数值类型检查
    try:
        old_num = float(old_value)
        new_num = float(new_value)
        return abs(new_num - old_num) > 0.0
    except (ValueError, TypeError):
        # 5. 非数值类型，值不同即触发
        return True
```

## 实际效果

### ✅ 会触发拍照的情况

- **运动传感器**: `off` → `on` (检测到运动)
- **门窗传感器**: `closed` → `open` (门打开)
- **温度传感器**: `23.5` → `24.1` (温度变化)
- **状态恢复**: `unknown` → `on` (传感器恢复)

### ⏸️ 不会触发拍照的情况

- **相同值**: `on` → `on` (重复事件)
- **数值相同**: `23.5` → `23.5` (温度无变化)
- **变为无效**: `on` → `unknown` (传感器离线)
- **保持无效**: `unavailable` → `unknown` (仍然无效)

## 使用场景优化

### 🏠 运动检测延时摄影
```
传感器状态变化:
off → on     ✅ 拍照 (检测到运动)
on → on      ⏸️ 跳过 (运动持续)
on → off     ✅ 拍照 (运动结束)
```

### 🌡️ 温度监控延时摄影
```
温度变化:
23.5 → 23.5    ⏸️ 跳过 (温度无变化)
23.5 → 24.1    ✅ 拍照 (温度上升)
24.1 → unknown ⏸️ 跳过 (传感器离线)
unknown → 23.8 ✅ 拍照 (传感器恢复)
```

### 🚪 门窗监控延时摄影
```
门窗状态:
closed → open   ✅ 拍照 (门打开)
open → open     ⏸️ 跳过 (门保持打开)
open → closed   ✅ 拍照 (门关闭)
```

## 调试信息

启用调试模式后，你会在日志中看到详细信息：

### 有效变化
```
State value changed from 'off' to 'on', triggering frame capture
State changed from 'off' to 'on', capturing frame 5 for camera.front_door
```

### 无效变化
```
State change detected but value unchanged (on -> on), skipping frame capture
State change detected but value unchanged or insignificant (23.5 -> unavailable), skipping frame capture
```

## 配置建议

### 运动传感器
- **推荐**: 使用二进制运动传感器 (`binary_sensor.motion`)
- **效果**: 只在运动开始和结束时拍照

### 温度传感器
- **推荐**: 使用精度适中的温度传感器
- **效果**: 温度真正变化时拍照

### 门窗传感器
- **推荐**: 使用门窗接触传感器 (`binary_sensor.door`)
- **效果**: 只在开关状态改变时拍照

## 扩展功能

### 数值变化阈值 (未来功能)
可以为数值类型传感器设置最小变化阈值：
```python
# 温度变化超过 0.5 度才触发
min_threshold = 0.5
if abs(new_num - old_num) <= min_threshold:
    return False
```

### 时间间隔限制 (未来功能)
可以设置最小触发间隔，避免过于频繁的拍照：
```python
# 最少间隔 30 秒
min_interval = 30  # seconds
if time.time() - last_trigger_time < min_interval:
    return False
```

## 总结

这个改进确保了状态变化触发模式只在真正有意义的状态变化时才拍照，避免了：

1. 重复事件导致的多余拍照
2. 传感器离线时的无效触发
3. 数值传感器的微小波动
4. 系统资源的浪费

现在的状态变化触发更加智能和高效！🎯