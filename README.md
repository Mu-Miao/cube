# Cube Monorepo

Cube 的前后端整合仓库。

## 目录

- `backend/`：FastAPI、MQTT、WebSocket、OTA 与设备服务。
- `tianmu/`：Vue 3、Vite 与三套界面。

## 分支

- `backend`：原始后端独立分支，继续保留维护。
- `tianmu`：原始前端独立分支，继续保留维护。
- `cube-main`：前后端旧版整合基线。
- `cube-advanced`：在 `cube-main` 基础上加入安全、架构和前端重构。

## 本地验证

后端：

```bash
cd backend
/opt/miniconda3/envs/backend/bin/python -m pytest tests/
```

前端：

```bash
cd tianmu
npm ci
npm run type-check
npm run test:unit -- --run
npm run build
```

