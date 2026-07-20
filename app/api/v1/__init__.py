# app/api/v1/__init__.py
# API v1 版本路由初始化文件
# 统一注册 v1 版本的所有 API 路由到 FastAPI 应用

from fastapi import APIRouter

from app.api.v1 import auth, device, data, control, log, admin, ai, chat, ota

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)     # /api/v1/auth/*
api_router.include_router(device.router)   # /api/v1/device/*
api_router.include_router(data.router)     # /api/v1/data/*
api_router.include_router(control.router)  # /api/v1/control/*
api_router.include_router(log.router)      # /api/v1/log/*
api_router.include_router(admin.router)    # /api/v1/admin/*
api_router.include_router(ai.router)       # /api/v1/ai/*
api_router.include_router(chat.router)     # /api/v1/chat/*
api_router.include_router(ota.router)      # /api/v1/ota/*
