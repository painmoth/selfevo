"""
配置API
"""
from fastapi import APIRouter
from app.models import ConfigResponse
from app.agent_manager import agent_manager

router = APIRouter()


@router.get("/config", response_model=ConfigResponse)
async def get_config():
    """获取当前配置"""
    return ConfigResponse(
        llm_provider=agent_manager.config.get("LLM_PROVIDER", "openai"),
        llm_model=agent_manager.config.get("LLM_MODEL", agent_manager.config.get("MODEL", "gpt-4o")),
        debug_log_level=agent_manager.debug_log_level
    )
