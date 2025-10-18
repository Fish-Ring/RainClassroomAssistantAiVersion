#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试数学计算题的准确性
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scai import get_answer, is_math_problem

# 测试配置
test_config = {
    "ai_config": {
        "api_key": "",  # 请替换为您的API密钥
        "base_url": "https://api.siliconflow.cn/v1",
        "model": "deepseek-ai/DeepSeek-V3.2-Exp"
    }
}

def test_complex_math_calculations():
    """测试复杂数学计算题答题功能"""
    print("=== 测试复杂数学计算题答题功能 ===")
    
    # 初始化AI客户端
    from scai import init_ai_client
    init_ai_client(test_config)
    
    test_cases = [
        # 基础四则运算
        {
            "text": "25+17=?",
            "options": ["40", "41", "42", "43"],
            "type": "选择题",
            "expected": "C"
        },
        {
            "text": "100-37=?",
            "options": ["61", "62", "63", "64"],
            "type": "选择题",
            "expected": "C"
        },
        {
            "text": "15×8=?",
            "options": ["110", "115", "120", "125"],
            "type": "选择题",
            "expected": "C"
        },
        {
            "text": "144÷12=?",
            "options": ["10", "11", "12", "13"],
            "type": "选择题",
            "expected": "C"
        },
        # 小数运算
        {
            "text": "3.5+2.7=?",
            "options": ["6.1", "6.2", "6.3", "6.4"],
            "type": "选择题",
            "expected": "B"
        },
        {
            "text": "10.8-3.2=?",
            "options": ["7.5", "7.6", "7.7", "7.8"],
            "type": "选择题",
            "expected": "B"
        },
        {
            "text": "2.5×4=?",
            "options": ["9", "9.5", "10", "10.5"],
            "type": "选择题",
            "expected": "C"
        },
        {
            "text": "15.6÷3=?",
            "options": ["5.1", "5.2", "5.3", "5.4"],
            "type": "选择题",
            "expected": "B"
        },
        # 分数运算
        {
            "text": "1/2+1/3=?",
            "options": ["3/6", "4/6", "5/6", "6/6"],
            "type": "选择题",
            "expected": "C"
        },
        {
            "text": "3/4-1/2=?",
            "options": ["1/2", "1/3", "1/4", "1/5"],
            "type": "选择题",
            "expected": "C"
        },
        {
            "text": "2/3×3/4=?",
            "options": ["1/2", "1/3", "1/4", "1/5"],
            "type": "选择题",
            "expected": "A"
        },
        {
            "text": "3/4÷1/2=?",
            "options": ["1", "1.5", "2", "2.5"],
            "type": "选择题",
            "expected": "B"
        },
        # 百分数运算
        {
            "text": "25%+40%=?",
            "options": ["60%", "65%", "70%", "75%"],
            "type": "选择题",
            "expected": "B"
        },
        {
            "text": "80%-35%=?",
            "options": ["40%", "45%", "50%", "55%"],
            "type": "选择题",
            "expected": "B"
        },
        {
            "text": "20%×150=?",
            "options": ["20", "25", "30", "35"],
            "type": "选择题",
            "expected": "C"
        },
        {
            "text": "50÷25%=?",
            "options": ["100", "150", "200", "250"],
            "type": "选择题",
            "expected": "C"
        },
        # 混合运算
        {
            "text": "5+3×2=?",
            "options": ["11", "16", "21", "26"],
            "type": "选择题",
            "expected": "A"
        },
        {
            "text": "(5+3)×2=?",
            "options": ["11", "16", "21", "26"],
            "type": "选择题",
            "expected": "B"
        },
        {
            "text": "10-6÷2=?",
            "options": ["5", "6", "7", "8"],
            "type": "选择题",
            "expected": "C"
        },
        {
            "text": "(10-6)÷2=?",
            "options": ["1", "2", "3", "4"],
            "type": "选择题",
            "expected": "B"
        },
        # 填空题
        {
            "text": "7×8=____",
            "options": None,
            "type": "填空题",
            "expected": "56",
            "blanks": [{"answers": ["56"]}]
        },
        {
            "text": "9²=____",
            "options": None,
            "type": "填空题",
            "expected": "81",
            "blanks": [{"answers": ["81"]}]
        },
        {
            "text": "√64=____",
            "options": None,
            "type": "填空题",
            "expected": "8",
            "blanks": [{"answers": ["8"]}]
        },
        {
            "text": "3.14×2²=____",
            "options": None,
            "type": "填空题",
            "expected": "12.56",
            "blanks": [{"answers": ["12.56"]}]
        }
    ]
    
    correct_count = 0
    total_count = len(test_cases)
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n测试案例 {i}: {case['text']}")
        if case['options']:
            print(f"选项: {case['options']}")
        
        try:
            # 构建符合scai.py期望的题目信息结构
            question_info = {
                "title": case['text'],
                "type": 1 if case['options'] else 2,  # 1: 选择题, 2: 填空题
                "options": case['options'],
                "blanks": case.get('blanks', [])
            }
            
            # 使用get_answer函数获取答案
            answer = get_answer(question_info)
            print(f"AI答案: {answer}")
            
            if answer and len(answer) > 0:
                if case['options']:  # 选择题
                    if answer[0] == case['expected']:
                        print("✓ 答案正确")
                        correct_count += 1
                    else:
                        print(f"✗ 答案错误，期望: {case['expected']}")
                else:  # 填空题
                    if str(answer[0]) == case['expected']:
                        print("✓ 答案正确")
                        correct_count += 1
                    else:
                        print(f"✗ 答案错误，期望: {case['expected']}")
            else:
                print("✗ 未获取到有效答案")
        except Exception as e:
            print(f"✗ 测试失败: {e}")
    
    print(f"\n=== 测试结果统计 ===")
    print(f"总题数: {total_count}")
    print(f"正确数: {correct_count}")
    print(f"正确率: {correct_count/total_count*100:.1f}%")
    
    return correct_count, total_count

if __name__ == "__main__":
    print("开始测试数学计算题的准确性...\n")
    
    # 测试复杂数学计算题
    correct_count, total_count = test_complex_math_calculations()
    
    print("\n测试完成！")