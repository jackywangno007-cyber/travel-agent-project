# Travel Agent Project

一个面向春招展示的智能旅行助手项目。  
项目以“多 Agent + 工具层 + 前后端分离”的方式实现完整旅行规划链路，支持从用户输入出发，生成包含景点、天气、酒店、餐饮、交通、地图、预算和可编辑行程的旅行计划。

---

## 1. 项目简介

本项目希望解决“旅行规划信息分散、手动整合成本高”的问题。  
用户输入出发地、目的地、日期、预算和偏好后，系统会自动生成多天旅行计划，并给出：

- 每日景点安排
- 真实天气信息
- 酒店推荐
- 餐饮安排
- 轻量交通建议
- 地图可视化
- 预算拆分
- 导出 PDF / 图片
- 单日重规划

项目不仅关注“生成结果”，也强调“可交互性”和“可落地执行”，因此在结果页中加入了编辑、重规划、地图联动和预算实时更新等能力。

---

## 2. 核心功能列表

- 基于用户偏好的多天旅行计划生成
- 景点搜索：接入高德 POI 搜索，返回真实景点名称、地址和坐标
- 天气服务：接入真实天气 API，并提供 fallback 兜底
- 酒店推荐：基于真实 POI 搜索 + 规则估算价格
- 餐饮安排：支持早餐 / 午餐 / 晚餐 / 小吃候选与 fallback
- 交通建议：基于景点顺序、距离和天气生成轻量路线说明
- 地图展示：高德地图打点、按天高亮、marker 信息查看
- 预算管理：拆分酒店 / 门票 / 餐饮 / 其他预估
- 行程编辑：删除景点、同日内排序、局部预算联动
- 单日重规划：只替换某一天 DayPlan，不重跑整份行程
- 导出功能：支持导出 PNG 和 PDF

---

## 3. 技术栈

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
- OpenAI / DeepSeek 兼容 LLM 接口
- Python 标准库 HTTP 请求

### 外部服务

- 高德地图 POI / JS API
- Open-Meteo 天气服务
- Unsplash 图片搜索

---

## 4. 系统架构

项目采用前后端分离架构，后端内部按 `API -> Orchestrator -> Agents -> Services / Tools` 分层组织。

### 前端

- `Home.vue`
  - 收集用户输入并发起旅行计划请求
- `Result.vue`
  - 负责结果页总览、地图、预算、锚点导航和单日重规划
- `DayCard.vue`
  - 展示单日行程、餐饮、交通、酒店、预算拆分
- `MapView.vue`
  - 地图渲染与按天高亮
- `stores/trip.ts`
  - 管理可编辑行程状态、预算重算和本地持久化

### 后端

- `api/trip.py`
  - 提供整程生成与单日重规划接口
- `orchestrators/trip_orchestrator.py`
  - 负责聚合景点、天气、酒店、餐饮，并调用 Planner
- `agents/`
  - `attraction_agent.py`：景点候选生成
  - `weather_agent.py`：天气查询
  - `hotel_agent.py`：酒店推荐
  - `meal_agent.py`：餐饮候选生成
  - `planner_agent.py`：调用大模型并进行结果后处理
- `services/`
  - 高德 POI、天气、图片、LLM 请求封装
- `tools/provider.py`
  - 统一工具入口，为后续 MCP 风格迁移做准备

更多说明见 [architecture.md](./docs/architecture.md)。

---

## 5. 项目运行方法

### 5.1 启动后端

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

默认后端地址：

```text
http://127.0.0.1:8000
```

Swagger 文档：

```text
http://127.0.0.1:8000/docs
```

### 5.2 启动前端

```powershell
cd frontend
npm install
npm run dev
```

默认前端地址：

```text
http://127.0.0.1:5173
```

---

## 6. 环境变量说明

### 后端 `.env`

参考 [backend/.env.example](./backend/.env.example)

常用变量：

```env
AMAP_API_KEY=
OPENAI_API_KEY=
OPENAI_BASE_URL=
OPENAI_MODEL=
WEATHER_API_TIMEOUT_SECONDS=10
UNSPLASH_ACCESS_KEY=
IMAGE_API_TIMEOUT_SECONDS=8
IMAGE_LOOKUP_LIMIT=3
```

说明：

- `AMAP_API_KEY`：高德 Web Service API Key，用于 POI 搜索
- `OPENAI_API_KEY / OPENAI_BASE_URL / OPENAI_MODEL`：大模型配置
- `UNSPLASH_ACCESS_KEY`：景点图片搜索

### 前端 `.env`

参考 [frontend/.env.example](./frontend/.env.example)

```env
VITE_AMAP_API_KEY=
VITE_AMAP_SECURITY_JS_CODE=
```

说明：

- `VITE_AMAP_API_KEY`：高德 JS API Key
- `VITE_AMAP_SECURITY_JS_CODE`：高德安全密钥

---

## 7. API 说明

当前核心接口包括：

- `POST /api/trip/plan`
  - 生成整份旅行计划
- `POST /api/trip/regenerate-day`
  - 单日重规划，只返回某一天新的 `DayPlan`

可进一步查看 [docs/api.md](./docs/api.md)。

---

## 8. 演示说明

建议录制或截图以下演示路径：

1. 首页输入旅行需求并生成完整行程
2. 结果页展示总览、预算、地图、DayCard
3. 删除景点 / 调整顺序，观察地图与预算联动
4. 点击“重规划当天”，只替换某一天
5. 导出 PNG / PDF

截图建议放在：

- `docs/demo_screenshots/home.png`
- `docs/demo_screenshots/result-overview.png`
- `docs/demo_screenshots/day-card.png`
- `docs/demo_screenshots/map.png`

README 中可后续补成：

```md
![Home](./docs/demo_screenshots/home.png)
![Result](./docs/demo_screenshots/result-overview.png)
```

---

## 9. 项目亮点

- 从“生成式 demo”推进到“可编辑、可重规划、可导出”的完整旅行助手产品形态
- 将景点、天气、酒店、餐饮、交通、预算、地图串成统一数据链路
- 通过 `planner_agent + 后处理规则` 提升大模型结果稳定性
- 通过共享 `ToolProvider` 保持项目稳定运行，同时为后续 MCP 风格迁移预留结构

---

## 10. 后续可继续扩展

- 历史记录与多次方案管理
- 更细粒度的预算明细
- 真正的路线规划 API 接入
- 更多偏好控制，例如亲子游 / 特种兵 / 雨天优先
- MCP 化工具接入与多 Agent 协作增强

