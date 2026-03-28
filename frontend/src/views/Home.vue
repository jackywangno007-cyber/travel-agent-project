<template>
  <div class="home-page">
    <div v-if="loading" class="loading-overlay">
      <div class="loading-panel">
        <div class="loading-head">
          <span class="loading-kicker">旅行方案生成中</span>
          <h2>{{ activeLoadingStage.label }}</h2>
          <p>{{ activeLoadingStage.description }}</p>
        </div>

        <div class="progress-track">
          <div class="progress-fill" :style="{ width: `${loadingProgress}%` }"></div>
        </div>

        <div class="progress-meta">
          <span>已完成 {{ completedStageCount }} / {{ loadingStages.length }} 个阶段</span>
          <span>{{ loadingProgress }}%</span>
        </div>

        <ol class="loading-steps">
          <li
            v-for="(stage, index) in loadingStages"
            :key="stage.label"
            class="loading-step"
            :class="{
              done: index < loadingStageIndex,
              active: index === loadingStageIndex,
            }"
          >
            <span class="step-dot"></span>
            <div class="step-copy">
              <strong>{{ stage.label }}</strong>
              <span>{{ stage.description }}</span>
            </div>
          </li>
        </ol>

        <div class="loading-footer">
          <span>预计需要几秒到十几秒，已为你保留当前输入内容。</span>
        </div>
      </div>
    </div>

    <div class="hero-shell">
      <section class="hero-panel">
        <div class="hero-copy">
          <span class="eyebrow">AI Travel Assistant</span>
          <h1>智能旅行规划助手</h1>
          <p class="subtitle">
            从出发地、目的地、日期和预算出发，自动生成包含景点路线、地图、预算、餐饮、酒店与交通建议的完整旅行方案。
          </p>

          <div class="feature-grid">
            <article class="feature-card">
              <h3>智能规划</h3>
              <p>结合真实景点候选、天气与预算，为你生成多日行程与每日主题。</p>
            </article>
            <article class="feature-card">
              <h3>路线可视化</h3>
              <p>支持地图点位、景点顺序与每日路线高亮，更容易理解当天路线。</p>
            </article>
            <article class="feature-card">
              <h3>预算拆分</h3>
              <p>自动汇总酒店、门票、餐饮与其他预估，帮助你快速判断整体成本。</p>
            </article>
            <article class="feature-card">
              <h3>餐饮与交通</h3>
              <p>补齐早餐、午餐、晚餐与轻量交通建议，让方案更具可执行性。</p>
            </article>
            <article class="feature-card">
              <h3>行程编辑</h3>
              <p>支持删除景点、调整顺序、单日重规划，并与地图和预算联动。</p>
            </article>
            <article class="feature-card">
              <h3>导出分享</h3>
              <p>支持导出图片与 PDF，适合保存、展示和日常使用。</p>
            </article>
          </div>

          <div class="quick-examples">
            <span class="quick-label">快速体验</span>
            <div class="example-list">
              <button type="button" class="example-chip" @click="applyExample('beijing-history')">
                北京历史文化 3 日
              </button>
              <button type="button" class="example-chip" @click="applyExample('shanghai-food')">
                上海城市美食 4 日
              </button>
              <button type="button" class="example-chip" @click="applyExample('chengdu-relaxed')">
                成都轻松慢游 5 日
              </button>
            </div>
          </div>
        </div>

        <div class="form-panel">
          <div class="panel-head">
            <div>
              <span class="panel-kicker">创建你的专属方案</span>
              <h2>输入旅行需求</h2>
            </div>
            <span class="panel-tip">支持自然语言偏好与快速示例</span>
          </div>

          <form class="trip-form" @submit.prevent="handleSubmit">
            <div class="field-grid">
              <label class="field">
                <span>出发地</span>
                <input v-model="form.origin" type="text" placeholder="例如：西安" required />
              </label>

              <label class="field">
                <span>目的地</span>
                <input v-model="form.destination" type="text" placeholder="例如：北京" required />
              </label>
            </div>

            <div class="field-grid">
              <label class="field">
                <span>开始日期</span>
                <input v-model="form.start_date" type="date" required />
              </label>

              <label class="field">
                <span>结束日期</span>
                <input v-model="form.end_date" type="date" required />
              </label>
            </div>

            <label class="field">
              <span>预算</span>
              <input
                v-model.number="form.budget"
                type="number"
                min="0"
                placeholder="例如：3000"
              />
            </label>

            <label class="field">
              <span>偏好（中文逗号或英文逗号分隔）</span>
              <input
                v-model="preferencesText"
                type="text"
                placeholder="例如：想要轻松一点，多吃点本地美食，最好适合拍照"
              />
            </label>

            <div class="hint-box">
              <strong>示例输入：</strong>
              西安 → 北京，3 天行程，预算 3000，偏好“想要轻松一点，多看历史文化，再吃一些本地美食”。
            </div>

            <button type="submit" class="submit-button" :disabled="loading">
              {{ loading ? "正在生成旅行计划..." : "开始生成旅行计划" }}
            </button>
          </form>

          <p v-if="error" class="error">{{ error }}</p>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import axios from "axios";
