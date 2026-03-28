<template>
  <div v-if="trip" class="page">
    <div class="container">
      <header class="hero-header" id="top">
        <div class="hero-copy">
          <span class="eyebrow">AI Travel Result</span>
          <h1>{{ trip.destination }} 旅行计划</h1>
          <p class="hero-subtitle">
            当前方案已经整合地图、预算、餐饮、交通和每日路线，可继续编辑、重规划或导出。
          </p>
        </div>

        <div class="hero-actions">
          <div class="action-note">
            <strong>当前支持</strong>
            <span>景点排序、单日重规划、地图路线高亮、预算拆分、导出图片与 PDF</span>
          </div>
          <div class="action-row">
            <ExportButtons
              target-id="trip-plan-content"
              :file-base-name="`${trip.destination}-trip-plan`"
            />
            <button class="secondary-button" @click="goBack">返回重新生成</button>
          </div>
        </div>
      </header>

      <nav class="anchor-nav" aria-label="结果页导航">
        <button
          v-for="item in navItems"
          :key="item.id"
          type="button"
          class="anchor-chip"
          @click="scrollToSection(item.id)"
        >
          {{ item.label }}
        </button>
      </nav>

      <div id="trip-plan-content" class="export-content">
        <section id="overview" class="hero-grid">
          <article class="summary-card surface-card">
            <div class="summary-top">
              <div class="summary-metric">
                <span class="metric-label">总天数</span>
                <strong>{{ trip.total_days }} 天</strong>
              </div>
              <div class="summary-metric">
                <span class="metric-label">预算估算</span>
                <strong>¥{{ formatMoney(trip.total_budget_estimate) }}</strong>
              </div>
              <div class="summary-metric">
                <span class="metric-label">结果来源</span>
                <strong>{{ trip.generation_source === "llm" ? "大模型" : "规则回退" }}</strong>
              </div>
              <div class="summary-metric">
                <span class="metric-label">景点总数</span>
                <strong>{{ totalAttractions }}</strong>
              </div>
            </div>

            <div class="summary-body">
              <div class="summary-block">
                <span class="block-label">整体总结</span>
                <p>{{ trip.summary }}</p>
              </div>

              <div v-if="recognizedPreferenceTags.length" class="summary-block">
                <span class="block-label">识别到的偏好标签</span>
                <div class="preference-tags">
                  <span
                    v-for="tag in recognizedPreferenceTags"
                    :key="tag"
                    class="preference-tag"
                  >
                    {{ tag }}
                  </span>
                </div>
              </div>

              <div v-if="trip.fallback_reason" class="summary-block warning">
                <span class="block-label">回退说明</span>
                <p>{{ trip.fallback_reason }}</p>
              </div>
            </div>
          </article>

          <section id="budget" class="budget-wrap">
            <BudgetPanel :total-budget="trip.total_budget_estimate" :breakdown="budgetBreakdown" />
          </section>
        </section>

        <section id="map" class="map-section surface-card" data-export-map>
          <div class="section-head">
            <div>
              <h2>景点地图与路线</h2>
              <p>可按天查看景点分布、访问顺序与轻量路线连线，辅助理解整体行程。</p>
            </div>
          </div>

          <MapView
            :points="mapPoints"
            :active-day="activeDay"
            :focused-point-key="focusedPointKey"
            @clear-active-day="
              activeDay = null;
              focusedPointKey = null;
            "
          />
        </section>

        <div class="map-legend">
          <button
            type="button"
            class="legend-chip"
            :class="{ active: activeDay === null }"
            @click="
              activeDay = null;
              focusedPointKey = null;
            "
          >
            全部行程
          </button>
          <button
            v-for="day in trip.daily_plan"
            :key="`legend-${day.day}`"
            type="button"
            class="legend-chip"
            :class="{ active: activeDay === day.day }"
            @click="toggleDay(day.day)"
          >
            Day {{ day.day }}
          </button>
        </div>

        <section class="day-section">
          <div class="section-head">
            <div>
              <h2>每日行程安排</h2>
              <p>可逐天查看、编辑、重规划，并与地图路线和预算保持同步联动。</p>
            </div>
          </div>

          <div class="day-list">
            <section
              v-for="day in trip.daily_plan"
              :id="`day-${day.day}`"
              :key="day.day"
              class="day-anchor-section"
            >
              <DayCard
                :day="day"
                :active="activeDay === day.day"
                :faded="activeDay !== null && activeDay !== day.day"
                :expanded="expandedDay === day.day"
                :day-budget="getDayBudget(day)"
                :regenerating="regeneratingDay === day.day"
                :regenerate-error="dayErrors[day.day]"
                @toggle-day="toggleDay"
                @toggle-expand="toggleAccordion"
                @delete-attraction="deleteAttraction"
                @move-attraction="moveAttraction"
                @regenerate-day="handleRegenerateDay"
                @focus-attraction="handleFocusAttraction"
                @view-detail="goToDayDetail"
              />
            </section>
          </div>
        </section>
      </div>

      <button
        v-if="showBackToTop"
        type="button"
        class="back-to-top"
        @click="scrollToSection('top')"
      >
        回到顶部
      </button>
    </div>
  </div>

  <div v-else class="page">
    <div class="container empty-state">
      <h1>没有找到旅行结果</h1>
      <p class="empty-tip">
        当前结果页没有可恢复的行程数据。请回到首页重新生成；如果你刚刚生成过结果，先返回首页再重新提交一次。
      </p>
      <button class="secondary-button" @click="goBack">返回首页</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import axios from "axios";
