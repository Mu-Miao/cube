# app/api/v1/__init__.py
# API v1 版本路由初始化文件
# 统一注册 v1 版本的所有 API 路由到 FastAPI 应用

from fastapi import APIRouter

from app.api.v1 import auth, device, data, control

# 创建 v1 版本的路由聚合器
api_router = APIRouter(prefix="/api/v1")

# 注册各模块路由，统一挂载到 /api/v1 前缀下
api_router.include_router(auth.router)     # /api/v1/auth/*
api_router.include_router(device.router)   # /api/v1/device/*
api_router.include_router(data.router)     # /api/v1/data/*
api_router.include_router(control.router)  # /api/v1/control/*
