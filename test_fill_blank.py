#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试填空题AI回答功能
"""

import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scai import get_answer

def test_fill_blank():
    """测试填空题"""
    # 测试1: 简单填空题
    question_info1 = {
        "title": "中国的首都是____。",
        "type": 2,  # 填空题
        "options": [],
        "blanks": []
    }
    
    print("测试1: 简单填空题")
    print(f"题目: {question_info1['title']}")
    result1 = get_answer(question_info1)
    print(f"答案: {result1}")
    print()
    
    # 测试2: 多空填空题
    question_info2 = {
        "title": "中国的首都是____，人口最多的城市是____。",
        "type": 2,  # 填空题
        "options": [],
        "blanks": []
    }
    
    print("测试2: 多空填空题")
    print(f"题目: {question_info2['title']}")
    result2 = get_answer(question_info2)
    print(f"答案: {result2}")
    print()
    
    # 测试3: 带选项的填空题（应该是选择题）
    question_info3 = {
        "title": "中国的首都是____。",
        "type": 2,  # 填空题
        "options": ["北京", "上海", "广州", "深圳"],
        "blanks": []
    }
    
    print("测试3: 带选项的填空题（应该是选择题）")
    print(f"题目: {question_info3['title']}")
    print(f"选项: {question_info3['options']}")
    result3 = get_answer(question_info3)
    print(f"答案: {result3}")
    print()
    
    # 测试4: 选择题
    question_info4 = {
        "title": "中国的首都是____。",
        "type": 1,  # 选择题
        "options": ["北京", "上海", "广州", "深圳"],
        "blanks": []
    }
    
    print("测试4: 选择题")
    print(f"题目: {question_info4['title']}")
    print(f"选项: {question_info4['options']}")
    result4 = get_answer(question_info4)
    print(f"答案: {result4}")
    print()

if __name__ == "__main__":
    test_fill_blank()