import { computed, onBeforeUnmount, reactive, ref, watch } from "vue";
import { useRouter } from "vue-router";

import BudgetPanel from "../components/BudgetPanel.vue";
import DayCard from "../components/DayCard.vue";
import ExportButtons from "../components/ExportButtons.vue";
import MapView from "../components/MapView.vue";
import { regenerateTripDay } from "../services/api";
import { useEditableTripPlan } from "../stores/trip";
import type { DayPlan, MapAttractionPoint } from "../types";

const router = useRouter();
const activeDay = ref<number | null>(null);
const focusedPointKey = ref<string | null>(null);
const expandedDay = ref<number | null>(null);
const showBackToTop = ref(false);
const regeneratingDay = ref<number | null>(null);
const dayErrors = reactive<Record<number, string>>({});

const {
  tripPlan,
  totalAttractions,
  loadFromSessionStorage,
  deleteAttraction,
  moveAttraction,
  replaceDayPlan,
} = useEditableTripPlan();

if (typeof window !== "undefined") {
  loadFromSessionStorage();
}

function updateBackToTop() {
  showBackToTop.value = window.scrollY > 480;
}

if (typeof window !== "undefined") {
  updateBackToTop();
  window.addEventListener("scroll", updateBackToTop, { passive: true });
}

onBeforeUnmount(() => {
  if (typeof window !== "undefined") {
    window.removeEventListener("scroll", updateBackToTop);
  }
});

const trip = computed(() => tripPlan.value);

watch(
  trip,
  (value) => {
    if (!value || value.daily_plan.length === 0) {
      expandedDay.value = null;
      return;
    }

    const hasExpandedDay = value.daily_plan.some((day) => day.day === expandedDay.value);
    if (!hasExpandedDay && expandedDay.value !== null) {
      expandedDay.value = null;
    }
  },
  { immediate: true }
);

const navItems = computed(() => {
  const items = [
    { id: "overview", label: "总览" },
    { id: "budget", label: "预算" },
    { id: "map", label: "地图" },
  ];

  if (!trip.value) {
    return items;
  }

  return [
    ...items,
    ...trip.value.daily_plan.map((day) => ({
      id: `day-${day.day}`,
      label: `Day ${day.day}`,
    })),
  ];
});

const mapPoints = computed<MapAttractionPoint[]>(() => {
  if (!trip.value) {
    return [];
  }

  return trip.value.daily_plan.flatMap((day) =>
    day.attractions.map((attraction, index) => ({
      key: `${day.day}-${attraction.name}-${attraction.address}-${index}`,
      day: day.day,
      date: day.date,
      orderInDay: index + 1,
      sequenceLabel: "第" + (index + 1) + "站",
      name: attraction.name,
      address: attraction.address,
      location: attraction.location,
      category: attraction.category,
    }))
  );
});

const budgetBreakdown = computed(() => {
  if (!trip.value) {
    return { hotel: 0, tickets: 0, meals: 0, other: 0 };
  }

  const hotel = trip.value.daily_plan.reduce(
    (sum, day) => sum + (day.hotel?.price_per_night ?? 0),
    0
  );
  const tickets = trip.value.daily_plan.reduce(
    (sum, day) =>
      sum + day.attractions.reduce((inner, item) => inner + (item.ticket_price ?? 0), 0),
    0
  );
  const meals = trip.value.daily_plan.reduce((sum, day) => sum + getMealCost(day), 0);
  const other = Math.max(trip.value.total_budget_estimate - hotel - tickets - meals, 0);

  return { hotel, tickets, meals, other };
});

