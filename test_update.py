#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试更新功能
"""

import sys
import os

# 添加项目根目录到系统路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from Scripts.Update import Update, get_version

def test_update():
    print("测试更新功能")
    print("=" * 50)
    
    # 测试获取当前版本
    current_version = get_version()
    print(f"当前版本: {current_version}")
    
    # 测试更新类
    update = Update("./")
    print(f"更新URL: {update.url}")
    
    # 测试获取最新版本
    try:
        latest_version = update.get_latest_version()
        print(f"最新版本: {latest_version}")
        
        # 检查是否有新版本
        has_new_version = update.have_new_version(latest_version)
        print(f"是否有新版本: {has_new_version}")
    except Exception as e:
        print(f"获取最新版本失败: {e}")
    
    print("=" * 50)
    print("测试完成")

if __name__ == "__main__":
    test_update()