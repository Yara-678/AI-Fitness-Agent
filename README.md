# 🏋️ 全能 AI 私教 (RAG + Agent)

这是一个基于大语言模型（LLM）开发的智能健身与营养助手。它不仅能像真人教练一样根据你的身体参数精准计算运动热量，还能查阅权威营养指南给出建议，并进行食物营养的智能估算。

🔗 **在线体验地址**：[点击这里体验](https://ai-fitness-agent-grgraqgjpspg3ynegwjjcn.streamlit.app/) 
*(注：基于 Streamlit 云端免费托管，首次打开若遇白屏，请耐心等待 30 秒加载唤醒)*

## ✨ 核心功能

1. **📚 本地 RAG 知识库检索**：喂入权威的《健身与营养指南》文本。使用 `TF-IDF` 算法与余弦相似度进行语义向量化检索，将匹配内容注入 Prompt，彻底解决大模型在垂直领域的“幻觉”问题。
2. **🧮 Agent 智能工具调度**：实现 Function Calling 机制。大模型可自主解析用户意图，并精准调度本地 Python 脚本，计算复杂的运动热量（METs）。同时，针对通用食物热量，模型会调用自身庞大的常识库进行精准估算。
3. **🛡️ 防崩溃与强兜底机制**：针对开源小模型偶尔的“偷懒”或参数提取失败，代码中设计了正则表达式强行提取与默认参数兜底机制，确保 100% 给出准确回答，防止大模型“胡编乱造”。

## 🛠️ 技术栈

* **核心语言**：Python 3.10+
* **Web 框架**：Streamlit
* **大模型集成**：OpenAI SDK (兼容智谱 GLM-4 接口)
* **NLP 检索**：Scikit-Learn (TF-IDF 算法)
* **部署**：GitHub + Streamlit Community Cloud

## 🚀 本地运行指南

如果想在本地运行本项目，请按以下步骤操作：

1. 克隆仓库：
   ```bash
   git clone https://github.com/Yara-678/AI-Fitness-Agent.git
2. 安装依赖：
   pip install -r requirements.txt
3. 运行应用：
   streamlit run app.py
4. 在网页左侧输入你的智谱 API Key 即可开始使用。
