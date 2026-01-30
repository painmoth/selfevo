"""
API数据模型
"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class ChatRequest(BaseModel):
    """对话请求"""
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    """对话响应"""
    response: str
    session_id: str
    emotion: Optional[str] = None  # 情绪标签
    sprite_path: Optional[str] = None  # sprites图片路径


class FeedbackRequest(BaseModel):
    """反馈请求"""
    task: str
    response: str
    satisfaction: int  # 1-10
    description: Optional[str] = None
    session_id: str


class FeedbackResponse(BaseModel):
    """反馈响应"""
    success: bool
    feedback_report: Optional[str] = None
    message: str


class SessionResponse(BaseModel):
    """会话响应"""
    session_id: str
    message: str


class ConfigResponse(BaseModel):
    """配置响应"""
    llm_provider: str
    llm_model: str
    debug_log_level: int


class MemoryResponse(BaseModel):
    """记忆响应"""
    content: str


class PromptResponse(BaseModel):
    """Prompt响应"""
    content: str


class SessionInfo(BaseModel):
    id: str
    title: str
    created_at: float
    updated_at: float
    message_count: int


class SessionListResponse(BaseModel):
    sessions: List[SessionInfo]
    count: int


class MessageItem(BaseModel):
    role: str
    content: str
    ts: float


class SessionMessagesResponse(BaseModel):
    session_id: str
    messages: List[MessageItem]


class RenameSessionRequest(BaseModel):
    title: str
