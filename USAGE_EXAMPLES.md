# 状态变化触发延时摄影使用示例

## 场景1: 门口监控 - 有人经过时拍照

当门口的运动传感器检测到有人经过时，自动拍摄一张照片。

### 自动化配置

```yaml
automation:
  - alias: "门口延时摄影"
    trigger:
      - platform: state
        entity_id: binary_sensor.front_door_motion
        to: "on"
    action:
      - service: ha_camera_timelapse.start_timelapse
        data:
          entity_id: camera.front_door
          trigger_mode: state_change
          trigger_entity_id: binary_sensor.front_door_motion
          duration: 60  # 1小时监控
```

## 场景2: 植物生长记录 - 光照变化触发

当光照传感器数值发生变化时（比如日出日落），记录植物的生长状态。

### 服务调用

```yaml
service: ha_camera_timelapse.start_timelapse
data:
  entity_id: camera.plant_monitor
  trigger_mode: state_change
  trigger_entity_id: sensor.plant_light_level
  duration: 720  # 12小时
  output_path: /media/local/plant_growth
```

## 场景3: 温度变化记录

当温度传感器读数变化时，记录环境状态。

### 配置界面设置

1. 进入 Home Assistant 设置
2. 选择"设备与服务"
3. 找到"Camera Timelapse"集成
4. 点击"配置"
5. 设置以下参数：
   - 触发模式: `实体状态变化`
   - 触发实体: `sensor.room_temperature`
   - 默认持续时间: `480` (8小时)

## 场景4: 开关状态监控

监控重要设备的开关状态变化。

### Node-RED 流程

```json
[
    {
        "id": "switch_monitor",
        "type": "api-call-service",
        "name": "开关状态延时摄影",
        "server": "home_assistant",
        "version": 3,
        "service_domain": "ha_camera_timelapse",
        "service": "start_timelapse",
        "entityId": "",
        "data": {
            "entity_id": "camera.security_cam",
            "trigger_mode": "state_change", 
            "trigger_entity_id": "switch.main_power",
            "duration": 1440
        }
    }
]
```

## 场景5: 多传感器组合触发

使用模板传感器组合多个触发条件。

### 模板传感器配置

```yaml
template:
  - sensor:
      - name: "综合活动检测"
        state: >
          {% if is_state('binary_sensor.motion_1', 'on') or 
                is_state('binary_sensor.motion_2', 'on') or
                is_state('binary_sensor.door_sensor', 'on') %}
            active
          {% else %}
            inactive
          {% endif %}
```

### 延时摄影配置

```yaml
service: ha_camera_timelapse.start_timelapse
data:
  entity_id: camera.overview
  trigger_mode: state_change
  trigger_entity_id: sensor.comprehensive_activity_detection
  duration: 180  # 3小时
```

## 场景6: 定时与状态变化混合使用

在不同时间段使用不同的触发模式。

### 白天使用状态变化模式

```yaml
automation:
  - alias: "白天状态变化延时摄影"
    trigger:
      - platform: time
        at: "08:00:00"
    condition:
      - condition: sun
        after: sunrise
    action:
      - service: ha_camera_timelapse.start_timelapse
        data:
          entity_id: camera.garden
          trigger_mode: state_change
          trigger_entity_id: binary_sensor.garden_motion
          duration: 600  # 10小时
```

### 夜间使用固定间隔模式

```yaml
automation:
  - alias: "夜间固定间隔延时摄影"
    trigger:
      - platform: time
        at: "20:00:00"
    condition:
      - condition: sun
        after: sunset
    action:
      - service: ha_camera_timelapse.start_timelapse
        data:
          entity_id: camera.garden
          trigger_mode: interval
          interval: 300  # 5分钟间隔
          duration: 600  # 10小时
```

## 高级配置技巧

### 1. 防止过度触发

使用辅助实体来控制触发频率：

```yaml
input_boolean:
  timelapse_cooldown:
    name: "延时摄影冷却"
    initial: false

automation:
  - alias: "防过度触发延时摄影"
    trigger:
      - platform: state
        entity_id: sensor.trigger_sensor
    condition:
      - condition: state
        entity_id: input_boolean.timelapse_cooldown
        state: "off"
    action:
      - service: input_boolean.turn_on
        target:
          entity_id: input_boolean.timelapse_cooldown
      - service: ha_camera_timelapse.start_timelapse
        data:
          entity_id: camera.test
          trigger_mode: state_change
          trigger_entity_id: sensor.trigger_sensor
          duration: 30
      - delay: "00:05:00"  # 5分钟冷却
      - service: input_boolean.turn_off
        target:
          entity_id: input_boolean.timelapse_cooldown
```

### 2. 条件触发

只在特定条件下启动延时摄影：

```yaml
automation:
  - alias: "条件延时摄影"
    trigger:
      - platform: state
        entity_id: binary_sensor.motion_detector
        to: "on"
    condition:
      - condition: time
        after: "22:00:00"
        before: "06:00:00"
      - condition: state
        entity_id: alarm_control_panel.home
        state: "armed_night"
    action:
      - service: ha_camera_timelapse.start_timelapse
        data:
          entity_id: camera.security
          trigger_mode: state_change
          trigger_entity_id: binary_sensor.motion_detector
          duration: 120
```

### 3. 动态参数配置

使用输入助手动态配置参数：

```yaml
input_select:
  timelapse_trigger_entity:
    name: "延时摄影触发实体"
    options:
      - sensor.temperature
      - binary_sensor.motion
      - switch.light
    initial: sensor.temperature

input_number:
  timelapse_duration:
    name: "延时摄影持续时间"
    min: 30
    max: 1440
    step: 30
    unit_of_measurement: "分钟"

automation:
  - alias: "动态延时摄影"
    trigger:
      - platform: state
        entity_id: input_boolean.start_timelapse
        to: "on"
    action:
      - service: ha_camera_timelapse.start_timelapse
        data:
          entity_id: camera.dynamic
          trigger_mode: state_change
          trigger_entity_id: "{{ states('input_select.timelapse_trigger_entity') }}"
          duration: "{{ states('input_number.timelapse_duration') | int }}"
```

## 监控和通知

### 延时摄影完成通知

```yaml
automation:
  - alias: "延时摄影完成通知"
    trigger:
      - platform: state
        entity_id: switch.timelapse_camera
        attribute: status
        to: "idle"
    condition:
      - condition: template
        value_template: "{{ trigger.from_state.attributes.status == 'processing' }}"
    action:
      - service: notify.mobile_app
        data:
          title: "延时摄影完成"
          message: >
            摄像头 {{ trigger.entity_id }} 的延时摄影已完成。
            共捕获 {{ state_attr(trigger.entity_id, 'frames_captured') }} 帧图像。
            触发模式: {{ state_attr(trigger.entity_id, 'trigger_mode') }}
```

这些示例展示了状态变化触发延时摄影功能的各种使用方法，可以根据具体需求进行调整和组合。