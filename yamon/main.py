"""FastAPI application entry point"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pathlib import Path
from contextlib import asynccontextmanager
import os

# Import from yamon package
from yamon.api import metrics, websocket

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理：启动和停止后台任务"""
    # 启动时：启动后台数据收集任务
    await websocket.start_background_collector()
    yield
    # 关闭时：清理资源（如果需要）

app = FastAPI(title="Yamon API", version="1.0.0", lifespan=lifespan)

# CORS 配置（开发环境需要）
# 在生产环境中，静态文件和 API 同源，不需要 CORS
import os
if os.getenv("ENV") != "production":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],  # Vite dev server
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# API 路由
app.include_router(metrics.router, prefix="/api", tags=["metrics"])
app.include_router(websocket.router, prefix="/ws", tags=["websocket"])

# 静态文件服务（生产环境）
# 尝试多个可能的静态文件目录路径
possible_static_dirs = [
    Path(__file__).parent / "static",  # 从 yamon 包目录（安装后）
    Path(__file__).parent.parent / "frontend" / "dist",  # 从项目根目录（开发环境）
    Path(__file__).parent.parent.parent / "frontend" / "dist",  # 从项目根目录（另一种情况）
]

static_dir = None
for dir_path in possible_static_dirs:
    if dir_path.exists() and (dir_path / "index.html").exists():
        static_dir = dir_path
        break

if static_dir:
    # 如果存在静态文件，serve 它们
    assets_dir = static_dir / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")
    
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """Serve SPA - 所有非 API 路由都返回 index.html"""
        if full_path.startswith("api") or full_path.startswith("ws"):
            return {"error": "Not found"}
        
        index_path = static_dir / "index.html"
        if index_path.exists():
            return FileResponse(str(index_path))
        return {"error": "Static files not found"}

@app.get("/")
async def root():
    """根路径"""
    if static_dir:
        index_path = static_dir / "index.html"
        if index_path.exists():
            return FileResponse(str(index_path))
    return {"message": "Yamon API", "docs": "/docs"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
