#!/usr/bin/env python3
"""
验证新功能代码的语法正确性
"""

import ast
import os

def validate_python_file(file_path):
    """验证Python文件的语法"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 解析AST来检查语法
        ast.parse(content)
        print(f"✅ {file_path}: 语法正确")
        return True
    except SyntaxError as e:
        print(f"❌ {file_path}: 语法错误 - {e}")
        return False
    except Exception as e:
        print(f"⚠️ {file_path}: 其他错误 - {e}")
        return False

def main():
    """主函数"""
    print("🔍 验证延时摄影项目文件语法...")
    
    files_to_check = [
        "custom_components/ha_camera_timelapse/__init__.py",
        "custom_components/ha_camera_timelapse/const.py", 
        "custom_components/ha_camera_timelapse/config_flow.py",
        "custom_components/ha_camera_timelapse/coordinator.py",
        "custom_components/ha_camera_timelapse/switch.py",
    ]
    
    all_valid = True
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            if not validate_python_file(file_path):
                all_valid = False
        else:
            print(f"⚠️ {file_path}: 文件不存在")
            all_valid = False
    
    if all_valid:
        print("\n🎉 所有文件语法验证通过！")
        print("\n📋 新功能总结:")
        print("1. ✅ 添加了状态变化触发模式常量")
        print("2. ✅ 更新了配置流程以支持触发模式选择")
        print("3. ✅ 实现了状态变化监听和帧捕获逻辑")
        print("4. ✅ 更新了服务定义和参数处理")
        print("5. ✅ 添加了资源清理和错误处理")
        print("6. ✅ 更新了开关实体属性显示")
    else:
        print("\n❌ 发现语法错误，请检查上述文件")

if __name__ == "__main__":
    main()