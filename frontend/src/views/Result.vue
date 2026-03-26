<template>
  <div v-if="trip" class="page">
    <div class="container">
      <div class="header" id="top">
        <div>
          <span class="eyebrow">Travel Assistant</span>
          <h1>{{ trip.destination }} 旅行计划</h1>
        </div>
        <div class="header-actions">
          <span class="edit-note">支持删除景点、调整顺序、单日重规划与地图联动</span>
          <ExportButtons
            target-id="trip-plan-content"
            :file-base-name="`${trip.destination}-trip-plan`"
          />
          <button @click="goBack">返回重新生成</button>
        </div>
      </div>

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
          <article class="summary-card">
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
                <span class="metric-label">当前景点数</span>
                <strong>{{ totalAttractions }}</strong>
              </div>
            </div>

            <div class="summary-body">
              <div class="summary-block">
                <span class="block-label">整体总结</span>
                <p>{{ trip.summary }}</p>
              </div>
              <div v-if="trip.fallback_reason" class="summary-block warning">
                <span class="block-label">回退说明</span>
                <p>{{ trip.fallback_reason }}</p>
              </div>
            </div>
          </article>

          <section id="budget">
            <BudgetPanel :total-budget="trip.total_budget_estimate" :breakdown="budgetBreakdown" />
          </section>
        </section>

        <section id="map" data-export-map>
          <MapView
            :points="mapPoints"
            :active-day="activeDay"
            @clear-active-day="activeDay = null"
          />
        </section>

        <div class="map-legend">
          <button
            type="button"
            class="legend-chip"
            :class="{ active: activeDay === null }"
            @click="activeDay = null"
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
              :day-budget="getDayBudget(day)"
              :regenerating="regeneratingDay === day.day"
              :regenerate-error="dayErrors[day.day]"
              @toggle-day="toggleDay"
              @delete-attraction="deleteAttraction"
              @move-attraction="moveAttraction"
              @regenerate-day="handleRegenerateDay"
            />
          </section>
        </div>
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
      <button @click="goBack">返回首页</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import axios from "axios";
import { computed, onBeforeUnmount, reactive, ref } from "vue";
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

function goBack() {
  router.push("/");
}

function toggleDay(day: number) {
  activeDay.value = activeDay.value === day ? null : day;
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
    window.prompt("可选输入这一天的新偏好，例如：更轻松 / 更美食 / 更少步行 / 雨天优先", "") ?? "";
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
  padding: 32px 16px 48px;
}

.container {
  max-width: 1140px;
  margin: 0 auto;
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

.header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 16px;
  margin-bottom: 20px;
  scroll-margin-top: 96px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.edit-note {
  color: #475569;
  font-size: 13px;
}

.eyebrow {
  display: inline-flex;
  margin-bottom: 8px;
  color: #1d4ed8;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.header h1 {
  margin: 0;
  font-size: 44px;
  line-height: 1.05;
}

.header button,
.container button {
  padding: 10px 14px;
  border: none;
  border-radius: 10px;
  background: #1677ff;
  color: white;
  cursor: pointer;
}

.anchor-nav {
  position: sticky;
  top: 12px;
  z-index: 20;
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 20px;
  padding: 12px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(14px);
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.08);
}

.anchor-chip {
  background: #eff6ff;
  color: #1d4ed8;
  white-space: nowrap;
}

.hero-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) minmax(320px, 0.9fr);
  gap: 18px;
  margin-bottom: 24px;
  scroll-margin-top: 96px;
}

.summary-card {
  background: white;
  padding: 24px;
  border-radius: 18px;
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.08);
}

.summary-top {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
  margin-bottom: 18px;
}

.summary-metric {
  padding: 16px;
  border-radius: 16px;
  background: #f8fafc;
}

.metric-label,
.block-label {
  display: block;
  margin-bottom: 8px;
  color: #64748b;
  font-size: 12px;
}

.summary-metric strong {
  font-size: 24px;
}

.summary-body {
  display: grid;
  gap: 12px;
}

.summary-block {
  padding: 16px;
  border-radius: 16px;
  background: #f8fafc;
}

.summary-block p {
  margin: 0;
  color: #334155;
  line-height: 1.75;
}

.summary-block.warning {
  background: #fff7ed;
}

#budget,
#map,
.day-anchor-section {
  scroll-margin-top: 96px;
}

.map-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin: -6px 0 24px;
}

.export-content {
  display: grid;
  gap: 24px;
}

.legend-chip {
  background: #edf2ff;
  color: #1d4ed8;
}

.legend-chip.active {
  background: #1d4ed8;
  color: white;
}

.day-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.back-to-top {
  position: fixed;
  right: 24px;
  bottom: 24px;
  z-index: 30;
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.18);
}

@media (max-width: 960px) {
  .hero-grid,
  .summary-top {
    grid-template-columns: 1fr;
  }

  .anchor-nav {
    overflow-x: auto;
    flex-wrap: nowrap;
    padding-bottom: 10px;
  }
}

@media (max-width: 640px) {
  .header {
    flex-direction: column;
    align-items: flex-start;
  }

  .header-actions {
    justify-content: flex-start;
  }

  .header h1 {
    font-size: 36px;
  }

  .back-to-top {
    right: 16px;
    bottom: 16px;
  }
}
</style>
