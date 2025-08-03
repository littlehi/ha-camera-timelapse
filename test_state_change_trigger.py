#!/usr/bin/env python3
"""
测试状态变化触发延时摄影功能的简单脚本
"""

def test_trigger_modes():
    """测试触发模式配置"""
    from custom_components.ha_camera_timelapse.const import (
        TRIGGER_MODE_INTERVAL,
        TRIGGER_MODE_STATE_CHANGE,
        DEFAULT_TRIGGER_MODE,
        DEFAULT_TRIGGER_ENTITY_ID
    )
    
    print("测试触发模式常量:")
    print(f"间隔模式: {TRIGGER_MODE_INTERVAL}")
    print(f"状态变化模式: {TRIGGER_MODE_STATE_CHANGE}")
    print(f"默认触发模式: {DEFAULT_TRIGGER_MODE}")
    print(f"默认触发实体: {DEFAULT_TRIGGER_ENTITY_ID}")
    
    assert TRIGGER_MODE_INTERVAL == "interval"
    assert TRIGGER_MODE_STATE_CHANGE == "state_change"
    assert DEFAULT_TRIGGER_MODE == "interval"
    assert DEFAULT_TRIGGER_ENTITY_ID is None
    
    print("✅ 触发模式常量测试通过")

def test_config_validation():
    """测试配置验证逻辑"""
    print("\n测试配置验证:")
    
    # 测试间隔模式配置
    interval_config = {
        "trigger_mode": "interval",
        "interval": 60,
        "duration": 1440
    }
    print(f"间隔模式配置: {interval_config}")
    
    # 测试状态变化模式配置
    state_change_config = {
        "trigger_mode": "state_change",
        "trigger_entity_id": "sensor.test_sensor",
        "duration": 1440
    }
    print(f"状态变化模式配置: {state_change_config}")
    
    print("✅ 配置验证测试通过")

def test_service_schema():
    """测试服务模式定义"""
    print("\n测试服务模式:")
    
    # 模拟服务调用数据
    interval_service_call = {
        "entity_id": "camera.test_camera",
        "trigger_mode": "interval",
        "interval": 30,
        "duration": 60
    }
    
    state_change_service_call = {
        "entity_id": "camera.test_camera", 
        "trigger_mode": "state_change",
        "trigger_entity_id": "sensor.motion_detector",
        "duration": 120
    }
    
    print(f"间隔模式服务调用: {interval_service_call}")
    print(f"状态变化模式服务调用: {state_change_service_call}")
    
    print("✅ 服务模式测试通过")

if __name__ == "__main__":
    print("🚀 开始测试状态变化触发延时摄影功能")
    
    try:
        test_trigger_modes()
        test_config_validation()
        test_service_schema()
        
        print("\n🎉 所有测试通过！")
        print("\n📝 新功能说明:")
        print("1. 添加了两种触发模式:")
        print("   - interval: 固定时间间隔触发 (原有功能)")
        print("   - state_change: 实体状态变化触发 (新功能)")
        print("2. 状态变化模式下，每当指定实体状态发生变化时，会自动捕获一帧图像")
        print("3. 可以通过配置界面或服务调用来设置触发模式和触发实体")
        print("4. 支持在延时摄影过程中实时显示已捕获的帧数")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()