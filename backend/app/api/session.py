"""
会话管理API
"""
from fastapi import APIRouter
from app.models import SessionResponse, SessionListResponse, SessionMessagesResponse, MessageItem, SessionInfo, RenameSessionRequest
from app.agent_manager import agent_manager
from typing import List

router = APIRouter()


@router.post("/session/new", response_model=SessionResponse)
async def create_session():
    """创建新会话"""
    session_id = agent_manager.create_session()
    return SessionResponse(
        session_id=session_id,
        message="会话创建成功"
    )


@router.get("/session/list")
async def list_sessions() -> SessionListResponse:
    """获取会话列表"""
    sessions = agent_manager.list_sessions()
    # pydantic 兼容
    return SessionListResponse(
        sessions=[SessionInfo(**s) for s in sessions],
        count=len(sessions),
    )


@router.get("/session/{session_id}/messages", response_model=SessionMessagesResponse)
async def get_session_messages(session_id: str):
    """获取会话消息历史"""
    msgs = agent_manager.get_messages(session_id) or []
    return SessionMessagesResponse(
        session_id=session_id,
        messages=[MessageItem(**m) for m in msgs],
    )


@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """删除会话"""
    success = agent_manager.delete_session(session_id)
    return {
        "success": success,
        "message": "会话已删除" if success else "会话不存在"
    }


@router.post("/session/{session_id}/reset")
async def reset_session(session_id: str):
    """重置会话"""
    success = agent_manager.reset_session(session_id)
    return {
        "success": success,
        "message": "会话已重置" if success else "会话不存在"
    }


@router.put("/session/{session_id}/rename")
async def rename_session(session_id: str, request: RenameSessionRequest):
    """重命名会话"""
    success = agent_manager.rename_session(session_id=session_id, title=request.title)
    return {
        "success": success,
        "message": "会话已重命名" if success else "会话不存在或标题无效"
    }