import { onBeforeUnmount, reactive, ref } from "vue";
import { useRouter } from "vue-router";

import { createTripPlan } from "../services/api";
import { useEditableTripPlan } from "../stores/trip";
import type { TripPlanRequest } from "../types";

const router = useRouter();
const loading = ref(false);
const error = ref("");
const preferencesText = ref("");
const loadingStageIndex = ref(0);
const loadingProgress = ref(12);
const completedStageCount = ref(1);
let loadingTimer: ReturnType<typeof setTimeout> | null = null;

const loadingStages = [
  {
    label: "正在解析旅行需求",
    description: "系统会先整理出发地、目的地、日期、预算和基础旅行偏好。",
    waitMs: 900,
  },
  {
    label: "正在理解你的偏好",
    description: "结合你的输入内容，准备生成更贴近预期的景点与餐饮候选。",
    waitMs: 1100,
  },
  {
    label: "正在搜索景点与餐饮",
    description: "检索真实景点、餐饮与图片候选，并整理为可规划的数据集。",
    waitMs: 1300,
  },
  {
    label: "正在查询天气与酒店",
    description: "补充天气、住宿和基础交通信息，让行程更完整可执行。",
    waitMs: 1100,
  },
  {
    label: "正在规划每日路线",
    description: "结合顺路程度、主题分配和预算，生成更合理的每日安排。",
    waitMs: 1400,
  },
  {
    label: "正在生成最终旅行计划",
    description: "正在整理最终结果页需要的预算、地图和每日行程数据。",
    waitMs: 1800,
  },
] as const;

const activeLoadingStage = ref(loadingStages[0]);

const { setTripPlan } = useEditableTripPlan();

const form = reactive<TripPlanRequest>({
  origin: "",
  destination: "",
  start_date: "",
  end_date: "",
  budget: undefined,
  preferences: [],
});

const exampleMap = {
  "beijing-history": {
    origin: "西安",
    destination: "北京",
    start_date: "2026-04-01",
    end_date: "2026-04-03",
    budget: 3000,
    preferences: "更偏历史文化，想去博物馆和古建筑，顺便吃点本地美食",
  },
  "shanghai-food": {
    origin: "南京",
    destination: "上海",
    start_date: "2026-04-10",
    end_date: "2026-04-13",
    budget: 4500,
    preferences: "喜欢城市漫游和拍照，想吃本地美食，最好有夜景氛围",
  },
  "chengdu-relaxed": {
    origin: "重庆",
    destination: "成都",
    start_date: "2026-04-18",
    end_date: "2026-04-22",
    budget: 3800,
    preferences: "想要轻松慢游，不想太累，少走路，可以多吃点成都特色",
  },
} as const;

function syncLoadingProgress() {
  activeLoadingStage.value = loadingStages[loadingStageIndex.value];
  loadingProgress.value = Math.min(
    96,
    Math.round(((loadingStageIndex.value + 1) / loadingStages.length) * 100)
  );
  completedStageCount.value = loadingStageIndex.value + 1;
}

function clearLoadingTimer() {
  if (loadingTimer) {
    clearTimeout(loadingTimer);
    loadingTimer = null;
  }
}

function scheduleLoadingStageAdvance() {
  clearLoadingTimer();

  if (!loading.value || loadingStageIndex.value >= loadingStages.length - 1) {
    return;
  }

  const currentStage = loadingStages[loadingStageIndex.value];
  loadingTimer = setTimeout(() => {
    if (!loading.value) {
      return;
    }

    if (loadingStageIndex.value < loadingStages.length - 1) {
      loadingStageIndex.value += 1;
      syncLoadingProgress();
      scheduleLoadingStageAdvance();
    }
  }, currentStage.waitMs);
}

function startLoadingExperience() {
  loadingStageIndex.value = 0;
  syncLoadingProgress();
  scheduleLoadingStageAdvance();
}

function finishLoadingExperience() {
  loadingStageIndex.value = loadingStages.length - 1;
  syncLoadingProgress();
}

function resetLoadingExperience() {
  clearLoadingTimer();
  loadingStageIndex.value = 0;
  loadingProgress.value = 12;
  completedStageCount.value = 1;
  activeLoadingStage.value = loadingStages[0];
}

