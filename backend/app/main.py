"""
FastAPI应用主入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api import chat, feedback, config, session, memory, sprites
import os

app = FastAPI(
    title="Self Evolution Agent API",
    description="自我进化Agent的Web API",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(feedback.router, prefix="/api", tags=["feedback"])
app.include_router(config.router, prefix="/api", tags=["config"])
app.include_router(session.router, prefix="/api", tags=["session"])
app.include_router(memory.router, prefix="/api", tags=["memory"])
app.include_router(sprites.router, prefix="/api", tags=["sprites"])

# 配置静态文件服务（用于sprites图片）
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
img_src_path = os.path.join(project_root, "img_src")
if os.path.exists(img_src_path):
    app.mount("/img_src", StaticFiles(directory=img_src_path), name="img_src")


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "Self Evolution Agent API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "ok"}
