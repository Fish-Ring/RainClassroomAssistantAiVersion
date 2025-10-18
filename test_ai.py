#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
from scai import init_ai_client, get_answer

# 测试配置
test_config = {
    "ai_config": {
        "api_key": "",  # 请替换为您的API密钥
        "base_url": "https://api.siliconflow.cn/v1",
        "model": "deepseek-ai/DeepSeek-V3.2-Exp"
    }
}

def test_ai_answer():
    # 初始化AI客户端
    init_ai_client(test_config)
    
    # 测试选择题
    print("测试选择题：")
    choice_question = {
        "title": "2+2=?",
        "type": 1,
        "options": ["5", "4", "3", "7"],
        "blanks": []
    }
    choice_answer = get_answer(choice_question)
    print(f"题目：{choice_question['title']} {choice_question['options']}")
    print(f"AI答案：{choice_answer}")
    print(f"答案类型：{type(choice_answer)}")
    print()
    
    # 测试填空题
    print("测试填空题：")
    blank_question = {
        "title": "中国的首都是____。",
        "type": 3,
        "options": [],
        "blanks": []
    }
    blank_answer = get_answer(blank_question)
    print(f"题目：{blank_question['title']}")
    print(f"AI答案：{blank_answer}")
    print(f"答案类型：{type(blank_answer)}")
    print()
    
    # 测试多填空题
    print("测试多填空题：")
    multi_blank_question = {
        "title": "1+1=____，2+2=____。",
        "type": 3,
        "options": [],
        "blanks": []
    }
    multi_blank_answer = get_answer(multi_blank_question)
    print(f"题目：{multi_blank_question['title']}")
    print(f"AI答案：{multi_blank_answer}")
    print(f"答案类型：{type(multi_blank_answer)}")
    print()
    
    # 测试多选题
    print("测试多选题：")
    multi_choice_question = {
        "title": "以下哪些是正确的？",
        "type": 2,
        "options": ["地球是圆的", "太阳是恒星", "月亮是行星", "水是H2O"],
        "blanks": []
    }
    multi_choice_answer = get_answer(multi_choice_question)
    print(f"题目：{multi_choice_question['title']} {multi_choice_question['options']}")
    print(f"AI答案：{multi_choice_answer}")
    print(f"答案类型：{type(multi_choice_answer)}")

if __name__ == "__main__":
    test_ai_answer()