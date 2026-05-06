"""
FastAPI Application
取名大师 - AI智能取名服务主应用
兼容 Vercel Serverless Functions
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.routers import naming, user

# 创建FastAPI应用
app = FastAPI(
    title="取名大师 NameMaster API",
    description="AI智能取名服务 - 输入姓氏和期望，从国学典籍、诗词、五行八字中为你取好名",
    version="1.0.0",
    docs_url="/docs" if os.getenv("VERCEL") is None else None,
    redoc_url="/redoc" if os.getenv("VERCEL") is None else None
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 注册路由
app.include_router(naming.router)
app.include_router(user.router)


# 健康检查
@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "取名大师 NameMaster",
        "version": "1.0.0"
    }


# 根路径 - 返回前端页面
@app.get("/")
async def root():
    """返回前端页面"""
    static_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
    index_path = os.path.join(static_path, "index.html")
    
    if os.path.exists(index_path):
        return FileResponse(index_path)
    
    return {
        "message": "取名大师 API",
        "version": "1.0.0",
        "docs": "/docs" if os.getenv("VERCEL") is None else "API文档在生产环境中已禁用",
        "endpoints": {
            "generate": "POST /api/naming/generate",
            "types": "GET /api/naming/types",
            "styles": "GET /api/naming/styles",
            "pricing": "GET /api/user/pricing"
        }
    }


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理"""
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": str(exc),
            "code": "INTERNAL_ERROR",
            "message": "服务器内部错误，请稍后重试"
        }
    )


# Vercel Serverless Functions 入口
def handler(event, context):
    """Vercel Serverless Functions 入口"""
    return app(event, context)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
