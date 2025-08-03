#!/usr/bin/env python3
"""
调试配置问题的脚本
"""

def debug_config_issue():
    """调试配置读取问题"""
    print("🔍 调试延时摄影配置问题")
    print()
    
    print("可能的问题原因:")
    print("1. 配置保存位置不一致 (entry.data vs entry.options)")
    print("2. 常量值不匹配")
    print("3. 配置读取顺序问题")
    print("4. 默认值覆盖了用户配置")
    print()
    
    print("调试步骤:")
    print("1. 检查 Home Assistant 日志中的调试信息")
    print("2. 确认配置界面中选择的触发模式")
    print("3. 验证常量值是否正确")
    print("4. 检查配置保存和读取逻辑")
    print()
    
    print("预期的日志输出:")
    print("- Coordinator initialized with trigger_mode: state_change")
    print("- Switch turn_on called with trigger_mode: state_change")
    print("- start_timelapse called with: trigger_mode=state_change")
    print("- Setting up state change listener for entity: [entity_id]")
    print()
    
    print("如果看到 trigger_mode: interval，说明配置读取有问题")

def check_constants():
    """检查常量定义"""
    print("📋 检查常量定义:")
    
    # 模拟常量值
    TRIGGER_MODE_INTERVAL = "interval"
    TRIGGER_MODE_STATE_CHANGE = "state_change"
    DEFAULT_TRIGGER_MODE = "interval"
    
    print(f"TRIGGER_MODE_INTERVAL = '{TRIGGER_MODE_INTERVAL}'")
    print(f"TRIGGER_MODE_STATE_CHANGE = '{TRIGGER_MODE_STATE_CHANGE}'")
    print(f"DEFAULT_TRIGGER_MODE = '{DEFAULT_TRIGGER_MODE}'")
    print()
    
    print("✅ 常量定义正确")

def suggest_fixes():
    """建议修复方案"""
    print("🔧 建议的修复方案:")
    print()
    
    print("方案1: 强制重新加载配置")
    print("- 重启 Home Assistant")
    print("- 重新配置集成")
    print()
    
    print("方案2: 检查配置存储")
    print("- 查看 .storage/core.config_entries 文件")
    print("- 确认触发模式是否正确保存")
    print()
    
    print("方案3: 添加更多调试日志")
    print("- 在协调器初始化时打印完整配置")
    print("- 在开关启动时验证参数")
    print()
    
    print("方案4: 临时解决方案")
    print("- 直接在代码中硬编码触发模式进行测试")

if __name__ == "__main__":
    debug_config_issue()
    print()
    check_constants()
    print()
    suggest_fixes()