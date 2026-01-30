# 故障排查指南

## 前端输入后没有响应

### 检查步骤

1. **检查后端是否运行**
   ```bash
   # 在项目根目录
   cd backend
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
   访问 http://localhost:8000/docs 应该能看到API文档

2. **检查前端控制台**
   - 打开浏览器开发者工具（F12）
   - 查看Console标签页
   - 查看是否有错误信息

3. **检查网络请求**
   - 打开浏览器开发者工具
   - 查看Network标签页
   - 发送消息后，应该能看到：
     - WebSocket连接（ws://localhost:8000/api/chat/stream）
     - 或REST API请求（POST /api/chat）

4. **测试REST API**
   ```bash
   curl -X POST http://localhost:8000/api/chat \
     -H "Content-Type: application/json" \
     -d '{"message": "你好"}'
   ```

5. **检查配置文件**
   - 确保 `agent.conf` 在项目根目录
   - 确保 `LLM_API_KEY` 或 `OPENAI_API_KEY` 已配置
   - 确保 `LLM_PROVIDER` 和 `LLM_MODEL` 配置正确

### 常见问题

#### 1. WebSocket连接失败
- **现象**: 控制台显示WebSocket错误
- **解决**: 代码已自动fallback到REST API，应该能正常工作
- **如果REST API也失败**: 检查后端是否运行，端口是否正确

#### 2. CORS错误
- **现象**: 浏览器控制台显示CORS相关错误
- **解决**: 检查后端CORS配置，确保允许前端域名

#### 3. 导入错误
- **现象**: 后端启动时报错，无法导入self_evol_llm
- **解决**: 确保在项目根目录运行后端，或检查agent_manager.py中的路径设置

#### 4. API Key错误
- **现象**: LLM调用失败
- **解决**: 检查agent.conf中的API Key配置

### 调试技巧

1. **查看后端日志**
   - 后端控制台会显示所有请求和错误
   - 查看是否有异常堆栈信息

2. **查看前端日志**
   - 打开浏览器控制台
   - 代码中已添加console.log，查看输出

3. **测试单个API**
   - 使用curl或Postman测试后端API
   - 访问 http://localhost:8000/docs 使用Swagger UI测试

### 快速测试

1. 测试后端健康检查：
   ```bash
   curl http://localhost:8000/health
   ```

2. 测试创建会话：
   ```bash
   curl -X POST http://localhost:8000/api/session/new
   ```

3. 测试对话（需要先创建会话）：
   ```bash
   curl -X POST http://localhost:8000/api/chat \
     -H "Content-Type: application/json" \
     -d '{"message": "你好", "session_id": "your-session-id"}'
   ```