const recognizedPreferenceTags = computed(() => {
  if (!trip.value?.parsed_preferences) {
    return [];
  }

  const parsed = trip.value.parsed_preferences;
  return [
    ...parsed.interests,
    parsed.pace,
    parsed.mobility,
    ...parsed.scene,
    parsed.group_type,
  ].filter((item): item is string => Boolean(item && item.trim()));
});

function goBack() {
  router.push("/");
}

function goToDayDetail(day: number) {
  router.push(`/trip/day/${day}`);
}

function toggleDay(day: number) {
  activeDay.value = activeDay.value === day ? null : day;
  focusedPointKey.value = null;
}

function toggleAccordion(day: number) {
  if (expandedDay.value === day) {
    expandedDay.value = null;
    if (activeDay.value === day) {
      activeDay.value = null;
      focusedPointKey.value = null;
    }
    return;
  }

  expandedDay.value = day;
  activeDay.value = day;
  focusedPointKey.value = null;
}

function handleFocusAttraction(payload: { day: number; orderInDay: number }) {
  activeDay.value = payload.day;
  focusedPointKey.value = `${payload.day}-${payload.orderInDay}`;
}

function scrollToSection(id: string) {
  const element = document.getElementById(id);
  if (!element) {
    return;
  }

  element.scrollIntoView({
    behavior: "smooth",
    block: "start",
  });
}

function formatMoney(value: number) {
  return Math.round(value);
}

function getMealCost(day: DayPlan) {
  return [day.meals?.breakfast, day.meals?.lunch, day.meals?.dinner, day.meals?.snack].reduce(
    (sum, meal) => sum + (meal?.estimated_cost ?? 0),
    0
  );
}

function getDayBudget(day: DayPlan) {
  const hotel = day.hotel?.price_per_night ?? 0;
  const tickets = day.attractions.reduce((sum, item) => sum + (item.ticket_price ?? 0), 0);
  const meals = getMealCost(day);
  const other = Math.max(day.estimated_cost - hotel - tickets - meals, 0);
  return { hotel, tickets, meals, other };
}

async function handleRegenerateDay(dayNumber: number) {
  if (!trip.value || regeneratingDay.value !== null) {
    return;
  }

  const guidance =
    window.prompt(
      "可选输入这一天的新偏好，例如：更轻松 / 更美食 / 更少步行 / 雨天优先",
      ""
    ) ?? "";
  const parsedPreferences = guidance
    .split(/[，,]/)
    .map((item) => item.trim())
    .filter(Boolean);

  delete dayErrors[dayNumber];
  regeneratingDay.value = dayNumber;

  try {
    const nextDay = await regenerateTripDay({
      trip_plan: trip.value,
      day: dayNumber,
      preferences: parsedPreferences,
      guidance: guidance.trim() || null,
    });
    replaceDayPlan(nextDay);
    activeDay.value = dayNumber;
    focusedPointKey.value = null;
  } catch (error) {
    console.error(error);
    if (axios.isAxiosError(error)) {
      if (!error.response) {
        dayErrors[dayNumber] = "无法连接后端，请确认 backend 正在运行。";
      } else {
        dayErrors[dayNumber] = `重规划失败：${error.response.status}`;
      }
    } else {
      dayErrors[dayNumber] = "重规划失败，请稍后重试。";
    }
  } finally {
    regeneratingDay.value = null;
  }
}
</script>

<style scoped>
.page {
  min-height: 100vh;
  padding: 34px 18px 64px;
}

.container {
  max-width: 1180px;
  margin: 0 auto;
}

.surface-card {
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid rgba(219, 234, 254, 0.9);
  box-shadow: 0 22px 54px rgba(15, 23, 42, 0.08);
  backdrop-filter: blur(12px);
}

.hero-header {
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) minmax(320px, 0.8fr);
  gap: 22px;
  align-items: end;
  margin-bottom: 24px;
  padding: 10px 10px 12px;
  border-radius: 28px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.62) 0%, rgba(255, 255, 255, 0) 100%);
}

.hero-copy {
  display: grid;
  gap: 12px;
}

.eyebrow {
  display: inline-flex;
  width: fit-content;
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
  margin: 0;
  font-size: clamp(40px, 5vw, 60px);
  line-height: 1.02;
  letter-spacing: -0.04em;
}

.hero-subtitle {
  max-width: 720px;
  margin: 0;
  color: #475569;
  font-size: 16px;
  line-height: 1.8;
}

.hero-actions {
  display: grid;
  gap: 16px;
  justify-items: end;
}

.action-note {
  display: grid;
  gap: 6px;
  padding: 16px 18px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.86);
  border: 1px solid #dbeafe;
  color: #475569;
  text-align: right;
  box-shadow: 0 14px 30px rgba(15, 23, 42, 0.05);
}

