"""
Sprites / Emotion 调试 API
"""

from fastapi import APIRouter, Query
from app.emotion_detector import detect_emotion, get_sprite_path

router = APIRouter()


@router.get("/sprites/test")
async def sprites_test(text: str = Query("", description="要识别情绪的文本")):
    """快速验证情绪识别与 sprite_path 映射是否工作"""
    emotion = detect_emotion(text, use_llm=False)
    return {
        "emotion": emotion,
        "sprite_path": get_sprite_path(emotion),
    }

