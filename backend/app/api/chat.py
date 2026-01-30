"""
对话API
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.models import ChatRequest, ChatResponse
from app.agent_manager import agent_manager
from app.emotion_detector import detect_emotion, get_sprite_path
import json

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """非流式对话接口"""
    # 获取或创建会话
    if not request.session_id:
        session_id = agent_manager.create_session()
    else:
        session_id = request.session_id
        agent_manager.get_or_create_agent(session_id)
    
    # 获取Agent并发送消息
    agent = agent_manager.get_or_create_agent(session_id)
    # 先持久化用户消息
    agent_manager.append_message(session_id, "user", request.message)
    response = agent.chat(request.message)
    # 再持久化助手消息
    agent_manager.append_message(session_id, "assistant", response)
    
    # 识别情绪（默认用关键词匹配：更快、更稳定；需要更准再升级为 LLM 分类）
    emotion = detect_emotion(response, use_llm=False)
    sprite_path = get_sprite_path(emotion)
    
    return ChatResponse(
        response=response,
        session_id=session_id,
        emotion=emotion,
        sprite_path=sprite_path
    )


@router.websocket("/chat/stream")
async def chat_stream(websocket: WebSocket):
    """WebSocket流式对话接口"""
    await websocket.accept()
    session_id = None
    
    try:
        # 接收消息
        data = await websocket.receive_text()
        message_data = json.loads(data)
        
        message = message_data.get("message", "")
        session_id = message_data.get("session_id")
        
        if not message:
            await websocket.send_json({
                "type": "error",
                "error": "消息内容为空"
            })
            await websocket.close()
            return
        
        if not session_id:
            session_id = agent_manager.create_session()
        
        # 获取Agent
        try:
            agent = agent_manager.get_or_create_agent(session_id)
        except Exception as e:
            await websocket.send_json({
                "type": "error",
                "error": f"创建Agent失败: {str(e)}"
            })
            await websocket.close()
            return
        
        # 发送开始信号
        await websocket.send_json({
            "type": "start",
            "session_id": session_id
        })
        
        # 调用LLM（这里需要修改为流式）
        # 暂时使用非流式，后续可以优化
        try:
            agent_manager.append_message(session_id, "user", message)
            response = agent.chat(message)
            agent_manager.append_message(session_id, "assistant", response)
        except Exception as e:
            await websocket.send_json({
                "type": "error",
                "error": f"LLM调用失败: {str(e)}"
            })
            await websocket.close()
            return
        
        # 识别情绪
        emotion = detect_emotion(response, use_llm=False)
        sprite_path = get_sprite_path(emotion)
        
        # 模拟流式输出（逐字符发送）
        for char in response:
            await websocket.send_json({
                "type": "chunk",
                "content": char,
                "session_id": session_id
            })
        
        # 发送完成信号（包含情绪信息）
        await websocket.send_json({
            "type": "done",
            "session_id": session_id,
            "emotion": emotion,
            "sprite_path": sprite_path
        })
        
        await websocket.close()
            
    except WebSocketDisconnect:
        print("WebSocket客户端断开连接")
    except json.JSONDecodeError as e:
        print(f"JSON解析错误: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "error": f"消息格式错误: {str(e)}"
            })
            await websocket.close()
        except:
            pass
    except Exception as e:
        print(f"WebSocket处理错误: {e}")
        import traceback
        traceback.print_exc()
        try:
            await websocket.send_json({
                "type": "error",
                "error": str(e)
            })
            await websocket.close()
        except:
            pass
