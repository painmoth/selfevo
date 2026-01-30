"""
反馈API
"""
from fastapi import APIRouter
from app.models import FeedbackRequest, FeedbackResponse
from app.agent_manager import agent_manager

router = APIRouter()


@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(request: FeedbackRequest):
    """提交反馈"""
    try:
        feedback_agent = agent_manager.get_or_create_feedback_agent(request.session_id)
        agent = agent_manager.get_or_create_agent(request.session_id)
        
        # 收集反馈
        feedback_data = {
            "satisfaction": str(request.satisfaction),
            "description": request.description or "无文字反馈"
        }
        
        # 生成反馈报告
        feedback_report = feedback_agent.generate_feedback_report(
            task=request.task,
            response=request.response,
            satisfaction=str(request.satisfaction),
            description=request.description or "无文字反馈"
        )
        
        # 记录到记忆
        agent.update_memory(
            issue=request.task,
            solution=f"User satisfaction: {request.satisfaction}/10. Response: {request.response[:200]}...",
            feedback=request.description
        )
        
        # 如果满意度低，触发进化
        if request.satisfaction < 7:
            agent.evolve_prompt(feedback_report)
            return FeedbackResponse(
                success=True,
                feedback_report=feedback_report,
                message="反馈已记录，已触发Agent进化"
            )
        
        return FeedbackResponse(
            success=True,
            feedback_report=feedback_report,
            message="反馈已记录"
        )
        
    except Exception as e:
        return FeedbackResponse(
            success=False,
            message=f"处理反馈时出错: {str(e)}"
        )
