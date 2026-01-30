"""
记忆和Prompt API
"""
from fastapi import APIRouter
from app.models import MemoryResponse, PromptResponse
import os

router = APIRouter()


@router.get("/memory", response_model=MemoryResponse)
async def get_memory():
    """获取记忆内容"""
    memory_file = "memory.md"
    if os.path.exists(memory_file):
        with open(memory_file, "r", encoding="utf-8") as f:
            content = f.read()
    else:
        content = "# Agent Experience Memory\n\n"
    
    return MemoryResponse(content=content)


@router.get("/prompt", response_model=PromptResponse)
async def get_prompt():
    """获取当前Prompt"""
    prompt_file = "system_prompt.txt"
    if os.path.exists(prompt_file):
        with open(prompt_file, "r", encoding="utf-8") as f:
            content = f.read()
    else:
        content = "You are an expert coder and helpful assistant. Solve problems step by step."
    
    return PromptResponse(content=content)
