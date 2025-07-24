import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import routes
from dotenv import load_dotenv

app = FastAPI(
    title="简历与文本处理API (重构版)",
    description="一个结构清晰、模块化的API服务，提供简历生成与文本处理功能。"
)

# CORS 配置
origins = os.getenv("ORIGINS", "").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,        # 开发阶段可以用 ["*"] 允许所有
    allow_credentials=True,
    allow_methods=["*"],          # 允许所有 HTTP 方法，包括 OPTIONS、GET、POST 等
    allow_headers=["*"],          # 允许所有请求头
)

# 注册所有来自 routes.py 的路由
app.include_router(routes.router)

@app.get("/", tags=["Health Check"])
def read_root():
    """
    根路径健康检查接口。
    """
    return {"status": "ok", "message": "API服务已成功启动！"}









