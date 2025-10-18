import json  
from openai import OpenAI

# 默认配置
DEFAULT_API_KEY = ""
DEFAULT_MODEL = "deepseek-ai/DeepSeek-R1"
DEFAULT_BASE_URL = "https://api.siliconflow.cn/v1"

# 全局变量，将在初始化时从配置读取
my_sk = ""
model = DEFAULT_MODEL
client = None
temperature = 0.7  # 默认temperature值，增加随机性
top_p = 0.9  # 默认top_p值

def init_ai_client(config=None):
    """初始化AI客户端，支持从配置读取自定义设置"""
    global my_sk, model, client, temperature, top_p
    
    if config and "ai_config" in config:
        ai_config = config["ai_config"]
        my_sk = ai_config.get("api_key", DEFAULT_API_KEY)
        model = ai_config.get("model", DEFAULT_MODEL)
        base_url = ai_config.get("base_url", DEFAULT_BASE_URL)
        temperature = ai_config.get("temperature", 0.7)  # 默认temperature值设为0.7
        top_p = ai_config.get("top_p", 0.9)
    else:
        my_sk = DEFAULT_API_KEY
        model = DEFAULT_MODEL
        base_url = DEFAULT_BASE_URL
        temperature = 0.7  # 默认temperature值设为0.7
        top_p = 0.9
    
    if my_sk:  # 只有提供了API密钥才创建客户端
        client = OpenAI(
            api_key=my_sk,
            base_url=base_url
        )
    else:
        client = None

def is_math_problem(problem_text):
    """检测题目是否为数学计算题"""
    math_keywords = [
        "计算", "求", "等于", "加", "减", "乘", "除", "+", "-", "×", "*", "÷", "/", 
        "平方", "立方", "根", "sin", "cos", "tan", "log", "ln", "π", "e", 
        "面积", "周长", "体积", "概率", "统计", "平均数", "百分比", "比例"
    ]
    
    # 检查是否包含数学关键词
    for keyword in math_keywords:
        if keyword in problem_text:
            return True
    
    # 检查是否包含数字和运算符
    import re
    # 匹配数字和运算符的模式
    pattern = r'\d+[\+\-\×\*÷\/]\d+|等于|求值|计算'
    if re.search(pattern, problem_text):
        return True
    
    return False


