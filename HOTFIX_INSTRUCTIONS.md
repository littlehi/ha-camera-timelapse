# 🚨 状态变化触发问题热修复

## 问题描述
用户选择了状态变化触发模式，但实际运行时仍按时间间隔捕获图片。

## 调试步骤

### 1. 检查日志
重启 Home Assistant 后，查看日志中的以下信息：
```
=== Trigger Mode Configuration Debug ===
From options: trigger_mode=..., trigger_entity_id=...
From data: trigger_mode=..., trigger_entity_id=...
Final values: trigger_mode=..., trigger_entity_id=...
```

### 2. 验证配置
开启延时摄影开关时，应该看到：
```
=== Switch Turn On Debug ===
Camera entity: camera.xxx
Coordinator trigger_mode: state_change
Coordinator trigger_entity_id: sensor.xxx
```

### 3. 确认触发模式
如果触发模式正确，应该看到：
```
Setting up state change listener for entity: sensor.xxx
State change mode: waiting for X minutes or until stopped
```

## 临时解决方案

如果配置读取有问题，可以临时硬编码触发模式进行测试：

### 方案1: 强制状态变化模式
在 `coordinator.py` 的 `__init__` 方法中，临时添加：
```python
# 临时强制使用状态变化模式
self._trigger_mode = TRIGGER_MODE_STATE_CHANGE
self._trigger_entity_id = "binary_sensor.motion_detector"  # 替换为你的实体ID
```

### 方案2: 在开关中强制设置
在 `switch.py` 的 `async_turn_on` 方法中：
```python
await self.coordinator.start_timelapse(
    camera_entity_id=self._camera_entity_id,
    trigger_mode="state_change",  # 强制使用状态变化模式
    trigger_entity_id="binary_sensor.motion_detector"  # 替换为你的实体ID
)
```

## 根本原因分析

可能的原因：
1. **配置保存问题**: 触发模式没有正确保存到配置中
2. **配置读取问题**: 协调器没有正确读取配置
3. **默认值覆盖**: 默认值覆盖了用户设置
4. **常量不匹配**: 配置界面和代码中的常量值不一致

## 永久修复方案

### 1. 配置存储统一
确保初始配置和选项配置都使用相同的存储方式。

### 2. 配置读取优化
改进配置读取逻辑，确保正确的优先级。

### 3. 配置验证
添加配置验证，确保无效值被正确处理。

### 4. 用户界面改进
在开关实体属性中显示当前的触发模式，方便用户确认。

## 测试步骤

1. 应用修复
2. 重启 Home Assistant
3. 检查日志中的调试信息
4. 开启延时摄影开关
5. 触发状态变化（如运动检测）
6. 确认是否捕获了图片
7. 检查日志中是否有状态变化事件

## 回滚方案

如果修复导致问题，可以：
1. 移除调试日志
2. 恢复原始的配置读取逻辑
3. 重启 Home Assistant

---

**注意**: 这是一个调试版本，包含大量日志输出。修复问题后应该移除调试日志。