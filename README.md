# Self Evolution Agent

具备记忆与情感反馈的对话 Agent，支持 Web 端聊天与流式输出。后端基于 FastAPI，前端为 React，LLM 支持 OpenAI / OpenRouter 等。

## 功能

- **对话**：发送消息、流式回复（WebSocket）
- **会话**：多会话隔离、会话持久化
- **记忆**：长期记忆（memory.md）、系统提示（system_prompt.txt）
- **情感**：情绪检测与表情展示（Hitomi 精灵）
- **配置**：`agent.conf` 配置 LLM 提供商、模型、API 等

## 项目结构

```
selfevo/
├── agent.conf           # Agent 配置（LLM 提供商、API Key、模型等）
├── self_evol.py         # 自进化 Agent 原型（投射 / 实践 / 内化）
├── self_evol_llm.py     # 基于 LLM 的对话 Agent 核心
├── system_prompt.txt    # 系统提示词
├── memory.md            # 长期记忆
├── backend/             # FastAPI 后端
│   ├── app/
│   │   ├── main.py
│   │   ├── agent_manager.py
│   │   ├── models.py
│   │   └── api/         # chat, session, feedback, memory, config, sprites
│   └── requirements.txt
├── frontend/            # React 前端
│   └── src/
├── img_src/             # 精灵图资源（如 Hitomi 表情）
├── start_backend.sh
└── start_frontend.sh
```

## 配置

在项目根目录的 `agent.conf` 中配置 LLM（**勿将真实 API Key 提交到仓库**）：

- `LLM_PROVIDER`：`openai` 或 `openrouter`
- `LLM_API_KEY`：API 密钥（也可用环境变量 `OPENAI_API_KEY` / `LLM_API_KEY`）
- `LLM_MODEL`：模型名，如 `gpt-4o`、`google/gemini-3-flash-preview`

本地使用建议：在 `agent.conf` 中留空密钥，通过环境变量设置：

```bash
export LLM_API_KEY="your-key"
# 或
export OPENAI_API_KEY="your-openai-key"
```

## 安装与运行

### 后端

```bash
cd backend
pip install -r requirements.txt
# 或使用项目根目录脚本：
./start_backend.sh
```

后端默认：<http://localhost:8000>，API 文档：<http://localhost:8000/docs>

### 前端

```bash
cd frontend
npm install
npm run dev
# 或：./start_frontend.sh
```

前端默认：<http://localhost:3000>

### 一键启动（两个终端）

```bash
# 终端 1
./start_backend.sh

# 终端 2
./start_frontend.sh
```

## API 概览

| 接口 | 说明 |
|------|------|
| `POST /api/chat` | 非流式对话 |
| WebSocket `/api/chat/stream` | 流式对话 |
| `POST /api/session/new` | 创建新会话 |
| `GET /api/config` | 获取配置 |
| `GET /api/memory` | 获取记忆 |
| `POST /api/feedback` | 提交反馈 |

## 文档

- [README_WEB.md](README_WEB.md) — Web 端使用与待实现功能
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) — 故障排查

## License

MIT License. See [LICENSE](LICENSE).
