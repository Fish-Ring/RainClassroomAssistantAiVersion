import json
import random
import threading
import time
import traceback
import sys
import os

import requests
import websocket

from Scripts.PPTManager import PPTManager
from Scripts.Utils import (
    calculate_waittime,
    dict_result,
    get_user_info,
    is_debug,
    get_host,
    show_ai_popup,
)

# 添加scai模块路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    import scai
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False


class Lesson:
    def __init__(self, lessonid, lessonname, classroomid, main_ui):
        self.classroomid = classroomid
        self.lessonid = lessonid
        self.lessonname = lessonname
        self.sessionid = main_ui.config["sessionid"]
        self.headers = {
            "Cookie": "sessionid=%s" % self.sessionid,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:97.0) Gecko/20100101 Firefox/97.0",
        }
        self.receive_danmu = {}
        self.sent_danmu_dict = {}
        self.danmu_dict = {}
        self.problems_ls = []
        self.problems_dict = {}
        self.unlocked_problem = []
        self.classmates_ls = []
        self.add_message = main_ui.add_message_signal.emit
        self.add_course = main_ui.add_course_signal.emit
        self.del_course = main_ui.del_course_signal.emit
        self.config = main_ui.config
        self.region = self.config["region"]
        code, rtn = get_user_info(self.sessionid, self.config["region"])
        self.user_uid = rtn["id"]
        self.user_uname = rtn["name"]
        self.main_ui = main_ui
        # self.pptmanager_dict = {}

    def _download(self, data):
        data["title"] = data["title"].replace("/", "_").strip()
        self.print_problems(data)
        self.add_message("开始下载ppt : " + data["title"] + ".pdf", 0)
        try:
            pdfname, usetime = PPTManager(data, self.lessonname).start()
            if pdfname is None or usetime is None:
                if is_debug():
                    self.add_message(
                        "重复下载ppt取消 : " + pdfname + f"，耗时{usetime}秒", 0
                    )
                return
            self.add_message("下载ppt成功 : " + pdfname + f"，耗时{usetime}秒", 0)
        except Exception as e:
            self.add_message("下载ppt失败 : " + data["title"] + ".pdf", 0)
            self.add_message(traceback.format_exc(), 0)

    def download_ppt(self, presentationid):
        threading.Thread(
            target=self._download, args=(self._get_ppt(presentationid),), daemon=True
        ).start()

    def _get_ppt(self, presentationid):
        # 获取课程各页ppt
        r = requests.get(
            url=f"https://{get_host(self.config['region'])}/api/v3/lesson/presentation/fetch?presentation_id={presentationid}",
            headers=self.headers,
            proxies={"http": None, "https": None},
        )
        data = dict_result(r.text)["data"]
        print(f"原始PPT数据 (presentationid={presentationid}):", data)
        
        # 检查数据结构
        if "slides" not in data:
            print(f"警告：PPT数据中没有slides字段 (presentationid={presentationid})")
            return data
        
        # 检查slides中是否有problem
        slides_with_problems = [slide for slide in data["slides"] if "problem" in slide.keys()]
        print(f"包含题目的幻灯片数量: {len(slides_with_problems)}")
        
        return data

    def print_problems(self, data):
        answers = {}
        slides = [problem for problem in data["slides"] if "problem" in problem.keys()]
        index = [problem["index"] for problem in slides]
        problems = [problem["problem"] for problem in slides]
        for i in range(len(problems)):
            problems[i]["index"] = index[i]
        for problem in problems:
            answers[problem["index"]] = problem["answers"]
        self.add_message(
            f"{self.lessonname}:{data['title']} 的答案为" + str(answers), 0
        )

    def get_problems(self, presentationid):
        # 获取课程ppt中的题目
        data = self._get_ppt(presentationid)
        
        # 检查数据结构
        if "slides" not in data:
            print(f"警告：PPT数据中没有slides字段 (presentationid={presentationid})")
            return []
        
        slides = [problem for problem in data["slides"] if "problem" in problem.keys()]
        print(f"筛选后的题目幻灯片 (presentationid={presentationid}):", slides)
        
        index = [problem["index"] for problem in slides]
        problems = [problem["problem"] for problem in slides]
        
        print(f"提取的题目数量: {len(problems)}")
        
        for i in range(len(problems)):
            problems[i]["index"] = index[i]
            print(f"题目 {i+1}:", problems[i])
            # 确保题目有必要的字段
            if "problemId" not in problems[i]:
                problems[i]["problemId"] = problems[i].get("id", "")
            if "title" not in problems[i] or not problems[i].get("title", ""):
                # 对于填空题，题目内容通常在body字段中
                if problems[i].get("problemType") == 4:  # 填空题
                    problems[i]["title"] = problems[i].get("body", "")
                else:
                    # 对于选择题，也尝试从body字段获取题目内容
                    problems[i]["title"] = problems[i].get("body", "") or problems[i].get("description", "")
            if "options" not in problems[i]:
                problems[i]["options"] = problems[i].get("choices", [])
            if "answers" not in problems[i]:
                problems[i]["answers"] = problems[i].get("correctAnswers", [])
            if "problemType" not in problems[i]:
                problems[i]["problemType"] = problems[i].get("type", 1)
            if "blanks" not in problems[i]:
                problems[i]["blanks"] = problems[i].get("fillBlanks", [])
            
            # 检查题目内容是否为空
            title = problems[i].get("title", "")
            options = problems[i].get("options", [])
            print(f"题目 {i+1} 内容检查 - title: '{title}', options: {options}")
            
            print(f"处理后的题目 {i+1}:", problems[i])
        return problems

    def answer_questions(self, problemid, problemtype, answer, limit):
        # 回答问题
        if answer:
            wait_time = calculate_waittime(
                limit,
                self.config["answer_config"]["answer_delay"]["type"],
                self.config["answer_config"]["answer_delay"]["custom"]["percent"],
            )
            if wait_time != 0:
                meg = "%s检测到问题，将在%s秒后自动回答，答案为%s" % (
                    self.lessonname,
                    wait_time,
                    answer,
                )
                # threading.Thread(target=say_something,args=(meg,)).start()
                self.add_message(meg, 3)
                time.sleep(wait_time)
            else:
                meg = "%s检测到问题，剩余时间小于15秒，将立即自动回答，答案为%s" % (
                    self.lessonname,
                    answer,
                )
                self.add_message(meg, 3)
                # threading.Thread(target=say_something,args=(meg,)).start()
            data = {
                "problemId": problemid,
                "problemType": problemtype,
                "dt": int(time.time()),
                "result": answer,
            }
            r = requests.post(
                url=f"https://{get_host(self.config['region'])}/api/v3/lesson/problem/answer",
                headers=self.headers,
                data=json.dumps(data),
                proxies={"http": None, "https": None},
            )
            return_dict = dict_result(r.text)
            if return_dict["code"] == 0:
                meg = "%s自动回答成功" % self.lessonname
                self.add_message(meg, 4)
                # threading.Thread(target=say_something,args=(meg,)).start()
                return True
            else:
                meg = "%s自动回答失败，原因：%s" % (
                    self.lessonname,
                    return_dict["msg"].replace("_", " "),
                )
                self.add_message(meg, 4)
                # threading.Thread(target=say_something,args=(meg,)).start()
                return False
        else:
            if limit == -1:
                meg = "%s的问题没有找到答案，该题不限时，请尽快前往雨课堂回答" % (
                    self.lessonname
                )
            else:
                meg = "%s的问题没有找到答案，请在%s秒内前往雨课堂回答" % (
                    self.lessonname,
                    limit,
                )
            # threading.Thread(target=say_something,args=(meg,)).start()
            self.add_message(meg, 4)
            return False

    def on_open(self, wsapp):
        self.handshark = {
            "op": "hello",
            "userid": self.user_uid,
            "role": "student",
            "auth": self.auth,
            "lessonid": self.lessonid,
        }
        wsapp.send(json.dumps(self.handshark))

    def checkin_class(self):
        r = requests.post(
            url=f"https://{get_host(self.config['region'])}/api/v3/lesson/checkin",
            headers=self.headers,
            data=json.dumps({"source": 5, "lessonId": self.lessonid}),
            proxies={"http": None, "https": None},
        )
        set_auth = r.headers.get("Set-Auth", None)
        times = 1
        while not set_auth and times <= 3:
            set_auth = r.headers.get("Set-Auth", None)
            times += 1
            time.sleep(1)
        self.headers["Authorization"] = "Bearer %s" % set_auth
        return dict_result(r.text)["data"]["lessonToken"]

    def on_message(self, wsapp, message):
        data = dict_result(message)
        op = data["op"]
        if is_debug():
            print(op)
            self.add_message(op, 0)
        if op == "hello":
            presentations = list(
                set(
                    [
                        slide["pres"]
                        for slide in data["timeline"]
                        if slide["type"] == "slide"
                    ]
                )
            )
            print("hello数据:", data)
            print("提取的presentations:", presentations)
            # 检查presentation字段是否存在
            current_presentation = data.get("presentation", "")
            if current_presentation and current_presentation not in presentations:
                presentations.append(current_presentation)
            print(f"处理前的题目列表长度: {len(self.problems_ls)}")
            for presentationid in presentations:
                # print(presentationid)
                print(f"处理presentationid: {presentationid}")
                new_problems = self.get_problems(presentationid)
                print(f"获取到的新题目数量: {len(new_problems)}")
                self.problems_ls.extend(new_problems)
                print(f"添加后的题目列表长度: {len(self.problems_ls)}")
                for problem in self.problems_ls:
                    self.problems_dict[problem["index"]] = problem["answers"]
                self.download_ppt(presentationid)
            self.unlocked_problem = data["unlockedproblem"]
            print(f"未解锁的题目: {self.unlocked_problem}")
            for problemid in self.unlocked_problem:
                self._current_problem(wsapp, problemid)
        elif op == "unlockproblem":
            problem_id = data["problem"]["sid"]
            problem_limit = data["problem"]["limit"]
            print(f"收到unlockproblem事件，题目ID: {problem_id}, 限制时间: {problem_limit}")
            print(f"当前题目列表: {[p['problemId'] for p in self.problems_ls]}")
            self.start_answer(problem_id, problem_limit)
        elif op == "lessonfinished":
            meg = "%s下课了" % self.lessonname
            # threading.Thread(target=say_something,args=(meg,)).start()
            self.add_message(meg, 7)
            wsapp.close()
        elif op == "presentationupdated":
            self.problems_ls.extend(self.get_problems(data["presentation"]))
            for problem in self.problems_ls:
                self.problems_dict[problem["index"]] = problem["answers"]
            self.download_ppt(data["presentation"])
        elif op == "presentationcreated":
            self.problems_ls.extend(self.get_problems(data["presentation"]))
            for problem in self.problems_ls:
                self.problems_dict[problem["index"]] = problem["answers"]
            self.download_ppt(data["presentation"])
        elif op == "newdanmu" and self.config["auto_danmu"]:
            current_content = data["danmu"].lower()
            uid = data["userid"]
            sent_danmu_user = User(uid)
            if sent_danmu_user in self.classmates_ls:
                for i in self.classmates_ls:
                    if i == sent_danmu_user:
                        meg = "%s课程的%s%s发送了弹幕：%s" % (
                            self.lessonname,
                            i.sno,
                            i.name,
                            data["danmu"],
                        )
                        self.add_message(meg, 2)
                        break
            else:
                self.classmates_ls.append(sent_danmu_user)
                sent_danmu_user.get_userinfo(self.classroomid, self.headers)
                meg = "%s课程的%s%s发送了弹幕：%s" % (
                    self.lessonname,
                    sent_danmu_user.sno,
                    sent_danmu_user.name,
                    data["danmu"],
                )
                self.add_message(meg, 2)
            now = time.time()
            # 收到一条弹幕，尝试取出其之前的所有记录的列表，取不到则初始化该内容列表
            try:
                same_content_ls = self.danmu_dict[current_content]
            except KeyError:
                self.danmu_dict[current_content] = []
                same_content_ls = self.danmu_dict[current_content]
            # 清除超过60秒的弹幕记录
            for i in same_content_ls:
                if now - i > 60:
                    same_content_ls.remove(i)
            # 如果当前的弹幕没被发过，或者已发送时间超过60秒
            if (
                current_content not in self.sent_danmu_dict.keys()
                or now - self.sent_danmu_dict[current_content] > 60
            ):
                if (
                    len(same_content_ls) + 1
                    >= self.config["danmu_config"]["danmu_limit"]
                ):
                    self.send_danmu(current_content)
                    same_content_ls = []
                    self.sent_danmu_dict[current_content] = now
                else:
                    same_content_ls.append(now)
        elif op == "callpaused":
            meg = "%s点名了，点到了：%s" % (self.lessonname, data["name"])
            if self.user_uname == data["name"]:
                self.add_message(meg, 5)
            else:
                self.add_message(meg, 6)
        # 程序在上课中途运行，由_current_problem发送的已解锁题目数据，得到的返回值。
        # 此处需要筛选未到期的题目进行回答。
        elif op == "probleminfo":
            print(f"收到probleminfo事件，数据: {data}")
            if data["limit"] != -1:
                time_left = int(
                    data["limit"] - (int(data["now"]) - int(data["dt"])) / 1000
                )
            else:
                time_left = data["limit"]
            # 筛选未到期题目
            if time_left > 0 or time_left == -1:
                print(f"题目剩余时间: {time_left}, 自动答题设置: {self.config['auto_answer']}")
                if self.config["auto_answer"]:
                    self.start_answer(data["problemid"], time_left)
                else:
                    self.add_message(
                        "%s检测到问题，但未开启自动回答" % self.lessonname, 3
                    )

    def start_answer(self, problemid, limit):
        print(f"开始答题，problemid: {problemid}, limit: {limit}")
        print(f"当前题目列表长度: {len(self.problems_ls)}")
        print(f"当前题目列表中的所有problemId: {[p.get('problemId', 'None') for p in self.problems_ls]}")
        
        for promble in self.problems_ls:
            if promble["problemId"] == problemid:
                print(f"找到匹配题目，题目ID: {problemid}")
                print(f"题目完整数据: {promble}")
                
                if promble["result"] is not None:
                    # 如果该题已经作答过，直接跳出函数以忽略该题
                    # 该情况理论上只会出现在启动监听时
                    return
                blanks = promble.get("blanks", [])
                answers = []
                
                # 优先使用AI获取答案
                if AI_AVAILABLE and self.config.get("ai_answer", False):
                    try:
                        # 检查AI客户端是否已初始化
                        if not hasattr(scai, 'client') or scai.client is None:
                            self.add_message(f"{self.lessonname}: AI客户端未初始化，请检查配置", 3)
                            # 回退到随机选择
                            if blanks:
                                for i in blanks:
                                    # 检查answers列表是否为空
                                    if i.get("answers") and len(i["answers"]) > 0:
                                        answers.append(random.choice(i["answers"]))
                                    else:
                                        # 如果答案列表为空，使用空字符串作为答案
                                        answers.append("")
                                        self.add_message(f"{self.lessonname}: 警告：填空题答案列表为空，使用空字符串", 3)
                            else:
                                answers = promble.get("answers", [])
                            self.add_message(f"{self.lessonname}: 使用随机选择: {answers}", 3)
                        else:
                            # 构建题目信息
                            question_info = {
                                "title": promble.get("title", ""),
                                "type": promble.get("problemType", 1),
                                "options": promble.get("options", []),
                                "blanks": blanks
                            }
                            
                            print(f"构建的题目信息: {question_info}")
                            
                            # 检查题目是否为空
                            if not question_info["title"].strip() and not question_info["options"]:
                                self.add_message(f"{self.lessonname}: 题目内容为空，无法使用AI获取答案", 3)
                                print(f"题目内容为空 - title: '{question_info['title']}', options: {question_info['options']}")
                                # 回退到随机选择
                                if blanks:
                                    for i in blanks:
                                        # 检查answers列表是否为空
                                        if i.get("answers") and len(i["answers"]) > 0:
                                            answers.append(random.choice(i["answers"]))
                                        else:
                                            # 如果答案列表为空，使用空字符串作为答案
                                            answers.append("")
                                            self.add_message(f"{self.lessonname}: 警告：填空题答案列表为空，使用空字符串", 3)
                                else:
                                    answers = promble.get("answers", [])
                                self.add_message(f"{self.lessonname}: 使用随机选择: {answers}", 3)
                            else:
                                self.add_message(f"{self.lessonname}: 正在使用AI获取答案，题目: {question_info['title']}", 3)
                                
                                # 调用AI获取答案
                                ai_answer = scai.get_answer(question_info)
                                if ai_answer:
                                    # 直接使用AI返回的答案，AI已经判断了题型并返回了正确格式
                                    answers = ai_answer if isinstance(ai_answer, list) else [ai_answer]
                                    
                                    # 对于填空题，如果AI错误地返回了选项字母，尝试使用blanks中的答案
                                    if blanks and answers and all(isinstance(item, str) and len(item) == 1 and item.isalpha() and item.isupper() for item in answers):
                                        print(f"警告：AI为填空题返回了选项字母，使用预设答案")
                                        answers = []
                                        for blank in blanks:
                                            # 检查answers列表是否为空
                                            if blank.get("answers") and len(blank["answers"]) > 0:
                                                answers.append(random.choice(blank["answers"]))
                                            else:
                                                # 如果答案列表为空，使用空字符串作为答案
                                                answers.append("")
                                                self.add_message(f"{self.lessonname}: 警告：填空题答案列表为空，使用空字符串", 3)
                                    self.add_message(f"{self.lessonname}: 使用AI获取答案成功: {answers}", 3)
                                    # AI答题成功消息使用可配置弹窗（仅在AI启用时显示）
                                    if self.config.get("ai_answer", False):
                                        show_ai_popup(f"{self.lessonname}: 使用AI获取答案成功", "AI答题", self.config)
                                elif ai_answer is None:
                                    # AI返回None表示填空题没有预设答案，AI无法处理，或者题目为空
                                    self.add_message(f"{self.lessonname}: AI无法获取答案", 3)
                                    # 回退到随机选择
                                    if blanks:
                                        for i in blanks:
                                            # 检查answers列表是否为空
                                            if i.get("answers") and len(i["answers"]) > 0:
                                                answers.append(random.choice(i["answers"]))
                                            else:
                                                # 如果答案列表为空，使用空字符串作为答案
                                                answers.append("")
                                                self.add_message(f"{self.lessonname}: 警告：填空题答案列表为空，使用空字符串", 3)
                                    else:
                                        answers = promble.get("answers", [])
                                    self.add_message(f"{self.lessonname}: 使用随机选择: {answers}", 3)
                                else:
                                    # AI无法获取答案时，回退到随机选择
                                    if blanks:
                                        for i in blanks:
                                            # 检查answers列表是否为空
                                            if i.get("answers") and len(i["answers"]) > 0:
                                                answers.append(random.choice(i["answers"]))
                                            else:
                                                # 如果答案列表为空，使用空字符串作为答案
                                                answers.append("")
                                                self.add_message(f"{self.lessonname}: 警告：填空题答案列表为空，使用空字符串", 3)
                                    else:
                                        answers = promble.get("answers", [])
                                    self.add_message(f"{self.lessonname}: AI无法获取答案，使用随机选择: {answers}", 3)
                    except Exception as e:
                        # AI调用失败时，回退到随机选择
                        self.add_message(f"{self.lessonname}: AI获取答案异常: {str(e)}", 3)
                        if blanks:
                            for i in blanks:
                                # 检查answers列表是否为空
                                if i.get("answers") and len(i["answers"]) > 0:
                                    answers.append(random.choice(i["answers"]))
                                else:
                                    # 如果答案列表为空，使用空字符串作为答案
                                    answers.append("")
                                    self.add_message(f"{self.lessonname}: 警告：填空题答案列表为空，使用空字符串", 3)
                        else:
                            answers = promble.get("answers", [])
                        self.add_message(f"{self.lessonname}: AI获取答案失败，使用随机选择: {answers}", 3)
                        # AI答题失败消息使用可配置弹窗（仅在AI启用时显示）
                        if self.config.get("ai_answer", False):
                            show_ai_popup(f"{self.lessonname}: AI获取答案失败，使用随机选择: {answers}", "AI答题失败", self.config)
                else:
                    # 未启用AI或AI不可用时，使用随机选择
                    if blanks:
                        for i in blanks:
                            # 检查answers列表是否为空
                            if i.get("answers") and len(i["answers"]) > 0:
                                answers.append(random.choice(i["answers"]))
                            else:
                                # 如果答案列表为空，使用空字符串作为答案
                                answers.append("")
                                self.add_message(f"{self.lessonname}: 警告：填空题答案列表为空，使用空字符串", 3)
                    else:
                        answers = promble.get("answers", [])
                    self.add_message(f"{self.lessonname}: AI不可用，使用随机选择: {answers}", 3)
                    # AI不可用消息使用可配置弹窗（仅在AI可用但配置关闭时显示）
                    if AI_AVAILABLE and not self.config.get("ai_answer", False):
                        show_ai_popup(f"{self.lessonname}: AI可用但未启用，使用随机选择", "AI未启用", self.config)
                    elif not AI_AVAILABLE:
                        # AI模块不可用时，只在日志中记录，不显示弹窗
                        print(f"{self.lessonname}: AI模块不可用，使用随机选择: {answers}")
                
                threading.Thread(
                    target=self.answer_questions,
                    args=(promble["problemId"], promble["problemType"], answers, limit),
                ).start()
                break
        else:
            if limit == -1:
                meg = "%s的问题没有找到答案，该题不限时，请尽快前往雨课堂回答" % (
                    self.lessonname
                )
            else:
                meg = "%s的问题没有找到答案，请在%s秒内前往雨课堂回答" % (
                    self.lessonname,
                    limit,
                )
            self.add_message(meg, 4)
            # threading.Thread(target=say_something,args=(meg,)).start()

    def _current_problem(self, wsapp, promblemid):
        # 为获取已解锁的问题详情信息，向wsapp发送probleminfo
        print(f"发送probleminfo请求，题目ID: {promblemid}")
        print(f"课程ID: {self.lessonid}")
        query_problem = {
            "op": "probleminfo",
            "lessonid": self.lessonid,
            "problemid": promblemid,
            "msgid": 1,
        }
        print(f"发送的probleminfo请求: {query_problem}")
        wsapp.send(json.dumps(query_problem))

    def start_lesson(self, delay, callback):
        self.auth = self.checkin_class()
        rtn = self.get_lesson_info()
        teacher = rtn["teacher"]["name"]
        title = rtn["title"]
        timestamp = rtn["startTime"] // 1000
        time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))
        index = self.main_ui.tableWidget.rowCount()
        self.add_course([self.lessonname, title, teacher, time_str], index)
        if self.lessonname.find("测试") != -1:
            meg = "%s测试课程，不进行监听" % self.lessonname
            self.add_message(meg, 7)
            return callback(self)
        if (
            int(time.time()) - timestamp
            <= self.config["sign_config"]["delay_time"]["custom"]["cutoff"]
            and delay > 0
        ):
            meg = f"检测到课程{self.lessonname}正在上课，将于{delay}秒后加入监听列表"
            self.add_message(meg, 7)
            time.sleep(delay)
        else:
            meg = f"检测到课程{self.lessonname}正在上课，已加入监听列表"
            self.add_message(meg, 7)
        self.wsapp = websocket.WebSocketApp(
            url=f"wss://{get_host(self.config['region'])}/wsapp/",
            header=self.headers,
            on_open=self.on_open,
            on_message=self.on_message,
        )
        self.wsapp.run_forever()
        meg = "%s监听结束" % self.lessonname
        self.add_message(meg, 7)
        self.del_course(index)
        # threading.Thread(target=say_something,args=(meg,)).start()
        return callback(self)

    def send_danmu(self, content):
        url = f"https://{get_host(self.config['region'])}/api/v3/lesson/danmu/send"
        data = {
            "extra": "",
            "fromStart": "50",
            "lessonId": self.lessonid,
            "message": content,
            "requiredCensor": False,
            "showStatus": True,
            "target": "",
            "userName": "",
            "wordCloud": True,
        }
        r = requests.post(
            url=url,
            headers=self.headers,
            data=json.dumps(data),
            proxies={"http": None, "https": None},
        )
        if dict_result(r.text)["code"] == 0:
            meg = "%s弹幕发送成功！内容：%s" % (self.lessonname, content)
        else:
            meg = "%s弹幕发送失败！内容：%s" % (self.lessonname, content)
        self.add_message(meg, 1)

    def get_lesson_info(self):
        url = f"https://{get_host(self.config['region'])}/api/v3/lesson/basic-info"
        r = requests.get(
            url=url, headers=self.headers, proxies={"http": None, "https": None}
        )
        return dict_result(r.text)["data"]

    def __eq__(self, other):
        return self.lessonid == other.lessonid


class User:
    def __init__(self, uid):
        self.uid = uid

    def get_userinfo(self, classroomid, headers):
        r = requests.get(
            f"https://{get_host(self.config['region'])}/v/course_meta/fetch_user_info_new?query_user_id={self.uid}&classroom_id={classroomid}",
            headers=headers,
            proxies={"http": None, "https": None},
        )
        data = dict_result(r.text)["data"]
        self.sno = data["school_number"]
        self.name = data["name"]