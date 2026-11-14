import streamlit as st
import json
from openai import OpenAI

# 页面设置
st.set_page_config(page_title="AI 私教 Agent", page_icon="🏃")
st.title("🏃 专业 AI 私教 Agent (RAG版)")
st.write("我不仅会算热量，我脑子里还有一本《健身秘籍》。")

# 尝试从 Streamlit 的保险箱里读取 Key
# 如果本地测试没配置，就会显示输入框；如果配置了云端，就会隐藏输入框
try:
    api_key = st.secrets["ZHIPU_API_KEY"]
except:
    with st.sidebar:
        st.header("本地测试设置")
        api_key = st.text_input("请输入你的智谱 API Key", type="password")

# 1. 模拟你的“私有知识库”（RAG 的数据源）
knowledge_base = """
【秘籍第一条】跑步：每小时消耗约 600 卡路里。建议初学者先从慢跑开始，每次30分钟。
【秘籍第二条】游泳：每小时消耗约 800 卡路里。游泳对膝盖损伤极小，适合大体重人群。
【秘籍第三条】练胸肌：推荐俯卧撑，每次做4组，每组做到力竭。新手不要上大重量。
"""

# 2. 简单的检索函数（匹配关键词）
def retrieve_info(query):
    keywords = ["跑步", "游泳", "胸肌", "俯卧撑"]
    for word in keywords:
        if word in query:
            return knowledge_base
    return "知识库中没有相关资料。"

# 3. 本地工具函数（Agent）
def calculate_calories(sport):
    if sport == "跑步": return 600
    elif sport == "游泳": return 800
    else: return 100

tools = [{
    "type": "function",
    "function": {
        "name": "calculate_calories",
        "description": "计算某项运动消耗的卡路里",
        "parameters": {
            "type": "object",
            "properties": {
                "sport": {"type": "string", "description": "运动项目名称"}
            },
            "required": ["sport"]
        }
    }
}]

if "messages" not in st.session_state:
    st.session_state.messages = []

# 显示历史聊天记录
for message in st.session_state.messages:
    role = message.get("role") if isinstance(message, dict) else getattr(message, "role", None)
    content = message.get("content") if isinstance(message, dict) else getattr(message, "content", None)
    if role in ["user", "assistant"] and isinstance(content, str):
        with st.chat_message(role):
            st.markdown(content)

if prompt := st.chat_input("比如：游泳有什么好处？或者我跑了1小时消耗多少？"):
    if not api_key:
        st.info("请在左侧输入 API Key！")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    client = OpenAI(api_key=api_key, base_url="https://open.bigmodel.cn/api/paas/v4/")

    with st.spinner("AI 正在查阅秘籍并思考..."):
        # 🚨 RAG 核心：先查资料
        context = retrieve_info(prompt)
        system_prompt = f"你是一个专业的健身教练。请优先根据以下参考资料回答问题：\n{context}"
        
        current_messages = [{"role": "system", "content": system_prompt}] + st.session_state.messages

        # Agent 调用
        response = client.chat.completions.create(
            model="glm-4-flash",
            messages=current_messages,
            tools=tools
        )
        
        response_message = response.choices[0].message
        
        if response_message.tool_calls:
            current_messages.append(response_message)
            for tool_call in response_message.tool_calls:
                function_args = json.loads(tool_call.function.arguments)
                result = calculate_calories(function_args.get("sport"))
                current_messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(result)
                })
            
            second_response = client.chat.completions.create(
                model="glm-4-flash",
                messages=current_messages
            )
            final_answer = second_response.choices[0].message.content
        else:
            final_answer = response_message.content

        st.session_state.messages.append({"role": "assistant", "content": final_answer})
        with st.chat_message("assistant"):
            st.markdown(final_answer)