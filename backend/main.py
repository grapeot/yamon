"""FastAPI application entry point"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pathlib import Path
import os

from backend.api import metrics, websocket

app = FastAPI(title="Yamon API", version="1.0.0")

# CORS 配置（开发环境需要）
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
static_dir = Path(__file__).parent / "static"
if static_dir.exists() and (static_dir / "index.html").exists():
    # 如果存在静态文件，serve 它们
    app.mount("/assets", StaticFiles(directory=static_dir / "assets"), name="assets")
    
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """Serve SPA - 所有非 API 路由都返回 index.html"""
        if full_path.startswith("api") or full_path.startswith("ws"):
            return {"error": "Not found"}
        
        index_path = static_dir / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
        return {"error": "Static files not found"}

@app.get("/")
async def root():
    """根路径"""
    index_path = static_dir / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "Yamon API", "docs": "/docs"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

