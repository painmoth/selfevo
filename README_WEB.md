# Self Evolution Agent - Web端使用说明

## 项目结构

```
self_evol/
├── backend/              # FastAPI后端
│   ├── app/
│   │   ├── main.py       # 应用入口
│   │   ├── agent_manager.py  # Agent会话管理
│   │   ├── models.py     # 数据模型
│   │   └── api/          # API路由
│   └── requirements.txt
├── frontend/             # React前端
│   ├── src/
│   │   ├── components/   # React组件
│   │   └── App.tsx
│   └── package.json
└── self_evol_llm.py      # 核心Agent代码
```

## 安装和运行

### 后端

1. 安装依赖：
```bash
cd backend
pip install -r requirements.txt
```

2. 运行后端服务：
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

后端API文档：http://localhost:8000/docs

### 前端

1. 安装依赖：
```bash
cd frontend
npm install
```

2. 运行开发服务器：
```bash
npm run dev
```

前端地址：http://localhost:3000

## 功能说明

### 已实现功能

1. **基础对话**
   - 发送消息
   - 接收Agent回复
   - WebSocket流式输出

2. **会话管理**
   - 自动创建会话
   - 会话隔离

3. **API接口**
   - `/api/chat` - 非流式对话
   - `/api/chat/stream` - WebSocket流式对话
   - `/api/session/new` - 创建新会话
   - `/api/feedback` - 提交反馈
   - `/api/config` - 获取配置
   - `/api/memory` - 获取记忆
   - `/api/prompt` - 获取Prompt

### 待实现功能

1. 反馈界面
2. 配置管理界面
3. 记忆查看界面
4. 会话列表管理
5. 更好的流式输出优化

## 注意事项

1. 确保 `agent.conf` 配置正确
2. 后端需要能访问 `self_evol_llm.py` 和配置文件
3. WebSocket连接地址需要根据实际部署调整
