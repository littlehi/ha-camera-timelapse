#!/usr/bin/env python3
"""
测试状态变化过滤逻辑
"""

def test_is_significant_change():
    """测试状态变化是否显著的判断逻辑"""
    
    def _is_significant_change(old_value: str, new_value: str) -> bool:
        """模拟协调器中的方法"""
        # 基本检查：值是否相同
        if old_value == new_value:
            return False
        
        # 检查是否为 "unknown" 或 "unavailable" 状态
        if new_value in ["unknown", "unavailable", "None", None]:
            return False
            
        if old_value in ["unknown", "unavailable", "None", None]:
            return True
        
        # 对于数值类型，检查变化
        try:
            old_num = float(old_value)
            new_num = float(new_value)
            
            min_threshold = 0.0
            change = abs(new_num - old_num)
            
            if change <= min_threshold:
                return False
                
            return True
            
        except (ValueError, TypeError):
            # 非数值类型，只要值不同就认为是有效变化
            return True
    
    print("🧪 测试状态变化过滤逻辑")
    print("=" * 50)
    
    test_cases = [
        # (old_value, new_value, expected, description)
        ("on", "on", False, "相同值 - 不应触发"),
        ("off", "on", True, "二进制传感器变化 - 应触发"),
        ("20.5", "20.5", False, "相同数值 - 不应触发"),
        ("20.5", "21.0", True, "数值变化 - 应触发"),
        ("unknown", "on", True, "从未知到已知 - 应触发"),
        ("on", "unknown", False, "变为未知状态 - 不应触发"),
        ("unavailable", "off", True, "从不可用到可用 - 应触发"),
        ("25.3", "unavailable", False, "变为不可用 - 不应触发"),
        ("open", "closed", True, "门窗状态变化 - 应触发"),
        ("home", "away", True, "位置状态变化 - 应触发"),
        ("", "motion", True, "空值到有值 - 应触发"),
        ("motion", "", True, "有值到空值 - 应触发"),
    ]
    
    passed = 0
    failed = 0
    
    for old_val, new_val, expected, desc in test_cases:
        result = _is_significant_change(old_val, new_val)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        
        if result == expected:
            passed += 1
        else:
            failed += 1
            
        print(f"{status} | '{old_val}' -> '{new_val}' | {desc}")
    
    print("=" * 50)
    print(f"测试结果: {passed} 通过, {failed} 失败")
    
    if failed == 0:
        print("🎉 所有测试通过！")
    else:
        print("⚠️ 有测试失败，需要检查逻辑")

def test_real_world_scenarios():
    """测试真实世界的场景"""
    print("\n🌍 真实场景测试")
    print("=" * 50)
    
    scenarios = [
        {
            "name": "运动传感器",
            "changes": [
                ("off", "on", "检测到运动"),
                ("on", "on", "运动持续（重复事件）"),
                ("on", "off", "运动结束"),
            ]
        },
        {
            "name": "温度传感器",
            "changes": [
                ("23.5", "23.5", "温度无变化"),
                ("23.5", "24.1", "温度上升"),
                ("24.1", "unknown", "传感器离线"),
                ("unknown", "23.8", "传感器恢复"),
            ]
        },
        {
            "name": "门窗传感器",
            "changes": [
                ("closed", "open", "门打开"),
                ("open", "open", "门保持打开"),
                ("open", "closed", "门关闭"),
            ]
        }
    ]
    
    def _is_significant_change(old_value: str, new_value: str) -> bool:
        if old_value == new_value:
            return False
        if new_value in ["unknown", "unavailable", "None", None]:
            return False
        if old_value in ["unknown", "unavailable", "None", None]:
            return True
        try:
            old_num = float(old_value)
            new_num = float(new_value)
            return abs(new_num - old_num) > 0.0
        except (ValueError, TypeError):
            return True
    
    for scenario in scenarios:
        print(f"\n📊 {scenario['name']}:")
        for old_val, new_val, desc in scenario['changes']:
            should_trigger = _is_significant_change(old_val, new_val)
            trigger_text = "🔥 触发拍照" if should_trigger else "⏸️ 跳过"
            print(f"  {trigger_text} | '{old_val}' -> '{new_val}' | {desc}")

if __name__ == "__main__":
    test_is_significant_change()
    test_real_world_scenarios()
    
    print("\n📝 改进说明:")
    print("1. 只有状态值真正改变时才触发拍照")
    print("2. 忽略到 unknown/unavailable 的变化")
    print("3. 支持数值类型的变化检测")
    print("4. 可扩展支持最小变化阈值")
    print("5. 详细的调试日志输出")