function validateDates(): string | null {
  if (!form.start_date || !form.end_date) {
    return null;
  }

  if (form.end_date < form.start_date) {
    return "结束日期不能早于开始日期。";
  }

  return null;
}

function applyExample(key: keyof typeof exampleMap) {
  const example = exampleMap[key];
  form.origin = example.origin;
  form.destination = example.destination;
  form.start_date = example.start_date;
  form.end_date = example.end_date;
  form.budget = example.budget;
  preferencesText.value = example.preferences;
  error.value = "";
}

async function handleSubmit() {
  error.value = "";

  const dateError = validateDates();
  if (dateError) {
    error.value = dateError;
    return;
  }

  loading.value = true;
  startLoadingExperience();

  try {
    form.preferences = preferencesText.value
      .split(/[，,]/)
      .map((item) => item.trim())
      .filter(Boolean);

    const result = await createTripPlan(form);
    finishLoadingExperience();
    setTripPlan(result);
    await router.push("/result");
  } catch (err) {
    console.error(err);

    if (axios.isAxiosError(err)) {
      if (!err.response) {
        error.value = `无法连接后端服务，请检查 VITE_API_BASE_URL 配置，或确认本地 backend 与 Vite 代理正在运行。${
          err.message ? `\n错误详情：${err.message}` : ""
        }`;
      } else {
        const detail =
          typeof err.response.data === "string"
            ? err.response.data
            : JSON.stringify(err.response.data);
        error.value = `生成失败：${err.response.status}，${detail}`;
      }
    } else {
      error.value = "生成失败，请稍后重试。";
    }
  } finally {
    loading.value = false;
    resetLoadingExperience();
  }
}

onBeforeUnmount(() => {
  clearLoadingTimer();
});
</script>

<style scoped>
.home-page {
  min-height: 100vh;
  padding: 34px 18px 56px;
}

.loading-overlay {
  position: fixed;
  inset: 0;
  z-index: 120;
  display: grid;
  place-items: center;
  padding: 20px;
  background:
    linear-gradient(180deg, rgba(241, 245, 249, 0.84) 0%, rgba(236, 243, 252, 0.88) 100%);
  backdrop-filter: blur(12px);
}

.loading-panel {
  width: min(560px, 100%);
  padding: 30px;
  border-radius: 30px;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 30px 72px rgba(15, 23, 42, 0.18);
  border: 1px solid rgba(219, 234, 254, 0.95);
  display: grid;
  gap: 20px;
}

.loading-head {
  display: grid;
  gap: 8px;
}

.loading-kicker {
  display: inline-flex;
  width: fit-content;
  padding: 6px 12px;
  border-radius: 999px;
  background: #e8f1ff;
  color: #1d4ed8;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.loading-head h2 {
  margin: 0;
  font-size: 32px;
  color: #0f172a;
  letter-spacing: -0.03em;
}

.loading-head p {
  margin: 0;
  color: #64748b;
  line-height: 1.7;
}

.progress-track {
  width: 100%;
  height: 12px;
  border-radius: 999px;
  background: #e2e8f0;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(135deg, #1677ff 0%, #1d4ed8 100%);
  transition: width 0.45s ease;
}

.progress-meta {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  color: #475569;
  font-size: 13px;
  font-weight: 600;
}

.loading-steps {
  display: grid;
  gap: 12px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.loading-step {
  display: grid;
  grid-template-columns: 18px minmax(0, 1fr);
  gap: 12px;
  align-items: start;
  padding: 14px 16px;
  border-radius: 18px;
  background: #f8fafc;
  border: 1px solid transparent;
  transition: background 0.2s ease, border-color 0.2s ease, transform 0.2s ease;
}

.loading-step.done {
  background: #f0fdf4;
  border-color: #bbf7d0;
}

.loading-step.active {
  background: #eff6ff;
  border-color: #bfdbfe;
  transform: translateY(-1px);
}

.step-dot {
  width: 12px;
  height: 12px;
  margin-top: 4px;
  border-radius: 999px;
  background: #cbd5e1;
  box-shadow: 0 0 0 6px rgba(203, 213, 225, 0.18);
}

.loading-step.done .step-dot {
  background: #22c55e;
  box-shadow: 0 0 0 6px rgba(34, 197, 94, 0.15);
}

.loading-step.active .step-dot {
  background: #1677ff;
  box-shadow: 0 0 0 6px rgba(22, 119, 255, 0.14);
}

.step-copy {
  display: grid;
  gap: 4px;
}

.step-copy strong {
  color: #0f172a;
  font-size: 15px;
}

.step-copy span {
  color: #64748b;
  line-height: 1.6;
  font-size: 13px;
}

.loading-footer {
  color: #64748b;
  font-size: 13px;
  line-height: 1.7;
}

.hero-shell {
  max-width: 1180px;
  margin: 0 auto;
}

.hero-panel {
  display: grid;
  grid-template-columns: minmax(0, 1.1fr) minmax(360px, 460px);
  gap: 26px;
  align-items: start;
}

.hero-copy,
.form-panel {
  position: relative;
  border-radius: 30px;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 26px 64px rgba(15, 23, 42, 0.08);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(219, 234, 254, 0.92);
}

.hero-copy {
  padding: 44px;
}

.form-panel {
  padding: 30px;
}

.eyebrow,
.panel-kicker {
  display: inline-flex;
  align-items: center;
  padding: 6px 12px;
  border-radius: 999px;
  background: #e8f1ff;
  color: #1d4ed8;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.hero-copy h1 {
  margin: 18px 0 16px;
  font-size: clamp(42px, 5vw, 68px);
  line-height: 1.02;
  letter-spacing: -0.04em;
  color: #0f172a;
  max-width: 10ch;
}

.subtitle {
  max-width: 680px;
  margin: 0 0 32px;
  color: #475569;
  font-size: 18px;
  line-height: 1.8;
}

.feature-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
  margin-bottom: 28px;
}

