"""
Agent会话管理器
管理多个用户的Agent实例，确保会话隔离
"""
import uuid
import sys
import os
from typing import Dict, Optional

from app.storage import SessionStore

# 添加项目根目录到路径，以便导入self_evol_llm
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from self_evol_llm import ManuscriptAgent, FeedbackAgent, create_llm_client, load_config


class AgentManager:
    """管理多个Agent会话"""
    
    def __init__(self):
        self.agents: Dict[str, ManuscriptAgent] = {}
        self.feedback_agents: Dict[str, FeedbackAgent] = {}
        # 获取项目根目录的agent.conf路径
        # __file__ 是 backend/app/agent_manager.py
        # 需要回到项目根目录
        current_file_dir = os.path.dirname(os.path.abspath(__file__))
        # backend/app -> backend -> 项目根目录
        project_root = os.path.abspath(os.path.join(current_file_dir, '../..'))
        config_path = os.path.join(project_root, "agent.conf")
        
        # 如果找不到，尝试从当前工作目录查找
        if not os.path.exists(config_path):
            cwd_config = os.path.abspath("agent.conf")
            if os.path.exists(cwd_config):
                config_path = cwd_config
                print(f"[AgentManager] 使用当前工作目录的配置文件: {config_path}")
            else:
                # 尝试从backend目录的上一级查找
                backend_config = os.path.abspath(os.path.join(current_file_dir, '..', '..', 'agent.conf'))
                if os.path.exists(backend_config):
                    config_path = backend_config
                    print(f"[AgentManager] 使用backend上级目录的配置文件: {config_path}")
                else:
                    print(f"[警告] 未找到配置文件，尝试的路径:")
                    print(f"  - {os.path.abspath(os.path.join(project_root, 'agent.conf'))}")
                    print(f"  - {cwd_config}")
                    print(f"  - {backend_config}")
        
        print(f"[AgentManager] 加载配置文件: {config_path}")
        print(f"[AgentManager] 配置文件存在: {os.path.exists(config_path)}")
        
        self.config = load_config(config_path)
        print(f"[AgentManager] 已加载配置项: {list(self.config.keys())}")
        
        # 检查API Key
        api_key = self.config.get("LLM_API_KEY", "").strip() or self.config.get("OPENAI_API_KEY", "").strip()
        if not api_key:
            print("[警告] 未找到API Key配置！请在agent.conf中设置LLM_API_KEY或OPENAI_API_KEY")
        else:
            # 只显示前4个和后4个字符，中间用*代替
            masked_key = api_key[:4] + "*" * (len(api_key) - 8) + api_key[-4:] if len(api_key) > 8 else "***"
            print(f"[AgentManager] API Key已配置: {masked_key} (长度: {len(api_key)})")
        # 初始化会话存储（落盘）
        store_path = os.path.abspath(os.path.join(project_root, "backend", "data", "sessions.json"))
        self.store = SessionStore(store_path=store_path)
        print(f"[AgentManager] Session store: {store_path}")

        self._init_default_client()
    
    def _init_default_client(self):
        """初始化默认的LLM客户端"""
        # 读取配置
        llm_provider = self.config.get("LLM_PROVIDER", "openai").lower()
        api_key = self.config.get("LLM_API_KEY", "")
        if not api_key:
            api_key = self.config.get("OPENAI_API_KEY", "")
        
        # 如果还是没有，尝试从环境变量读取
        if not api_key:
            import os
            if llm_provider == "openrouter":
                api_key = os.getenv("OPENROUTER_API_KEY", "")
            else:
                api_key = os.getenv("OPENAI_API_KEY", "")
        
        if not api_key:
            raise ValueError(
                "未找到API Key！请在agent.conf中设置LLM_API_KEY或OPENAI_API_KEY，"
                "或设置环境变量OPENAI_API_KEY/OPENROUTER_API_KEY"
            )
        
        model = self.config.get("LLM_MODEL", self.config.get("MODEL", "gpt-4o"))
        base_url = self.config.get("LLM_BASE_URL", "")
        if not base_url and llm_provider == "openrouter":
            base_url = "https://openrouter.ai/api/v1"
        
        debug_log_level_str = self.config.get("DEBUG_LOG_LEVEL", "0")
        try:
            debug_log_level = int(debug_log_level_str)
            if debug_log_level < 0 or debug_log_level > 3:
                debug_log_level = 0
        except ValueError:
            debug_log_level = 0
        
        print(f"[AgentManager] 初始化LLM客户端: provider={llm_provider}, model={model}")
        
        # 创建客户端
        try:
            self.default_client = create_llm_client(
                provider=llm_provider,
                api_key=api_key,
                base_url=base_url if base_url else None,
                model=model
            )
            self.default_model = model
            self.debug_log_level = debug_log_level
            print("[AgentManager] LLM客户端初始化成功")
        except Exception as e:
            print(f"[AgentManager] LLM客户端初始化失败: {e}")
            raise
    
    def get_or_create_agent(self, session_id: str) -> ManuscriptAgent:
        """获取或创建Agent实例"""
        if session_id not in self.agents:
            self.agents[session_id] = ManuscriptAgent(
                client=self.default_client,
                model=self.default_model,
                debug_log_level=self.debug_log_level
            )
            # 恢复历史消息（如果有）
            self._restore_agent_history(session_id)
        return self.agents[session_id]

    def _restore_agent_history(self, session_id: str) -> None:
        """从存储恢复该 session 的对话历史到 agent.conversation_history"""
        agent = self.agents.get(session_id)
        if not agent:
            return
        messages = self.store.get_messages(session_id)
        # 仅恢复 user/assistant 消息；system 由 agent.chat 内部动态构建
        if not messages:
            return

        # 构建 system_message（与 ManuscriptAgent.chat 的逻辑保持一致）
        system_p = agent.get_current_prompt()
        memory_context = agent.get_memory_context()
        system_message = system_p
        if memory_context:
            system_message += f"\n\n[Historical Experience Memory]\n{memory_context[:2000]}"

        agent.conversation_history = [{"role": "system", "content": system_message}]
        for m in messages:
            role = m.get("role")
            if role in ("user", "assistant"):
                agent.conversation_history.append({"role": role, "content": m.get("content", "")})
    
    def get_or_create_feedback_agent(self, session_id: str) -> FeedbackAgent:
        """获取或创建FeedbackAgent实例"""
        if session_id not in self.feedback_agents:
            self.feedback_agents[session_id] = FeedbackAgent(
                client=self.default_client,
                model=self.default_model
            )
        return self.feedback_agents[session_id]
    
    def create_session(self) -> str:
        """创建新会话"""
        session_id = str(uuid.uuid4())
        # 先创建存储记录
        self.store.create_session(session_id=session_id)
        # 预创建Agent实例
        self.get_or_create_agent(session_id)
        return session_id
    
    def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        if session_id in self.agents:
            del self.agents[session_id]
        if session_id in self.feedback_agents:
            del self.feedback_agents[session_id]
        return self.store.delete_session(session_id)
    
    def list_sessions(self) -> list:
        """列出所有会话ID"""
        return self.store.list_sessions()
    
    def reset_session(self, session_id: str) -> bool:
        """重置会话的对话历史"""
        if session_id in self.agents:
            self.agents[session_id].reset_conversation()
        return self.store.reset_messages(session_id)

    def append_message(self, session_id: str, role: str, content: str) -> None:
        self.store.append_message(session_id=session_id, role=role, content=content)

    def get_messages(self, session_id: str):
        return self.store.get_messages(session_id)

    def rename_session(self, session_id: str, title: str) -> bool:
        return self.store.rename_session(session_id=session_id, title=title)


# 全局Agent管理器实例
agent_manager = AgentManager()
