# Deployment Guide

这个项目推荐使用下面这套公开分享方案：

- 前端：Vercel
- 后端：Render

## 前端部署到 Vercel

1. 在 Vercel 新建项目并导入 GitHub 仓库
2. Root Directory 选择 `frontend`
3. Framework Preset 选择 `Vite`
4. 配置环境变量：

```env
VITE_API_BASE_URL=https://你的-render-后端域名
VITE_AMAP_API_KEY=你的高德JSAPI Key
VITE_AMAP_SECURITY_JS_CODE=你的高德安全密钥
```

5. 部署完成后访问生成的 Vercel 域名

## 后端部署到 Render

1. 在 Render 创建 `Web Service`
2. Root Directory 选择 `backend`
3. 配置：

- Build Command：`pip install -r requirements.txt`
- Start Command：`uvicorn app.main:app --host 0.0.0.0 --port $PORT`

4. 配置环境变量：

```env
APP_ENV=production
OPEN_BROWSER_ON_START=false
CORS_ALLOW_ORIGINS=https://你的-vercel-前端域名

OPENAI_API_KEY=
OPENAI_BASE_URL=
OPENAI_MODEL=

AMAP_API_KEY=
WEATHER_API_TIMEOUT_SECONDS=10

UNSPLASH_ACCESS_KEY=
IMAGE_API_TIMEOUT_SECONDS=8
IMAGE_LOOKUP_LIMIT=3
```

## 联调顺序

1. 先部署后端
2. 拿到 Render 域名
3. 把 Render 域名填到 Vercel 的 `VITE_API_BASE_URL`
4. 重新部署前端
5. 验证首页、结果页、地图、导出和 Day Detail
