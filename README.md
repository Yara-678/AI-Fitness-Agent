# 🏋️ 全能 AI 私教 (RAG + Agent)

这是一个基于大语言模型（LLM）开发的智能健身与营养助手。它不仅能陪你聊天，还能像真人教练一样根据你的身体参数精准计算热量，并查阅权威营养指南给出建议。

🔗 **在线体验地址**：[点击这里体验](https://agent-grgraqgjpspg3ynegwjcn.streamlit.app) 
*(注：若链接打开较慢，请耐心等待几秒，云端正在唤醒)*

## ✨ 核心功能

1. **📚 本地 RAG 知识库检索**：喂入权威的《健身与营养指南》文本，系统会自动进行分词检索。当用户询问营养或减脂问题时，模型会严格基于参考资料回答，彻底解决大模型的“幻觉”问题。
2. **🧮 Function Calling 多工具调用**：大模型能够自主解析用户的意图，并调度本地 Python 脚本。例如：识别用户输入的“坡度、速度、时长、体重”，精准计算运动消耗的卡路里；或查询本地数据库计算食物宏量营养素。
3. **🛡️ 防崩溃与强兜底机制**：针对开源小模型偶尔的“偷懒”或参数提取失败，代码中设计了正则表达式强行提取与默认参数兜底，确保 100% 给出准确回答。

## 🛠️ 技术栈

* **核心语言**：Python 3.10+
* **Web 框架**：Streamlit
* **大模型集成**：OpenAI SDK (兼容智谱 GLM-4 接口)
* **文本处理**：LangChain
* **部署**：GitHub + Streamlit Community Cloud

本地运行指南

如果想在本地运行本项目，请按以下步骤操作：

1. 克隆仓库：
   ```bash
   git clone https://github.com/Yara-678/AI-Fitness-Agent.git
2. 安装依赖：
   pip install -r requirements.txt
3. 运行应用：
   streamlit run app.py
4. 在网页左侧输入你的智谱 API Key 即可开始使用。
