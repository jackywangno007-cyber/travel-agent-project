# API 说明

## 1. 生成完整旅行计划

### `POST /api/trip/plan`

请求体示例：

```json
{
  "origin": "西安",
  "destination": "北京",
  "start_date": "2026-04-01",
  "end_date": "2026-04-03",
  "budget": 3000,
  "preferences": ["历史", "美食"]
}
```

返回：

- `TripPlanResponse`

主要字段：

- `destination`
- `total_days`
- `total_budget_estimate`
- `summary`
- `daily_plan`
- `generation_source`
- `fallback_reason`

## 2. 单日重规划

### `POST /api/trip/regenerate-day`

请求体示例：

```json
{
  "trip_plan": { "...": "当前整份旅行计划对象" },
  "day": 2,
  "preferences": ["更轻松", "更少步行"],
  "guidance": "雨天优先室内"
}
```

返回：

- 单个 `DayPlan`

说明：

- 只替换指定的某一天
- 其他天保持不变
- 继续复用景点、天气、酒店、餐饮、交通和 planner 逻辑

## 3. 调试方式

本地启动后端后访问：

- `http://127.0.0.1:8000/docs`

可直接通过 Swagger UI 调试。
## Travel Agent API

### 1. 生成完整旅行计划

`POST /api/trip/plan`

请求示例：

```json
{
  "origin": "西安",
  "destination": "北京",
  "start_date": "2026-04-01",
  "end_date": "2026-04-03",
  "budget": 3000,
  "preferences": ["历史", "美食"]
}
```

响应核心字段：

- `destination`
- `total_days`
- `total_budget_estimate`
- `summary`
- `daily_plan`
- `generation_source`
- `fallback_reason`

---

### 2. 单日重规划

`POST /api/trip/regenerate-day`

请求示例：

```json
{
  "trip_plan": { "...": "当前整份 TripPlanResponse" },
  "day": 2,
  "preferences": ["更轻松", "更少步行"],
  "guidance": "这一天希望减少步行，多安排室内项目"
}
```

响应：

- 返回新的 `DayPlan`
- 前端只替换对应的某一天

---

### 3. 本地调试

- Swagger: `http://127.0.0.1:8000/docs`
- OpenAPI: `http://127.0.0.1:8000/openapi.json`