.action-note strong {
  color: #0f172a;
}

.action-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.secondary-button {
  padding: 11px 16px;
  border: none;
  border-radius: 14px;
  background: linear-gradient(135deg, #1677ff 0%, #1d4ed8 100%);
  color: white;
  cursor: pointer;
  box-shadow: 0 14px 28px rgba(29, 78, 216, 0.18);
  font-weight: 700;
}

.anchor-nav {
  position: sticky;
  top: 12px;
  z-index: 20;
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 28px;
  padding: 12px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.88);
  backdrop-filter: blur(14px);
  box-shadow: 0 14px 28px rgba(15, 23, 42, 0.08);
}

.anchor-chip {
  padding: 10px 14px;
  border: 1px solid #dbeafe;
  border-radius: 999px;
  background: #eff6ff;
  color: #1d4ed8;
  white-space: nowrap;
  cursor: pointer;
  font-weight: 700;
}

.anchor-chip:hover {
  transform: translateY(-1px);
  background: #dbeafe;
}

.export-content {
  display: grid;
  gap: 34px;
}

.hero-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) minmax(340px, 0.92fr);
  gap: 22px;
  align-items: start;
}

.summary-card {
  padding: 28px;
  border-radius: 26px;
}

.summary-top {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
  margin-bottom: 20px;
}

.summary-metric {
  padding: 18px;
  border-radius: 20px;
  background: #f8fafc;
  border: 1px solid rgba(219, 234, 254, 0.7);
}

.metric-label,
.block-label {
  display: block;
  margin-bottom: 8px;
  color: #64748b;
  font-size: 12px;
}

.summary-metric strong {
  color: #0f172a;
  font-size: 24px;
}

.summary-body {
  display: grid;
  gap: 12px;
}

.summary-block {
  padding: 18px;
  border-radius: 20px;
  background: #f8fafc;
  border: 1px solid rgba(226, 232, 240, 0.7);
}

.summary-block p {
  margin: 0;
  color: #334155;
  line-height: 1.8;
}

.preference-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.preference-tag {
  display: inline-flex;
  align-items: center;
  padding: 8px 12px;
  border-radius: 999px;
  background: #e8f1ff;
  color: #1d4ed8;
  font-size: 13px;
  font-weight: 600;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.85);
}

.summary-block.warning {
  background: #fff7ed;
}

.budget-wrap {
  align-self: stretch;
}

.map-section {
  padding: 22px;
  border-radius: 26px;
}

.section-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 14px;
  margin-bottom: 16px;
}

.section-head h2 {
  margin: 0;
  font-size: 24px;
}

.section-head p {
  margin: 8px 0 0;
  color: #64748b;
  line-height: 1.7;
}

#overview,
#budget,
#map,
.day-anchor-section {
  scroll-margin-top: 96px;
}

.map-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: -2px;
}

.legend-chip {
  padding: 10px 14px;
  border: 1px solid #dbeafe;
  border-radius: 999px;
  background: #edf2ff;
  color: #1d4ed8;
  cursor: pointer;
  font-weight: 700;
  box-shadow: 0 8px 18px rgba(148, 163, 184, 0.1);
}

.legend-chip.active {
  background: #1d4ed8;
  color: white;
}

.day-section {
  display: grid;
  gap: 18px;
}

.day-list {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.empty-state {
  text-align: center;
}

.empty-tip {
  max-width: 520px;
  margin: 12px auto 20px;
  color: #64748b;
  line-height: 1.7;
}

.back-to-top {
  position: fixed;
  right: 24px;
  bottom: 24px;
  z-index: 30;
  padding: 11px 16px;
  border: none;
  border-radius: 999px;
  background: #1d4ed8;
  color: white;
  box-shadow: 0 14px 24px rgba(15, 23, 42, 0.18);
  cursor: pointer;
  font-weight: 700;
}

@media (max-width: 980px) {
  .hero-header,
  .hero-grid,
  .summary-top {
    grid-template-columns: 1fr;
  }

  .hero-actions {
    justify-items: start;
  }

  .action-note {
    text-align: left;
  }

  .action-row {
    justify-content: flex-start;
  }
}

@media (max-width: 720px) {
  .page {
    padding: 20px 12px 42px;
  }

  .summary-card,
  .map-section {
    padding: 18px;
    border-radius: 20px;
  }

  .anchor-nav {
    overflow-x: auto;
    flex-wrap: nowrap;
    padding-bottom: 10px;
  }

  .hero-copy h1 {
    font-size: 38px;
  }

  .back-to-top {
    right: 16px;
    bottom: 16px;
  }
}
</style>
