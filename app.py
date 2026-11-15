import streamlit as st
import json
import os
from openai import OpenAI
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from tool import get_food_info, calc_exercise_calories

st.set_page_config(page_title="全能 AI 私教", page_icon="🏋️")
st.title("🏋️ 全能 AI 私教 ")

with st.sidebar:
    st.header("设置")
    api_key = st.text_input("请输入 API Key", type="password")

if not api_key:
    st.info("请先在左侧输入 API Key！")
    st.stop()

client = OpenAI(api_key=api_key, base_url="https://open.bigmodel.cn/api/paas/v4/")

# ================= 1. 查书引擎 =================
@st.cache_resource(show_spinner="正在阅读权威书籍...")
def init_rag_engine():
    try:
        if not os.path.exists("data/book.md"): return []
        loader = TextLoader("data/book.md", encoding="utf-8")
        docs = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=50)
        return text_splitter.split_documents(docs)
    except: return []

def local_search(query, splits):
    if not splits: return ""
    keywords = [kw for kw in list(query) if kw.strip()]
    matched = []
    for doc in splits:
        if sum(1 for kw in keywords if kw in doc.page_content) >= 2:
            matched.append(doc.page_content)
    return "\n".join(matched[:2]) if matched else "查无资料。"

splits = init_rag_engine()
# =======================================================

tools = [
    {
        "type": "function", 
        "function": {
            "name": "get_food_info", 
            "description": "查询食物每百克的热量，必须传入食物名字", 
            "parameters": {"type": "object", "properties": {"food_name": {"type": "string"}}, "required": ["food_name"]}
        }
    },
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

if prompt := st.chat_input("今天练了什么？或者想了解什么健康问题？"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.spinner("教练思考中..."):
        context = local_search(prompt, splits)
        system_prompt = f"你是一个专业教练。参考资料：\n{context}\n如果用户问热量，必须调用工具！"
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
                    # 🚨 防盗门1：拦截参数解析报错
                    try:
                        args = json.loads(tool_call.function.arguments)
                    except:
                        args = {}
                        
                    res = ""
                    if tool_call.function.name == "get_food_info":
                        food = args.get("food_name", "苹果") # 没传就默认苹果
                        res = get_food_info(food)
                    elif tool_call.function.name == "calc_exercise_calories":
                        # 🚨 防盗门2：强制补齐大模型漏掉的参数
                        ex_type = args.get("exercise_type", "跑步")
                        dur = args.get("duration_min", 60)
                        wt = args.get("weight", 70)
                        inc = args.get("incline", 0)
                        spd = args.get("speed", 0)
                        
                        # 如果大模型把速度/坡度漏了，强行从用户的提问里正则提取
                        if inc == 0 and "坡度" in prompt:
                            import re
                            match = re.search(r'坡度(\d+)', prompt)
                            if match: inc = int(match.group(1))
                        if spd == 0 and "速度" in prompt:
                            import re
                            match = re.search(r'速度([\d\.]+)', prompt)
                            if match: spd = float(match.group(1))
                            
                        res = calc_exercise_calories(ex_type, dur, wt, inc, spd)
                    
                    # 在界面上显示正确的计算结果
                    st.success(f"📊 数据核对：{res}")
                    
                    current_messages.append({
                        "role": "tool", 
                        "tool_call_id": tool_call.id, 
                        "content": f"{res}。请直接复述结果，不要修改数字！"
                    })
                
                final_res = client.chat.completions.create(model="glm-4-flash", messages=current_messages)
                ans = final_res.choices[0].message.content
            else:
                ans = response_msg.content
                
            st.session_state.messages.append({"role": "assistant", "content": ans})
            with st.chat_message("assistant"):
                st.markdown(ans)
                
        except Exception as e:
            st.error(f"大模型抽风了，请再问一遍。错误：{e}")