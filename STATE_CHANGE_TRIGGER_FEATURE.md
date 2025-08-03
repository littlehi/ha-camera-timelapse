# 状态变化触发延时摄影功能

## 功能概述

这个新功能为 Home Assistant 摄像头延时摄影集成添加了基于实体状态变化的触发模式。除了原有的固定时间间隔模式外，现在可以选择在指定实体状态发生变化时自动捕获图像帧。

## 功能特性

### 两种触发模式

1. **固定时间间隔模式** (`interval`)
   - 原有功能，按固定时间间隔捕获图像
   - 适用于需要定期记录的场景

2. **实体状态变化模式** (`state_change`) - **新功能**
   - 当指定实体状态发生变化时自动捕获图像
   - 适用于事件驱动的延时摄影场景

### 使用场景示例

- **门窗传感器触发**: 每当门窗开关时捕获一帧
- **运动检测触发**: 检测到运动时记录图像
- **温度变化触发**: 温度传感器数值变化时拍照
- **开关状态触发**: 灯光或设备开关状态改变时记录

## 配置方法

### 1. 通过配置界面

在 Home Assistant 的集成配置界面中：

1. 选择**触发模式**:
   - `固定时间间隔`: 传统的定时拍摄模式
   - `实体状态变化`: 新的状态变化触发模式

2. 如果选择状态变化模式，需要指定**触发实体**:
   - 可以是任何 Home Assistant 实体（传感器、开关、二进制传感器等）

3. 设置**持续时间**: 延时摄影的总时长（分钟）

### 2. 通过服务调用

#### 状态变化模式服务调用示例

```yaml
service: ha_camera_timelapse.start_timelapse
data:
  entity_id: camera.front_door
  trigger_mode: state_change
  trigger_entity_id: binary_sensor.front_door_motion
  duration: 120  # 2小时
  output_path: /media/local/timelapses
```

#### 固定间隔模式服务调用示例

```yaml
service: ha_camera_timelapse.start_timelapse
data:
  entity_id: camera.garden
  trigger_mode: interval
  interval: 60  # 60秒间隔
  duration: 1440  # 24小时
  output_path: /media/local/timelapses
```

## 技术实现

### 核心组件

1. **状态监听器**: 使用 `async_track_state_change_event` 监听实体状态变化
2. **帧捕获逻辑**: 状态变化时异步捕获单帧图像
3. **资源管理**: 自动清理状态监听器，避免内存泄漏

### 新增配置项

- `CONF_TRIGGER_MODE`: 触发模式配置
- `CONF_TRIGGER_ENTITY_ID`: 触发实体ID配置
- `TRIGGER_MODE_INTERVAL`: 间隔模式常量
- `TRIGGER_MODE_STATE_CHANGE`: 状态变化模式常量

### 服务参数

- `trigger_mode`: 触发模式 (`interval` 或 `state_change`)
- `trigger_entity_id`: 触发实体ID（状态变化模式必需）

## 监控和调试

### 实体属性

延时摄影开关实体会显示以下新属性：

- `trigger_mode`: 当前使用的触发模式
- `trigger_entity_id`: 触发实体ID（如果适用）
- `frames_captured`: 已捕获的帧数

### 日志信息

- 状态变化检测和帧捕获会记录在日志中
- 支持调试模式以获取详细信息

## 注意事项

1. **状态变化频率**: 如果触发实体状态变化过于频繁，可能会产生大量图像帧
2. **存储空间**: 确保有足够的存储空间来保存捕获的图像
3. **性能影响**: 频繁的状态变化可能会影响系统性能
4. **实体选择**: 选择合适的触发实体，避免不必要的触发

## 兼容性

- 完全向后兼容原有的固定间隔模式
- 支持所有现有的配置选项和功能
- 可以与 Google Photos 上传功能配合使用

## 故障排除

### 常见问题

1. **状态变化未触发拍摄**
   - 检查触发实体ID是否正确
   - 确认实体状态确实发生了变化
   - 查看日志中的错误信息

2. **拍摄频率过高**
   - 考虑更换触发实体
   - 或者回到固定间隔模式

3. **图像质量问题**
   - 检查摄像头连接状态
   - 确认摄像头实体可用

### 调试步骤

1. 启用调试模式
2. 查看 Home Assistant 日志
3. 检查触发实体的状态历史
4. 验证摄像头实体的可用性

## 更新说明

此功能是对现有延时摄影集成的增强，不会影响现有配置和功能。用户可以选择继续使用原有的固定间隔模式，或者尝试新的状态变化触发模式。