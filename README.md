
# RainClassroomAssistantAiVersion
## 原库(非AI版本) https://github.com/travellerse/RainClassroomAssistant
## 新库(AI版本，基于v0.4.2修改) https://github.com/Fish-Ring/RainClassroomAssistantAiVersion
    
&emsp;&emsp;基于Python的雨课堂线上课AI答题小助手。
默认配置文件：%APPDATA%\RainClassroomAssistantAi\config.json
## 增加功能
 - AI答题（新增）
    - 支持多种题型
    - 支持自定义模型
    - 不同模型，不同配置，答题效果不同，答案可能存在错误

 
## 使用方法
### 使用前准备
1. **使用前最好关闭所有代理程序，否则程序可能无法正常使用**
### 使用程序
双击打开RainClassroomAssistantAi即可使用！
### 打包程序
1. 安装pyinstaller(已包含在requirements.txt中)
```shell
pip install pyinstaller
```
2. 使用配置文件打包
```shell
pyinstaller RainClassroomAssistantAi.spec
```
## 配置界面效果说明

### 前端配置界面

在RainClassroomAssistantAi的配置界面中，AI配置部分现在包含以下新增参数：

1. **Temperature参数滑块**
   - 范围：0.0-2.0
   - 步长：0.1
   - 默认值：0.1
   - 工具提示：控制AI回答的随机性，值越高回答越随机、越有创造性

2. **Top-p参数滑块**
   - 范围：0.0-1.0
   - 步长：0.1
   - 默认值：0.9
   - 工具提示：控制AI词汇选择的多样性，值越高词汇选择越多样

### 配置界面位置

这些参数位于：
1. 打开RainClassroomAssistantAi应用
2. 点击"配置"按钮
3. 在"答题配置"部分，勾选"启用AI答案获取"
4. 在展开的AI配置中，可以看到新增的Temperature和Top-p参数

### 参数调整建议

根据不同题型，推荐以下参数设置：

1. **数学计算题**
   - Temperature: 0.1-0.2 (低随机性，确保答案准确)
   - Top-p: 0.9 (保持一定词汇多样性)

2. **创意题/开放题**
   - Temperature: 0.7-0.9 (高随机性，鼓励创造性回答)
   - Top-p: 0.9-1.0 (高词汇多样性)

3. **一般知识题**
   - Temperature: 0.3-0.5 (平衡准确性和多样性)
   - Top-p: 0.9 (标准词汇多样性)

### 配置保存
调整参数后，点击"保存"按钮，配置将被保存并在下次启动时自动加载。AI答题功能将使用最新的参数设置。