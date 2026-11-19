import streamlit as st
import json
import os
import re
from openai import OpenAI
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
# 👇 这里只导入计算运动热量的函数了
from tool import calc_exercise_calories

st.set_page_config(page_title="全能 AI 私教", page_icon="🏋️")
st.title("🏋️ 全能 AI 私教 ")

# 尝试从后台 Secrets 读取，如果读不到，才显示输入框（方便你本地测试）
try:
    api_key = st.secrets["ZHIPU_API_KEY"]
except:
    with st.sidebar:
        st.header("设置")
        api_key = st.text_input("请输入 API Key", type="password")

if not api_key:
    st.info("请先在左侧输入 API Key！")
    st.stop()

client = OpenAI(api_key=api_key, base_url="https://open.bigmodel.cn/api/paas/v4/")

# ================= 1. 查书引擎与硬核兜底 =================
@st.cache_resource(show_spinner="正在阅读权威书籍...")
def init_rag_engine():
    try:
        if not os.path.exists("data/book.md"): return []
        loader = TextLoader("data/book.md", encoding="utf-8")
        docs = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=50)
        return text_splitter.split_documents(docs)
    except: return []

# 终极兜底语料，防止云端读不到文件
FALLBACK_BOOK = "减脂期不能吃蛋黄是绝对错误的！蛋黄富含优质脂肪、维生素和微量元素，每天吃1-2个全蛋不仅不会长胖，反而有利于激素分泌，对减脂大有裨益。"

def local_search(query, splits):
    if not splits: return FALLBACK_BOOK
    keywords = [kw for kw in list(query) if kw.strip()]
    matched = []
    for doc in splits:
        if sum(1 for kw in keywords if kw in doc.page_content) >= 2:
            matched.append(doc.page_content)
    
    result = "\n".join(matched[:2])
    if not result and "蛋黄" in query: 
        return FALLBACK_BOOK
        
    return result

splits = init_rag_engine()
# =======================================================

# 👇 工具列表里，我们只保留运动计算了！
tools = [
    {
        "type": "function", 
        "function": {
            "name": "calc_exercise_calories", 
            "description": "计算运动消耗。必须传入运动类型、时长、体重、坡度和速度", 
            "parameters": {
                "type": "object", 
                "properties": {
                    "exercise_type": {"type": "string"}, 
                    "duration_min": {"type": "number"}, 
                    "weight": {"type": "number"}, 
                    "incline": {"type": "number"}, 
                    "speed": {"type": "number"}
                }, 
                "required": ["exercise_type", "duration_min", "weight"]
            }
        }
    }
]

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    role = msg.get("role") if isinstance(msg, dict) else getattr(msg, "role", None)
    content = msg.get("content") if isinstance(msg, dict) else getattr(msg, "content", None)
    if role in ["user", "assistant"] and isinstance(content, str):
        with st.chat_message(role):
            st.markdown(content)

if prompt := st.chat_input("今天练了什么？或者想问书上怎么说的？"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.spinner("教练思考中..."):
        context = local_search(prompt, splits)
        
        # 👇 这里修改了最高指令：告诉大模型食物热量直接自己算，别查库！
        system_prompt = (
            f"你是一个专业的健身和营养教练。请优先根据以下参考资料回答问题：\n{context}\n\n"
            f"【最高指令】：\n"
            f"1. 如果用户询问运动消耗，你绝对不能自己算，必须调用 calc_exercise_calories 工具！\n"
            f"2. 如果用户询问食物的热量和营养，请**直接使用你自带的庞大常识知识库进行精准估算**，绝对不要去调用任何查食物的工具！"
        )
        current_messages = [{"role": "system", "content": system_prompt}] + st.session_state.messages

        try:
            response = client.chat.completions.create(
                model="glm-4-flash", 
                messages=current_messages, 
                tools=tools,
                tool_choice="auto" 
            )
            response_msg = response.choices[0].message
            
            if response_msg.tool_calls:
                current_messages.append(response_msg)
                
                for tool_call in response_msg.tool_calls:
                    try:
                        args = json.loads(tool_call.function.arguments)
                    except:
                        args = {}
                        
                    res = ""
                    # 👇 这里去掉了查食物的逻辑，只保留运动计算
                    if tool_call.function.name == "calc_exercise_calories":
                        ex_type = args.get("exercise_type", "快走")
                        dur = args.get("duration_min", 30)
                        wt = args.get("weight", 70)
                        inc = args.get("incline", 0)
                        spd = args.get("speed", 0)
                        
                        # 🚨 终极反杀 1：只要用户提了爬坡，不管大模型传啥，强行覆盖！
                        if "爬坡" in prompt or "跑步" in prompt:
                            ex_type = "爬坡"

                        # 🚨 终极反杀 2：正则强行提取坡度和速度
                        if "坡度" in prompt:
                            match = re.search(r'坡度(\d+)', prompt)
                            if match: inc = int(match.group(1))
                        if "速度" in prompt:
                            match = re.search(r'速度([\d\.]+)', prompt)
                            if match: spd = float(match.group(1))
                            
                        res = calc_exercise_calories(ex_type, dur, wt, inc, spd)
                    
                    st.success(f"📊 数据核对：{res}")
                    
                    current_messages.append({
                        "role": "tool", 
                        "tool_call_id": tool_call.id, 
                        "content": f"{res}。请直接复述结果，不要修改数字！"
                    })
                
                # 🚨 终极反杀 3：加一句提示词，防止它把底层代码当文本吐出来
                current_messages.append({"role": "system", "content": "请直接用自然语言回答，千万不要在回复中输出任何工具调用的格式或代码！"})
                
                final_res = client.chat.completions.create(model="glm-4-flash", messages=current_messages)
                ans = final_res.choices[0].message.content
            else:
                ans = response_msg.content
                
            st.session_state.messages.append({"role": "assistant", "content": ans})
            with st.chat_message("assistant"):
                st.markdown(ans)
                
        except Exception as e:
            st.error(f"大模型抽风了，请再试一次。错误：{e}")