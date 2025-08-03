# 状态变化触发延时摄影功能实现总结

## 功能概述

为 Home Assistant 摄像头延时摄影集成添加了基于实体状态变化的触发模式。**延时摄影任务的启动依然通过开关控制**，但现在用户可以在配置中选择两种图片捕获方式：
1. **固定时间间隔模式** (原有功能)：按设定的时间间隔捕获图片
2. **实体状态变化模式** (新增功能)：当指定实体状态发生变化时自动捕获图片

## 修改的文件

### 1. `custom_components/ha_camera_timelapse/const.py`
**新增常量:**
- `CONF_TRIGGER_MODE`: 触发模式配置键
- `CONF_TRIGGER_ENTITY_ID`: 触发实体ID配置键
- `ATTR_TRIGGER_MODE`: 触发模式属性
- `ATTR_TRIGGER_ENTITY_ID`: 触发实体ID属性
- `DEFAULT_TRIGGER_MODE`: 默认触发模式 ("interval")
- `DEFAULT_TRIGGER_ENTITY_ID`: 默认触发实体ID (None)
- `TRIGGER_MODE_INTERVAL`: 间隔模式常量 ("interval")
- `TRIGGER_MODE_STATE_CHANGE`: 状态变化模式常量 ("state_change")

### 2. `custom_components/ha_camera_timelapse/config_flow.py`
**修改内容:**
- 导入新的常量和触发模式
- 在配置表单中添加触发模式选择器
- 添加触发实体选择器
- 在选项流程中支持触发模式配置

**新增配置项:**
- 触发模式下拉选择 (固定时间间隔/实体状态变化)
- 触发实体选择器 (支持所有实体类型)

### 3. `custom_components/ha_camera_timelapse/coordinator.py`
**重大修改:**
- 添加状态监听器管理 (`_state_listeners`)
- 新增触发模式配置属性
- 实现状态变化监听器 (`_state_change_listener`)
- 实现单帧捕获方法 (`_capture_single_frame_on_state_change`)
- 重构帧捕获逻辑，分离间隔模式到独立方法 (`_capture_frames_interval_mode`)
- 修改 `start_timelapse` 方法支持新参数
- 修改 `_capture_timelapse` 方法支持两种触发模式
- 添加状态监听器清理方法 (`_cleanup_state_listener`)
- 添加协调器关闭方法 (`async_shutdown`)

**新增方法:**
- `_state_change_listener()`: 处理状态变化事件
- `_capture_single_frame_on_state_change()`: 状态变化时捕获单帧
- `_capture_frames_interval_mode()`: 间隔模式帧捕获
- `_cleanup_state_listener()`: 清理状态监听器
- `async_shutdown()`: 协调器关闭清理

### 4. `custom_components/ha_camera_timelapse/switch.py`
**修改内容:**
- 修改 `async_turn_on` 方法，使用配置中的触发模式和触发实体启动延时摄影
- 在实体属性中添加触发模式和触发实体ID显示
- 保持开关控制延时摄影启动/停止的原有方式

### 5. `custom_components/ha_camera_timelapse/services.yaml`
**修改内容:**
- 添加 `trigger_mode` 参数定义
- 添加 `trigger_entity_id` 参数定义
- 更新参数描述和示例

### 6. `custom_components/ha_camera_timelapse/__init__.py`
**修改内容:**
- 导入新的常量
- 更新服务处理函数支持新参数
- 更新服务注册模式定义

## 新增功能特性

### 1. 双触发模式支持
- **间隔模式**: 原有的固定时间间隔触发 (向后兼容)
- **状态变化模式**: 新的实体状态变化触发

### 2. 状态监听机制
- 使用 `async_track_state_change_event` 监听实体状态变化
- 异步处理状态变化事件
- 自动清理监听器防止内存泄漏

### 3. 智能帧捕获
- 状态变化时立即捕获单帧图像
- 支持任何类型的 Home Assistant 实体作为触发源
- 实时更新帧计数和进度

### 4. 资源管理
- 自动清理状态监听器
- 任务停止时清理相关资源
- 协调器关闭时清理所有资源

## 技术实现细节

### 状态变化监听
```python
listener = async_track_state_change_event(
    self.hass,
    [trigger_entity_id],
    partial(self._state_change_listener, task_id=task_id, camera_entity_id=camera_entity_id, frame_dir=frame_dir)
)
```

### 异步帧捕获
```python
@callback
def _state_change_listener(self, event: Event, task_id: str, camera_entity_id: str, frame_dir: str) -> None:
    self.hass.async_create_task(
        self._capture_single_frame_on_state_change(task_id, camera_entity_id, frame_dir)
    )
```

### 资源清理
```python
def _cleanup_state_listener(self, task_id: str) -> None:
    if task_id in self._state_listeners:
        self._state_listeners[task_id]()
        del self._state_listeners[task_id]
```

## 使用场景

**重要说明**: 所有场景下，延时摄影任务都是通过开关启动的，区别只在于图片捕获的触发方式。

### 1. 运动检测触发
- 配置触发实体: `binary_sensor.motion_detector`
- 用户开启开关 → 延时摄影开始 → 检测到运动时拍照

### 2. 门窗状态监控
- 配置触发实体: `binary_sensor.door_sensor`
- 用户开启开关 → 延时摄影开始 → 门窗开关时记录

### 3. 环境变化记录
- 配置触发实体: `sensor.temperature`
- 用户开启开关 → 延时摄影开始 → 温度变化时拍照

### 4. 设备状态监控
- 配置触发实体: `switch.device_power`
- 用户开启开关 → 延时摄影开始 → 设备开关状态变化时记录

## 向后兼容性

- 完全保持原有间隔模式功能
- 默认使用间隔模式，确保现有配置不受影响
- 所有原有参数和功能保持不变
- 新参数为可选参数

## 配置示例

### 配置界面
- 触发模式: 下拉选择 (固定时间间隔/实体状态变化)
- 触发实体: 实体选择器 (当选择状态变化模式时)

### 服务调用
```yaml
# 状态变化模式
service: ha_camera_timelapse.start_timelapse
data:
  entity_id: camera.test
  trigger_mode: state_change
  trigger_entity_id: binary_sensor.motion
  duration: 120

# 间隔模式 (原有功能)
service: ha_camera_timelapse.start_timelapse
data:
  entity_id: camera.test
  trigger_mode: interval
  interval: 60
  duration: 120
```

## 错误处理

### 1. 参数验证
- 状态变化模式必须提供 `trigger_entity_id`
- 实体ID有效性检查

### 2. 资源清理
- 任务停止时自动清理监听器
- 异常情况下的资源释放
- 协调器关闭时的完整清理

### 3. 日志记录
- 详细的调试信息
- 错误状态记录
- 性能监控日志

## 测试和验证

### 语法验证
- 所有修改的文件通过 Python AST 语法检查
- 导入依赖正确性验证

### 功能测试
- 创建了测试脚本验证常量定义
- 提供了使用示例和场景测试

## 文档更新

### 新增文档
- `STATE_CHANGE_TRIGGER_FEATURE.md`: 详细功能说明
- `USAGE_EXAMPLES.md`: 使用示例和场景
- `IMPLEMENTATION_SUMMARY.md`: 实现总结

### 更新文档
- `README.md`: 添加新功能介绍和使用说明

## 总结

这次实现成功为延时摄影集成添加了状态变化触发功能，提供了更灵活的帧捕获方式。实现保持了良好的向后兼容性，同时引入了强大的事件驱动延时摄影能力。代码结构清晰，错误处理完善，资源管理得当，为用户提供了更多样化的延时摄影解决方案。