def get_answer(question_info):
    """
    根据题目信息获取答案 - 完全由AI判断题型并返回相应格式
    

    由信息获取题型（放弃）
    Args:
        question_info: dict，包含题目信息
            - title: 题目标题
            - type: 题目类型 (1: 单选题, 2: 多选题, 3: 填空题)
            - options: 选项列表
            - blanks: 填空题答案列表
    
    Returns:
        list: 答案列表（选择题返回选项字母，填空题返回答案文本）
    """
    # 检查AI客户端是否已初始化
    if client is None:
        print("AI客户端未初始化，请先配置API密钥")
        return None
    
    try:
        title = question_info.get("title", "")
        question_type = question_info.get("type", 1)
        options = question_info.get("options", [])
        blanks = question_info.get("blanks", [])
        
        # 构建题目字符串
        problem_text = title
        
        # 如果有选项，构建选项字符串
        if options:
            # 处理选项格式，确保是字典格式
            formatted_options = []
            for option in options:
                if isinstance(option, dict) and "key" in option and "value" in option:
                    formatted_options.append(f"{option['key']}.{option['value']}")
                elif isinstance(option, str):
                    formatted_options.append(f"{chr(65+len(formatted_options))}.{option}")
                else:
                    formatted_options.append(f"{chr(65+len(formatted_options))}.{str(option)}")
            
            option_text = " ".join(formatted_options)
            problem_text = f"{title} {option_text}"
        
        # 添加调试信息，打印题目内容
        print(f"AI获取到的题目内容 - title: '{title}', options: {options}, problem_text: '{problem_text}'")
        print(f"题目类型: {question_type}, 是否有选项: {bool(options)}, 是否有预设答案: {bool(blanks)}")
        
        # 检查题目是否为空
        if not problem_text.strip():
            print("题目为空，无法获取答案")
            return None
        
        # 检测是否为数学题
        is_math = is_math_problem(problem_text)
        
        # 添加更多调试信息
        print(f"开始处理题目 - 题目类型: {question_type}, 是否为数学题: {is_math}")
        print(f"使用的模型: {model}, temperature: {temperature}, top_p: {top_p}")
        
        # 对于填空题，如果有预设答案，优先使用
        if blanks and question_type == 3:
            return [blank["answers"][0] for blank in blanks] if isinstance(blanks, list) else blanks
        
        # 使用AI智能判断题型并生成答案
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system", 
                        "content": """你是一个专业的答题助手，能够智能判断题型并生成正确格式的答案。

                        答题规则：
                        1. 首先判断题目类型：
                           - 如果题目有选项（A.、B.、C.等），则是选择题
                           - 如果题目有下划线（____）或需要填写内容，则是填空题
                        
                        2. 选择题处理：
                           - 输出格式：{"answer": ["A", "B"]}，返回正确答案的选项字母
                           - 对于单选题，返回一个选项字母；对于多选题，返回多个选项字母
                           - 必须返回选项字母（A、B、C、D等），不能返回答案内容
                           - 对于数学计算题，必须先进行精确计算，然后选择正确答案
                        
                        3. 填空题处理：
                           - 输出格式：{"answer": ["答案1", "答案2"]}，返回答案文本
                           - 对于单个填空，返回一个答案；对于多个填空，返回多个答案
                           - 必须返回答案文本，不能返回选项字母
                           - 对于数学计算题，必须返回精确计算结果，不能返回"答案1"、"答案2"等占位符
                           - 重要：必须返回具体的答案内容，例如"北京"、"7"等，绝对不能返回"答案1"、"答案2"等占位符
                        
                        4. 通用规则：
                           - 只输出JSON，不添加其他文字
                           - 确保返回的是正确格式的答案
                           - 不要返回"好的"、"收到"等确认信息，必须返回具体答案
                           - 对于数学计算题，必须进行精确计算，不能猜测或随机选择
                        
                        5. 数学题特别注意：
                           - 如果检测到数学计算题，必须进行精确计算
                           - 不能返回"答案1"、"答案2"等占位符
                           - 必须返回具体的计算结果

                        选择题示例：
                        题目：2+2=? A.5 B.4 C.3 D.7
                        输出：{"answer": ["B"]}
                        
                        题目：以下哪些是正确的？ A.地球是圆的 B.太阳是恒星 C.月亮是行星 D.水是H2O
                        输出：{"answer": ["A", "B", "D"]}

                        填空题示例：
                        题目：中国的首都是____。
                        输出：{"answer": ["北京"]}
                        
                        题目：1+1=____，2+2=____。
                        输出：{"answer": ["2", "4"]}
                        
                        题目：8+1=____。
                        输出：{"answer": ["9"]}"""
                    },
                    {"role": "user", "content": f"题目：{problem_text} 请直接回答，不要解释。"}
                ],
                response_format={"type": "json_object"},
                temperature=temperature,
                top_p=top_p
            )
            
            result = response.choices[0].message.content
            result_dict = json.loads(result)
            ai_answers = result_dict.get("answer", [])
            
            # 确保返回答案列表
            if not ai_answers:
                print("AI返回了空答案，尝试重新生成")
                # 尝试重新生成一次
                return get_answer_retry(question_info)
            
            # 过滤掉空字符串
            if isinstance(ai_answers, list):
                ai_answers = [answer for answer in ai_answers if answer and str(answer).strip()]
            else:
                ai_answers = [ai_answers] if ai_answers and str(ai_answers).strip() else []
            
            # 检查是否返回了确认信息而不是具体答案
            confirmation_words = ["好的", "收到", "知道了", "明白", "OK", "ok", "Okay", "okay"]
            if ai_answers and any(str(answer).lower() in [word.lower() for word in confirmation_words] for answer in ai_answers):
                print(f"AI返回了确认信息而非具体答案: {ai_answers}，尝试重新生成")
                return get_answer_retry(question_info)
            
            # 对于填空题，检查是否返回了占位符答案
            if not options and ai_answers:
                placeholder_answers = ["答案1", "答案2", "答案3", "答案4", "答案5"]
                for ans in ai_answers:
                    if ans in placeholder_answers:
                        print("AI返回了占位符答案，尝试重新生成")
                        return get_answer_retry(question_info)
            
            # 如果过滤后仍然为空，尝试重新生成
            if not ai_answers:
                print("AI返回的答案全部为空，尝试重新生成")
                return get_answer_retry(question_info)
            
            return ai_answers
            
        except Exception as e:
            print(f"AI生成答案失败: {e}")
            # 如果AI失败，尝试使用预设答案
            if blanks:
                # 检查是否有预设答案
                has_answers = False
                for blank in blanks:
                    if blank.get("answers") and len(blank["answers"]) > 0:
                        has_answers = True
                        break
                
                if has_answers:
                    return [blank["answers"][0] for blank in blanks] if isinstance(blanks, list) else blanks
                else:
                    # 如果没有预设答案，返回None让调用方知道AI无法处理
                    print("填空题没有预设答案，AI无法处理")
                    return None
            elif question_type != 3:  # 选择题
                return question_info.get("answers", [])
            return []
            
    except Exception as e:
        print(f"AI获取答案失败: {e}")
        return None

