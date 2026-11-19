import streamlit as st
import json
import os
import re
import numpy as np
from openai import OpenAI
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
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

# ================= 1. 升级版：TF-IDF 本地向量检索 =================
@st.cache_resource(show_spinner="正在构建本地向量索引...")
def init_rag_engine():
    try:
        if not os.path.exists("data/book.md"): return None, None, []
        with open("data/book.md", "r", encoding="utf-8") as f:
            text = f.read()
        
        # 按段落切片
        paragraphs = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 10]
        
        # 🚨 核心：使用 TF-IDF 算法把文字变成向量矩阵
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(paragraphs)
        
        return vectorizer, tfidf_matrix, paragraphs
    except Exception as e:
        return None, None, []

# 终极兜底语料
FALLBACK_BOOK = "减脂期不能吃蛋黄是绝对错误的！蛋黄富含优质脂肪、维生素和微量元素，每天吃1-2个全蛋不仅不会长胖，反而有利于激素分泌，对减脂大有裨益。"

# 向量检索函数
def vector_search(query, top_k=2):
    vectorizer, tfidf_matrix, paragraphs = init_rag_engine()
    if vectorizer is None or tfidf_matrix is None: 
        return FALLBACK_BOOK
    
    # 将用户的提问也变成向量
    query_vec = vectorizer.transform([query])
    
    # 🚨 核心：计算“用户提问”与“书籍段落”的余弦相似度
    similarities = cosine_similarity(query_vec, tfidf_matrix).flatten()
    
    # 找到相似度最高的前 2 个段落索引
    top_indices = similarities.argsort()[-top_k:][::-1]
    
    # 如果最高相似度大于0，说明匹配到了
    if similarities[top_indices[0]] > 0.05:
        return "\n".join([paragraphs[i] for i in top_indices])
    
    if "蛋黄" in query:
        return FALLBACK_BOOK
        
    return "知识库中未找到高度相关的段落。"
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
        # 👇 改成了调用 vector_search
        context = vector_search(prompt)
        
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