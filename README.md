# Travel Agent Project

一个自己从 0 到 1 持续迭代的智能旅行助手项目。

这个项目围绕“输入旅行需求 -> 生成可执行旅行计划 -> 地图与预算联动 -> 支持编辑、重规划与导出”这条完整链路展开，目标不是只生成一段推荐文案，而是做出一个更接近真实产品体验的 AI 旅行规划工具。

---

## 项目简介

用户输入出发地、目的地、日期、预算和偏好后，系统会自动生成包含以下信息的多日旅行计划：

- 每日景点安排
- 真实天气信息
- 酒店推荐
- 餐饮安排
- 轻量交通建议
- 地图点位与路线可视化
- 预算拆分
- 可编辑、可重规划、可导出的结果页

整个项目采用前后端分离结构，后端通过多 Agent + 外部服务的方式组织能力，前端负责结果可视化、交互编辑和导出体验。

---

## 核心功能

- 基于用户输入自动生成多日旅行计划
- 接入真实景点搜索，返回景点名称、地址、坐标、分类等信息
- 接入真实天气服务，并提供 fallback 兜底
- 酒店推荐支持真实 POI 搜索 + 规则估算价格
- 餐饮安排支持早餐 / 午餐 / 晚餐 / 小吃
- 支持地图打点、路线高亮、按天查看路线
- 支持预算拆分：酒店 / 门票 / 餐饮 / 其他
- 支持删除景点、调整顺序、单日重规划
- 支持导出图片和 PDF
- 支持 Day Detail 单日详情页

---

## 技术栈

### 前端

- Vue 3
- TypeScript
- Vite
- Vue Router
- Axios
- html2canvas
- jsPDF

### 后端

- FastAPI
- Pydantic
- Uvicorn
- OpenAI / DeepSeek 兼容大模型接口
- Python 标准库 HTTP 请求

### 外部服务

- 高德地图 POI / JS API
- Open-Meteo 天气服务
- Unsplash 图片搜索

---

## 系统架构

项目后端按 `API -> Orchestrator -> Agents -> Services / Tools` 分层组织，前端按“页面 + 组件 + store”组织状态与交互。

### 前端

- `Home.vue`
  - 收集用户需求并发起旅行计划生成
- `Result.vue`
  - 展示总览、预算、地图、每日行程、导出入口
- `DayCard.vue`
  - 渲染每日行程摘要与展开内容
- `DayDetail.vue`
  - 展示单日完整 itinerary 页面
- `stores/trip.ts`
  - 管理可编辑 trip plan、预算重算与 sessionStorage 恢复

### 后端

- `api/trip.py`
  - 提供完整行程生成和单日重规划接口
- `orchestrators/trip_orchestrator.py`
  - 串联景点、天气、酒店、餐饮、planner 等模块
- `agents/`
  - `attraction_agent.py`：景点候选生成
  - `weather_agent.py`：天气查询
  - `hotel_agent.py`：酒店推荐
  - `meal_agent.py`：餐饮候选生成
  - `planner_agent.py`：大模型规划与后处理
- `services/`
  - 封装 POI、天气、图片、LLM 请求能力
- `tools/provider.py`
  - 作为共享工具入口，为后续更 MCP 风格的工具接入预留结构

更多说明见 [architecture.md](./docs/architecture.md)。

---

## 本地运行

### 启动后端

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

默认地址：

```text
http://127.0.0.1:8000
```

接口文档：

```text
http://127.0.0.1:8000/docs
```

### 启动前端

```powershell
cd frontend
npm install
npm run dev
```

默认地址：

```text
http://127.0.0.1:5173
```

---

## 环境变量说明

### 后端 `.env`

参考 [backend/.env.example](./backend/.env.example)

```env
APP_ENV=development
APP_HOST=127.0.0.1
APP_PORT=8000
OPEN_BROWSER_ON_START=true
CORS_ALLOW_ORIGINS=http://127.0.0.1:5173,http://localhost:5173

OPENAI_API_KEY=
OPENAI_BASE_URL=
OPENAI_MODEL=

AMAP_API_KEY=
WEATHER_API_TIMEOUT_SECONDS=10

UNSPLASH_ACCESS_KEY=
IMAGE_API_TIMEOUT_SECONDS=8
IMAGE_LOOKUP_LIMIT=3
```

### 前端 `.env`

参考 [frontend/.env.example](./frontend/.env.example)

```env
VITE_API_BASE_URL=
VITE_AMAP_API_KEY=
VITE_AMAP_SECURITY_JS_CODE=
```

说明：

- `VITE_API_BASE_URL`
  - 本地开发可以留空，使用 Vite 代理访问 `/api`
  - 部署到 Vercel 后，需要填写 Render 后端公网地址，例如 `https://your-backend.onrender.com`
