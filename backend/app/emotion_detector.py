"""
情绪识别模块
从文本中识别情绪，返回对应的情绪标签（28种GoEmotions）
"""
import re
from typing import Optional

# 28种情绪标签（GoEmotions数据集）
EMOTIONS = [
    "admiration", "amusement", "anger", "annoyance", "approval", "caring",
    "confusion", "curiosity", "desire", "disappointment", "disapproval",
    "disgust", "embarrassment", "excitement", "fear", "gratitude", "grief",
    "joy", "love", "nervousness", "neutral", "optimism", "pride",
    "realization", "relief", "remorse", "sadness", "surprise"
]

# 情绪关键词映射（用于快速匹配）
EMOTION_KEYWORDS = {
    "joy": ["高兴", "开心", "快乐", "愉快", "兴奋", "joy", "happy", "glad", "pleased", "delighted"],
    "sadness": ["悲伤", "难过", "伤心", "沮丧", "sad", "sadness", "unhappy", "depressed", "melancholy"],
    "anger": ["生气", "愤怒", "恼火", "angry", "anger", "mad", "furious", "irritated"],
    "fear": ["害怕", "恐惧", "担心", "fear", "afraid", "scared", "worried", "anxious"],
    "surprise": ["惊讶", "吃惊", "surprise", "surprised", "amazed", "shocked", "astonished"],
    "disgust": ["厌恶", "恶心", "disgust", "disgusted", "revolted", "repulsed"],
    "neutral": ["中性", "neutral", "normal", "calm", "平静"],
    "excitement": ["激动", "兴奋", "excitement", "excited", "thrilled", "enthusiastic"],
    "love": ["爱", "喜欢", "love", "loved", "adore", "affection"],
    "curiosity": ["好奇", "curiosity", "curious", "wonder", "inquisitive"],
    "confusion": ["困惑", "confusion", "confused", "puzzled", "bewildered"],
    "amusement": ["有趣", "amusement", "amused", "entertained", "funny"],
    "gratitude": ["感谢", "感激", "gratitude", "grateful", "thankful", "appreciate"],
    "pride": ["骄傲", "自豪", "pride", "proud", "accomplished"],
    "relief": ["放松", "relief", "relieved", "eased", "comforted"],
    "embarrassment": ["尴尬", "embarrassment", "embarrassed", "awkward", "ashamed"],
    "disappointment": ["失望", "disappointment", "disappointed", "let down"],
    "annoyance": ["烦恼", "annoyance", "annoyed", "irritated", "bothered"],
    "approval": ["赞同", "approval", "approve", "agree", "support"],
    "disapproval": ["不赞同", "disapproval", "disapprove", "disagree", "object"],
    "caring": ["关心", "caring", "care", "concerned", "compassionate"],
    "desire": ["渴望", "desire", "want", "wish", "longing"],
    "optimism": ["乐观", "optimism", "optimistic", "hopeful", "positive"],
    "grief": ["悲痛", "grief", "grieving", "mourning", "sorrow"],
    "nervousness": ["紧张", "nervousness", "nervous", "tense", "anxious"],
    "realization": ["意识到", "realization", "realize", "understand", "comprehend"],
    "remorse": ["懊悔", "remorse", "remorseful", "regret", "guilty"],
    "admiration": ["钦佩", "admiration", "admire", "respect", "appreciate"],
}


def detect_emotion(text: str, use_llm: bool = False, llm_client=None) -> str:
    """
    从文本中检测情绪
    
    Args:
        text: 要分析的文本
        use_llm: 是否使用LLM进行更精确的分析（需要传入llm_client）
        llm_client: LLM客户端（如果use_llm=True）
    
    Returns:
        情绪标签（28种之一），默认返回"neutral"
    """
    if not text or not text.strip():
        return "neutral"
    
    text_lower = text.lower()
    
    # 如果使用LLM分析
    if use_llm and llm_client:
        try:
            prompt = f"""分析以下文本的情绪，从以下28种情绪中选择最匹配的一个：
admiration, amusement, anger, annoyance, approval, caring, confusion, curiosity, desire, 
disappointment, disapproval, disgust, embarrassment, excitement, fear, gratitude, grief, 
joy, love, nervousness, neutral, optimism, pride, realization, relief, remorse, sadness, surprise

文本：{text[:500]}

只返回情绪标签，不要其他解释。"""
            
            response = llm_client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=20
            )
            emotion = response.choices[0].message.content.strip().lower()
            
            # 验证返回的情绪是否在列表中
            if emotion in EMOTIONS:
                return emotion
        except Exception as e:
            print(f"[EmotionDetector] LLM分析失败，使用关键词匹配: {e}")
    
    # 关键词匹配（fallback）
    emotion_scores = {}
    for emotion, keywords in EMOTION_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > 0:
            emotion_scores[emotion] = score
    
    if emotion_scores:
        # 返回得分最高的情绪
        return max(emotion_scores.items(), key=lambda x: x[1])[0]
    
    # 默认返回neutral
    return "neutral"


def get_sprite_path(emotion: str, character: str = "Hitomi") -> str:
    """
    获取sprites图片路径
    
    Args:
        emotion: 情绪标签
        character: 角色名称（默认Hitomi）
    
    Returns:
        图片路径（相对于项目根目录）
    """
    # 确保emotion在有效列表中
    if emotion not in EMOTIONS:
        emotion = "neutral"
    
    # 返回可直接被前端请求的静态路径（由 FastAPI 挂载 /img_src 提供）
    return f"/img_src/{character}/{emotion}.png"