.feature-card {
  padding: 20px;
  border-radius: 20px;
  background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
  border: 1px solid #dbeafe;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.7);
  transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
}

.feature-card:hover {
  transform: translateY(-2px);
  border-color: #bfdbfe;
  box-shadow: 0 18px 30px rgba(59, 130, 246, 0.1);
}

.feature-card h3 {
  margin: 0 0 8px;
  font-size: 18px;
  letter-spacing: -0.01em;
}

.feature-card p {
  margin: 0;
  color: #64748b;
  line-height: 1.7;
}

.quick-examples {
  display: grid;
  gap: 12px;
}

.quick-label {
  color: #334155;
  font-size: 14px;
  font-weight: 700;
}

.example-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.example-chip {
  padding: 11px 15px;
  border: 1px solid #dbeafe;
  border-radius: 999px;
  background: #f8fbff;
  color: #1d4ed8;
  cursor: pointer;
  transition: transform 0.18s ease, box-shadow 0.18s ease;
  font-weight: 600;
}

.example-chip:hover {
  transform: translateY(-1px);
  box-shadow: 0 10px 20px rgba(29, 78, 216, 0.1);
}

.panel-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 24px;
}

.panel-head h2 {
  margin: 14px 0 0;
  font-size: 32px;
  color: #0f172a;
  letter-spacing: -0.03em;
}

.panel-tip {
  color: #64748b;
  font-size: 13px;
}

.trip-form {
  display: grid;
  gap: 18px;
}

.field-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.field span {
  color: #334155;
  font-size: 14px;
  font-weight: 700;
}

.field input {
  padding: 15px 16px;
  border: 1px solid #dbe3f0;
  border-radius: 16px;
  background: linear-gradient(180deg, #fcfdff 0%, #f8fbff 100%);
  font-size: 15px;
  color: #0f172a;
  transition: border-color 0.18s ease, box-shadow 0.18s ease, background 0.18s ease;
}

.field input:focus {
  outline: none;
  border-color: #7aa2ff;
  background: #ffffff;
  box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.12);
}

.hint-box {
  padding: 15px 16px;
  border-radius: 16px;
  background: #f8fbff;
  border: 1px dashed #c7d9ff;
  color: #475569;
  line-height: 1.7;
}

.submit-button {
  padding: 16px 18px;
  border: none;
  border-radius: 16px;
  background: linear-gradient(135deg, #1677ff 0%, #1d4ed8 100%);
  color: white;
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  box-shadow: 0 18px 34px rgba(29, 78, 216, 0.2);
  transition: transform 0.18s ease, box-shadow 0.18s ease, opacity 0.18s ease;
}

.submit-button:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 20px 36px rgba(29, 78, 216, 0.24);
}

.submit-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.error {
  margin: 16px 0 0;
  padding: 14px 16px;
  border-radius: 16px;
  background: #fef2f2;
  color: #b91c1c;
  white-space: pre-wrap;
  line-height: 1.7;
}

@media (max-width: 980px) {
  .hero-panel {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .home-page {
    padding: 18px 12px 36px;
  }

  .loading-panel {
    padding: 22px;
    border-radius: 22px;
  }

  .hero-copy,
  .form-panel {
    padding: 22px;
    border-radius: 24px;
  }

  .feature-grid,
  .field-grid {
    grid-template-columns: 1fr;
  }

  .panel-head {
    flex-direction: column;
  }
}
</style>