def get_answer_retry(question_info):
    """
    重试获取答案，使用更明确的提示词
    
    Args:
        question_info: dict，包含题目信息
    
    Returns:
        list: 答案列表
    """
    global client, model
    
    if client is None:
        return None
    
    try:
        title = question_info.get("title", "")
        question_type = question_info.get("type", 1)
        options = question_info.get("options", [])
        blanks = question_info.get("blanks", [])
        
        # 构建题目字符串
        problem_text = title
        if options:
            # 处理选项格式，确保是字典格式
            formatted_options = []
            for option in options:
                if isinstance(option, dict) and "key" in option and "value" in option:
                    formatted_options.append(f"{option['key']}.{option['value']}")
                elif isinstance(option, str):
                    formatted_options.append(f"{chr(65+len(formatted_options))}.{option}")
                else:
                    formatted_options.append(f"{chr(65+len(formatted_options))}.{str(option)}")
            
            option_text = " ".join(formatted_options)
            problem_text = f"{title} {option_text}"
        
        # 检测是否为数学题
        is_math = is_math_problem(problem_text)
        
        # 对于填空题，添加特殊提示
        if blanks:
            problem_text += "\n注意：这是一道填空题，请直接填写答案内容，不要使用选项字母。"
            problem_text += "\n请务必返回具体的答案内容，不要返回'答案1'、'答案2'等占位符，也不要返回'好的'、'收到'等确认信息。"
        
        # 根据题目类型使用更明确的提示词
        if options:  # 选择题
            system_prompt = """你是一个专业的答题助手，专门回答选择题。

            答题规则：
            1. 分析题目并找出正确答案
            2. 输出格式：{"answer": ["A", "B"]}，返回正确答案的选项字母
            3. 只输出JSON，不添加其他文字
            4. 必须返回选项字母（A、B、C、D等），不能返回答案内容
            5. 确保答案不为空
            6. 不要返回"好的"、"收到"等确认信息，必须返回具体答案
            7. 对于数学计算题，必须先进行精确计算，然后选择正确答案，不能猜测或随机选择

            示例：
            题目：2+2=? A.5 B.4 C.3 D.7
            输出：{"answer": ["B"]}"""
        else:  # 填空题
            system_prompt = """你是一个专业的答题助手，专门回答填空题。

            答题规则：
            1. 分析题目并找出正确答案
            2. 输出格式：{"answer": ["答案1", "答案2"]}，返回答案文本
            3. 只输出JSON，不添加其他文字
            4. 必须返回答案文本，不能返回选项字母
            5. 确保答案不为空
            6. 不要返回"好的"、"收到"等确认信息，必须返回具体答案
            7. 对于数学计算题，必须返回精确计算结果，不能返回"答案1"、"答案2"等占位符
            8. 重要：必须返回具体的答案内容，例如"北京"、"7"等，绝对不能返回"答案1"、"答案2"等占位符

            示例：
            题目：中国的首都是____。
            输出：{"answer": ["北京"]}
            
            题目：6+1=____。
            输出：{"answer": ["7"]}"""
        
        # 如果是数学题，添加额外的提示
        if is_math:
            system_prompt += "\n\n重要提醒：这是一道数学计算题，请务必进行精确计算，不要猜测或使用占位符答案。"
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system", 
                    "content": system_prompt
                },
                {"role": "user", "content": f"题目：{problem_text} 请直接回答，不要解释。"}
            ],
            response_format={"type": "json_object"},
            temperature=temperature,  # 使用全局变量temperature
            top_p=top_p  # 使用全局变量top_p
        )
        
        result = response.choices[0].message.content
        result_dict = json.loads(result)
        ai_answers = result_dict.get("answer", [])
        
        # 确保返回答案列表
        if not ai_answers:
            print("重试后AI仍然返回空答案")
            # 如果重试仍然失败，尝试使用预设答案
            if blanks:
                # 检查是否有预设答案
                has_answers = False
                for blank in blanks:
                    if blank.get("answers") and len(blank["answers"]) > 0:
                        has_answers = True
                        break
                
                if has_answers:
                    return [blank["answers"][0] for blank in blanks] if isinstance(blanks, list) else blanks
                else:
                    # 如果没有预设答案，返回None让调用方知道AI无法处理
                    print("填空题没有预设答案，AI无法处理")
                    return None
            elif question_type != 3:  # 选择题
                return question_info.get("answers", [])
            return []
        
        # 过滤掉空字符串
        if isinstance(ai_answers, list):
            ai_answers = [answer for answer in ai_answers if answer and str(answer).strip()]
        else:
            ai_answers = [ai_answers] if ai_answers and str(ai_answers).strip() else []
        
        # 检查是否返回了确认信息而不是具体答案
        confirmation_words = ["好的", "收到", "知道了", "明白", "OK", "ok", "Okay", "okay"]
        if ai_answers and any(str(answer).lower() in [word.lower() for word in confirmation_words] for answer in ai_answers):
            print(f"重试后AI仍然返回确认信息而非具体答案: {ai_answers}")
            # 如果重试后仍然返回确认信息，使用预设答案
            if blanks:
                # 检查是否有预设答案
                has_answers = False
                for blank in blanks:
                    if blank.get("answers") and len(blank["answers"]) > 0:
                        has_answers = True
                        break
                
                if has_answers:
                    print("使用预设答案替代确认信息")
                    return [blank["answers"][0] for blank in blanks] if isinstance(blanks, list) else blanks
                else:
                    print("填空题没有预设答案，AI无法处理")
                    return None
            elif question_type != 3:  # 选择题
                return question_info.get("answers", [])
            return []
        
        # 对于填空题，检查是否返回了占位符答案
        if not options and ai_answers:
            placeholder_answers = ["答案1", "答案2", "答案3", "答案4", "答案5"]
            for ans in ai_answers:
                if ans in placeholder_answers:
                    print("重试后AI仍然返回占位符答案，使用预设答案")
                    # 如果重试后仍然返回占位符，使用预设答案
                    if blanks:
                        # 检查是否有预设答案
                        has_answers = False
                        for blank in blanks:
                            if blank.get("answers") and len(blank["answers"]) > 0:
                                has_answers = True
                                break
                        
                        if has_answers:
                            return [blank["answers"][0] for blank in blanks] if isinstance(blanks, list) else blanks
                        else:
                            print("填空题没有预设答案，AI无法处理")
                            return None
                    elif question_type != 3:  # 选择题
                        return question_info.get("answers", [])
                    return []
        
        # 如果过滤后仍然为空，使用预设答案
        if not ai_answers:
            print("重试后AI返回的答案全部为空，使用预设答案")
            if blanks:
                # 检查是否有预设答案
                has_answers = False
                for blank in blanks:
                    if blank.get("answers") and len(blank["answers"]) > 0:
                        has_answers = True
                        break
                
                if has_answers:
                    return [blank["answers"][0] for blank in blanks] if isinstance(blanks, list) else blanks
                else:
                    # 如果没有预设答案，返回None让调用方知道AI无法处理
                    print("填空题没有预设答案，AI无法处理")
                    return None
            elif question_type != 3:  # 选择题
                return question_info.get("answers", [])
            return []
        
        return ai_answers
        
    except Exception as e:
        print(f"重试获取答案失败: {e}")
        # 如果重试失败，尝试使用预设答案
        if blanks:
            # 检查是否有预设答案
            has_answers = False
            for blank in blanks:
                if blank.get("answers") and len(blank["answers"]) > 0:
                    has_answers = True
                    break
            
            if has_answers:
                return [blank["answers"][0] for blank in blanks] if isinstance(blanks, list) else blanks
            else:
                # 如果没有预设答案，返回None让调用方知道AI无法处理
                print("填空题没有预设答案，AI无法处理")
                return None
        elif question_type != 3:  # 选择题
            return question_info.get("answers", [])
        return []