- `VITE_AMAP_API_KEY`
  - 高德 JS API Key
- `VITE_AMAP_SECURITY_JS_CODE`
  - 高德安全密钥

---

## 部署说明

推荐采用下面这套最轻量的上线方案：

- frontend：部署到 Vercel
- backend：部署到 Render

这样前端是静态站点，后端是独立 API 服务，适合公开分享和后续继续迭代。

### 1. 前端部署到 Vercel

建议把 Vercel 项目的 Root Directory 设置为：

```text
frontend
```

构建配置：

- Framework Preset：`Vite`
- Build Command：`npm run build`
- Output Directory：`dist`

前端需要在 Vercel 配置这些环境变量：

```env
VITE_API_BASE_URL=https://你的-render-后端域名
VITE_AMAP_API_KEY=你的高德JSAPI Key
VITE_AMAP_SECURITY_JS_CODE=你的高德安全密钥
```

其中 `VITE_API_BASE_URL` 必须指向 Render 部署后的后端地址，例如：

```text
https://travel-agent-backend.onrender.com
```

### 2. 后端部署到 Render

建议在 Render 创建一个 `Web Service`，并把 Root Directory 设置为：

```text
backend
```

构建和启动配置：

- Build Command：`pip install -r requirements.txt`
- Start Command：`uvicorn app.main:app --host 0.0.0.0 --port $PORT`

后端需要在 Render 配置这些环境变量：

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

其中 `CORS_ALLOW_ORIGINS` 至少要包含你的前端 Vercel 域名，例如：

```text
https://travel-agent-project.vercel.app
```

如果后面绑定自定义域名，也要一并加进去，多个域名用英文逗号分隔。

### 3. 前后端如何连通

上线顺序建议是：

1. 先部署后端到 Render
2. 拿到 Render 后端公网地址
3. 再部署前端到 Vercel
4. 在 Vercel 配置 `VITE_API_BASE_URL`
5. 重新触发前端部署

这样前端就会把所有 API 请求发到线上后端，而不再访问本地地址。

### 4. Vue Router 刷新问题

项目前端使用了 Vue Router history 模式，所以部署到 Vercel 时需要保留 SPA rewrite 配置。

仓库中已经提供：

- [frontend/vercel.json](./frontend/vercel.json)

它会把非静态资源请求回退到 `index.html`，避免刷新 `/result` 或 `/trip/day/:dayIndex` 时出现 404。

---

## 上线后测试顺序

建议按这个顺序验证：

1. 打开前端首页  
   确认首页能正常打开，样式和静态资源正常加载。

2. 测试后端连通  
   在前端输入一组简单参数，确认不会出现“无法连接后端服务”。

3. 测试生成旅行计划  
   看是否能成功进入结果页，说明前后端 API 已经打通。

4. 测试地图  
   看地图能否正常加载 marker 和路线高亮。

5. 测试导出  
   试一次导出 PNG 和 PDF，确认不会因为公网部署而异常。

6. 测试详情页刷新  
   进入 `/trip/day/:dayIndex` 后手动刷新页面，确认仍可恢复当前行程数据。

7. 测试跨域  
   如果前端能请求后端、但浏览器控制台报 CORS 错误，优先检查 Render 的 `CORS_ALLOW_ORIGINS` 是否填写正确。

---

## 演示说明

推荐录制或截图以下几个典型流程：

1. 首页输入旅行需求并生成完整行程
2. 结果页展示总览、预算、地图和每日行程
3. 删除景点 / 调整顺序，观察地图与预算联动
4. 点击“重规划当天”，只替换某一天
5. 导出 PNG / PDF
6. 点击某一天进入 Day Detail 页面

可将截图放在：

- `docs/demo_screenshots/home.png`
- `docs/demo_screenshots/result-overview.png`
- `docs/demo_screenshots/day-card.png`
- `docs/demo_screenshots/day-detail.png`
- `docs/demo_screenshots/map.png`

---

## 项目亮点

- 从“生成文本”推进到“可编辑、可重规划、可导出”的完整旅行助手体验
- 把景点、天气、酒店、餐饮、交通、预算、地图串成统一数据链路
- 通过 `planner_agent + 后处理规则 + fallback` 提升大模型结果稳定性
- 支持地图路线高亮、单日详情页、预算联动、导出等偏产品化能力
- 工具层已开始抽象，为后续向更 MCP 风格的集成方式演进留出空间

---

## 后续可以继续扩展

- 历史记录与多次方案管理
- 更细颗粒度的预算明细
- 更真实的路线规划 API 接入
- 更丰富的偏好理解与行程风格控制
- 更完整的工具层抽象与 Agent 协作能力
