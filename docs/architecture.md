# Travel Agent 项目架构说明

## 1. 架构目标

本项目的目标不是只做一个“调用大模型返回文本”的 Demo，而是构建一个更接近真实产品形态的智能旅行助手：

- 前端可展示、可编辑、可导出
- 后端可组合多种工具与 Agent
- 大模型负责规划，但结果可以被规则校验和修正

---

## 2. 总体分层

```text
Frontend (Vue 3)
  ├─ Home.vue
  ├─ Result.vue
  ├─ DayCard.vue
  ├─ MapView.vue
  └─ stores/trip.ts

Backend (FastAPI)
  ├─ API Layer
  │   └─ /api/trip/plan
  │   └─ /api/trip/regenerate-day
  ├─ Orchestrator Layer
  │   └─ trip_orchestrator.py
  ├─ Agent Layer
  │   └─ attraction / weather / hotel / meal / planner
  ├─ Tool Layer
  │   └─ tools/provider.py
  └─ Service Layer
      └─ amap / weather / llm / image
```

---

## 3. 前端架构

### 3.1 页面层

- `Home.vue`
  - 用户输入旅行需求
  - 调用 `/api/trip/plan`
- `Result.vue`
  - 承担总览页
  - 负责地图、预算、导出、单日重规划入口

### 3.2 组件层

- `DayCard.vue`
  - 展示单日主题、天气、景点、餐饮、交通、酒店、预算
- `BudgetPanel.vue`
  - 展示总预算拆分
- `MapView.vue`
  - 渲染景点 marker、按天高亮、marker 信息窗
- `ExportButtons.vue`
  - 导出 PNG / PDF

### 3.3 状态层

- `stores/trip.ts`
  - 管理当前可编辑的 `tripPlan`
  - 支持删除景点、排序、替换某一天
  - 负责预算重算
  - 负责 `sessionStorage` 持久化

---

## 4. 后端架构

### 4.1 API Layer

`backend/app/api/trip.py`

- `POST /api/trip/plan`
  - 生成完整旅行计划
- `POST /api/trip/regenerate-day`
  - 单日重规划

### 4.2 Orchestrator Layer

`backend/app/orchestrators/trip_orchestrator.py`

作用：

- 拉起景点、天气、酒店、餐饮候选
- 统一调用 `planner_agent`
- 在最终返回前做 meals / budget 规范化

### 4.3 Agent Layer

- `attraction_agent.py`
  - 负责根据偏好搜索景点候选
- `weather_agent.py`
  - 获取真实天气，失败时 fallback
- `hotel_agent.py`
  - 生成酒店推荐，优先真实 POI，失败时回退模板酒店
- `meal_agent.py`
  - 生成三餐候选，失败时回退默认三餐
- `planner_agent.py`
  - 调用 LLM 生成 daily_plan
  - 再做规则校验、去重、重平衡、成本修正

---

## 5. Tool Layer 与渐进式 MCP 思路

当前项目没有强行重写成完整 MCP 框架，而是先抽出：

- `backend/app/tools/provider.py`

意义：

- 让 Agent 不直接依赖具体 HTTP service
- 当前 provider 仍调用已有 service
- 后续如果要迁移到 MCP，只需要替换 provider 的实现，而不必重写所有 agent

这是一种“先结构对齐，再逐步演进”的工程化思路。

---

## 6. Service Layer

### 6.1 高德服务

- `amap_service.py`
  - 文本搜索 POI
  - 解析名称、地址、分类、经纬度

### 6.2 天气服务

- `weather_service.py`
  - 拉取真实天气
  - 映射为 `WeatherInfo`

### 6.3 图片服务

- `image_service.py`
  - 搜索 Unsplash 图片
  - 为重点景点补图

### 6.4 LLM 服务

- `llm_service.py`
  - 封装模型请求
  - 输出 JSON 结构结果

---

## 7. 核心数据流

### 7.1 整程生成

```text
用户提交需求
→ Home.vue
→ /api/trip/plan
→ orchestrator 拉起 attraction / weather / hotel / meals
→ planner_agent 调用 LLM 规划
→ 规则后处理与 budget 规范化
→ Result.vue 展示地图、预算、DayCard
```

### 7.2 单日重规划

```text
用户点击 DayCard「重规划当天」
→ 前端提交当前 trip_plan + day + guidance
→ /api/trip/regenerate-day
→ 后端只针对该天重新构造单日 planner 请求
→ 返回新的 DayPlan
→ 前端 replaceDayPlan
→ 地图 / 预算 / DayCard 局部刷新
```

---

## 8. 为什么这个架构适合春招展示

- 有完整产品闭环，不只是算法或页面展示
- 有多层次工程结构，便于体现架构意识
- 有真实外部服务接入，体现工程落地能力
- 有 fallback 与后处理逻辑，体现稳定性思考
- 有后续演进空间，适合在面试中讲“怎么继续升级”

