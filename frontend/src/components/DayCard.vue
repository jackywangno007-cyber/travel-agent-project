<template>
  <article
    class="day-card"
    :class="{ active, faded }"
    @click="$emit('toggle-day', day.day)"
  >
    <div class="day-head">
      <div>
        <div class="day-kicker">Day {{ day.day }}</div>
        <h2>{{ day.date }}</h2>
      </div>

      <div class="day-head-actions">
        <button
          type="button"
          class="regen-button"
          :disabled="regenerating"
          @click.stop="$emit('regenerate-day', day.day)"
        >
          {{ regenerating ? "重规划中..." : "重规划当天" }}
        </button>
        <span class="day-action">
          {{ active ? "再次点击查看全部地图" : "点击高亮当天景点" }}
        </span>
      </div>
    </div>

    <div v-if="regenerateError" class="day-error">
      {{ regenerateError }}
    </div>

    <div class="overview-grid">
      <section class="panel theme-panel">
        <span class="panel-label">主题</span>
        <strong>{{ day.theme }}</strong>
      </section>

      <section class="panel weather-panel">
        <span class="panel-label">天气</span>
        <strong v-if="day.weather">{{ day.weather.weather }}</strong>
        <span v-if="day.weather">{{ day.weather.temperature }}</span>
        <span v-else>暂无天气信息</span>
      </section>

      <section class="panel budget-panel">
        <span class="panel-label">当日预算</span>
        <strong>¥{{ formatMoney(day.estimated_cost) }}</strong>
        <span>酒店 ¥{{ formatMoney(dayBudget.hotel) }} / 门票 ¥{{ formatMoney(dayBudget.tickets) }}</span>
        <span>餐饮 ¥{{ formatMoney(dayBudget.meals) }} / 其他 ¥{{ formatMoney(dayBudget.other) }}</span>
      </section>
    </div>

    <div class="content-grid">
      <section class="section attractions-section">
        <div class="section-head">
          <h3>景点安排</h3>
          <span>{{ day.attractions.length }} 个景点</span>
        </div>

        <div class="attraction-list">
          <article
            v-for="(attraction, index) in day.attractions"
            :key="`${day.day}-${attraction.name}-${attraction.address}-${index}`"
            class="attraction-card"
            @click.stop
          >
            <div v-if="showImage(attraction.image_url)" class="image-shell">
              <img
                :src="attraction.image_url!"
                :alt="attraction.name"
                class="attraction-image"
                loading="lazy"
                referrerpolicy="no-referrer"
                crossorigin="anonymous"
                @error="handleImageError"
              />
            </div>
            <div v-else class="compact-placeholder">
              <span>{{ attraction.name }}</span>
            </div>

            <div class="attraction-head">
              <div class="title-wrap">
                <span class="order-badge">{{ day.day }}-{{ index + 1 }}</span>
                <div>
                  <h4>{{ attraction.name }}</h4>
                  <span v-if="attraction.category" class="category-chip">
                    {{ attraction.category }}
                  </span>
                </div>
              </div>

              <div class="action-group">
                <button
                  type="button"
                  class="icon-button"
                  :disabled="index === 0"
                  @click.stop="$emit('move-attraction', day.day, index, 'up')"
                >
                  上移
                </button>
                <button
                  type="button"
                  class="icon-button"
                  :disabled="index === day.attractions.length - 1"
                  @click.stop="$emit('move-attraction', day.day, index, 'down')"
                >
                  下移
                </button>
                <button
                  type="button"
                  class="icon-button danger"
                  @click.stop="$emit('delete-attraction', day.day, index)"
                >
                  删除
                </button>
              </div>
            </div>

            <p class="attraction-desc">{{ attraction.description }}</p>

            <div class="field-grid">
              <div class="field-block">
                <span class="field-label">地址</span>
                <span>{{ attraction.address }}</span>
              </div>

              <div class="field-block">
                <span class="field-label">坐标</span>
                <span>
                  {{ formatCoordinate(attraction.location.longitude) }},
                  {{ formatCoordinate(attraction.location.latitude) }}
                </span>
              </div>

              <div class="field-block">
                <span class="field-label">建议时长</span>
                <span>
                  {{ attraction.suggested_duration }}
                  <template v-if="attraction.visit_duration">
                    （{{ attraction.visit_duration }} 分钟）
                  </template>
                </span>
              </div>

              <div class="field-block">
                <span class="field-label">门票</span>
                <span>{{ formatTicketPrice(attraction) }}</span>
              </div>

              <div
                v-if="attraction.rating !== null && attraction.rating !== undefined"
                class="field-block"
              >
                <span class="field-label">评分</span>
                <span>{{ attraction.rating }}</span>
              </div>

              <div v-if="attraction.ticket_price_note" class="field-block full-width">
                <span class="field-label">门票说明</span>
                <span>{{ attraction.ticket_price_note }}</span>
              </div>
            </div>
          </article>

          <div v-if="day.attractions.length === 0" class="empty-state warm">
            当前这一天暂时没有景点，你仍然可以查看交通、餐饮、酒店和天气信息。
          </div>
        </div>

        <article class="info-card export-only export-meals-card">
          <div class="section-head">
            <h3>餐饮安排</h3>
          </div>
          <div class="meal-list">
            <div v-for="meal in mealEntries" :key="`export-${meal.meal_type}`" class="meal-item">
              <div class="meal-head">
                <div class="meal-title">
                  <span class="meal-type">{{ mealLabel(meal.meal_type) }}</span>
                  <span v-if="meal.source === 'fallback'" class="source-badge fallback">备用推荐</span>
                  <span v-else class="source-badge real">真实推荐</span>
                </div>
                <strong>¥{{ formatMoney(meal.estimated_cost) }}</strong>
              </div>
              <div class="meal-name">{{ meal.name }}</div>
              <div v-if="meal.category" class="meal-category">{{ meal.category }}</div>
              <div class="meal-desc">{{ meal.description || "适合安排在当天行程附近顺路就餐。" }}</div>
              <div v-if="meal.address" class="meal-address">{{ meal.address }}</div>
            </div>
          </div>
        </article>
      </section>

      <section class="section side-section">
        <div class="side-stack">
          <article class="info-card transport-card">
            <div class="section-head">
              <h3>交通方式</h3>
            </div>
            <p class="info-primary">{{ transportation.mode }}</p>
            <p>{{ transportation.route_summary }}</p>
            <p v-if="transportation.estimated_travel_time_minutes !== null">
              预计交通耗时：{{ transportation.estimated_travel_time_minutes }} 分钟
            </p>
            <ul v-if="transportation.transport_tips.length" class="tip-list">
              <li v-for="tip in transportation.transport_tips" :key="tip">
                {{ tip }}
              </li>
            </ul>
          </article>

          <article class="info-card screen-meals-card">
            <div class="section-head">
              <h3>餐饮安排</h3>
              <span>{{ mealSummary }}</span>
            </div>

            <div v-if="mealEntries.length > 0" class="meal-list">
              <div v-for="meal in mealEntries" :key="meal.meal_type" class="meal-item">
                <div class="meal-head">
                  <div class="meal-title">
                    <span class="meal-type">{{ mealLabel(meal.meal_type) }}</span>
                    <span v-if="meal.source === 'fallback'" class="source-badge fallback">备用推荐</span>
                    <span v-else class="source-badge real">真实推荐</span>
                  </div>
                  <strong>¥{{ formatMoney(meal.estimated_cost) }}</strong>
                </div>
                <div class="meal-name">{{ meal.name }}</div>
                <div v-if="meal.category" class="meal-category">{{ meal.category }}</div>
                <div class="meal-desc">{{ meal.description || "适合安排在当天行程附近顺路就餐。" }}</div>
                <div v-if="meal.address" class="meal-address">{{ meal.address }}</div>
              </div>
            </div>

            <div v-else class="empty-state">
              当前没有可展示的餐饮安排。
            </div>
          </article>

          <article class="info-card">
            <div class="section-head">
              <h3>酒店</h3>
            </div>
            <p v-if="day.hotel" class="info-primary">{{ day.hotel.name }}</p>
            <p v-if="day.hotel">¥{{ formatMoney(day.hotel.price_per_night) }} / 晚</p>
            <p v-if="day.hotel">{{ day.hotel.location_summary }}</p>
            <p v-if="day.hotel">{{ day.hotel.address }}</p>
            <p v-if="day.hotel">{{ day.hotel.description }}</p>
            <p v-if="day.hotel?.price_note" class="field-label">{{ day.hotel.price_note }}</p>
            <p v-else>暂无酒店推荐</p>
          </article>

          <article class="info-card">
            <div class="section-head">
              <h3>预算拆分</h3>
              <span>实时汇总</span>
            </div>
            <div class="mini-budget">
              <div class="mini-budget-row">
                <span class="field-label">酒店</span>
                <strong>¥{{ formatMoney(dayBudget.hotel) }}</strong>
              </div>
              <div class="mini-budget-row">
                <span class="field-label">景点门票</span>
                <strong>¥{{ formatMoney(dayBudget.tickets) }}</strong>
              </div>
              <div class="mini-budget-row">
                <span class="field-label">餐饮</span>
                <strong>¥{{ formatMoney(dayBudget.meals) }}</strong>
              </div>
              <div class="mini-budget-row">
                <span class="field-label">其他预估</span>
                <strong>¥{{ formatMoney(dayBudget.other) }}</strong>
              </div>
            </div>
            <div class="formula-note">
              当日预算 = 酒店 + 门票 + 餐饮 + 其他预估
            </div>
          </article>
        </div>
      </section>
    </div>
  </article>
</template>

<script setup lang="ts">
import { computed } from "vue";

import type { AttractionInfo, DayPlan, MealInfo, TransportationInfo } from "../types";

defineEmits<{
  (event: "toggle-day", day: number): void;
  (event: "delete-attraction", day: number, attractionIndex: number): void;
  (event: "move-attraction", day: number, attractionIndex: number, direction: "up" | "down"): void;
  (event: "regenerate-day", day: number): void;
}>();

const props = defineProps<{
  day: DayPlan;
  active: boolean;
  faded: boolean;
  dayBudget: {
    hotel: number;
    tickets: number;
    meals: number;
    other: number;
  };
  regenerating?: boolean;
  regenerateError?: string;
}>();

const mealEntries = computed<MealInfo[]>(() =>
  [
    props.day.meals?.breakfast,
    props.day.meals?.lunch,
    props.day.meals?.dinner,
    props.day.meals?.snack,
  ].filter((item): item is MealInfo => Boolean(item))
);

const transportation = computed<TransportationInfo>(() => ({
  mode: props.day.transportation?.mode ?? "城市内灵活出行",
  route_summary:
    props.day.transportation?.route_summary ??
    "建议围绕当天景点顺路游览，优先选择距离更近的路线。",
  estimated_travel_time_minutes:
    props.day.transportation?.estimated_travel_time_minutes ?? null,
  transport_tips:
    props.day.transportation?.transport_tips?.length
      ? props.day.transportation.transport_tips
      : ["可优先结合地铁、步行和短途打车灵活衔接。"],
}));

const mealSummary = computed(() => {
  if (mealEntries.value.length === 0) {
    return "暂无餐饮";
  }

  const fallbackCount = mealEntries.value.filter((meal) => meal.source === "fallback").length;
  if (fallbackCount === mealEntries.value.length) {
    return "当前为备用餐饮方案";
  }
  if (fallbackCount > 0) {
    return "部分为备用餐饮方案";
  }
  return "已接入真实餐饮";
});

function formatCoordinate(value: number) {
  return value.toFixed(6);
}

function formatMoney(value: number) {
  return Math.round(value);
}

function formatTicketPrice(attraction: AttractionInfo) {
  if (attraction.ticket_price === null || attraction.ticket_price === undefined) {
    return "待确认";
  }
  if (attraction.ticket_price === 0) {
    return "免费或无单独门票";
  }
  return `¥${attraction.ticket_price}`;
}

function mealLabel(type: MealInfo["meal_type"]) {
  return {
    breakfast: "早餐",
    lunch: "午餐",
    dinner: "晚餐",
    snack: "小吃",
  }[type];
}

function showImage(imageUrl?: string | null) {
  return Boolean(imageUrl && imageUrl.trim());
}

function handleImageError(event: Event) {
  const target = event.target as HTMLImageElement | null;
  if (!target) {
    return;
  }
  target.style.display = "none";
  const shell = target.parentElement;
  if (shell) {
    shell.classList.add("image-shell-fallback");
  }
}
</script>

<style scoped>
.day-card {
  background: white;
  padding: 22px;
  border-radius: 20px;
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.08);
  cursor: pointer;
  transition: transform 0.18s ease, box-shadow 0.18s ease, opacity 0.18s ease;
}

.day-card:hover {
  transform: translateY(-2px);
}

.day-card.active {
  box-shadow: 0 12px 32px rgba(29, 78, 216, 0.16);
  border: 1px solid #bfd3ff;
}

.day-card.faded {
  opacity: 0.58;
}

.day-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
  margin-bottom: 18px;
}

.day-head-actions {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 10px;
}

.day-kicker {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: 999px;
  background: #dbeafe;
  color: #1d4ed8;
  font-size: 12px;
  font-weight: 700;
  margin-bottom: 8px;
}

.day-head h2 {
  margin: 0;
  font-size: 28px;
}

.day-action {
  color: #1d4ed8;
  font-size: 13px;
  font-weight: 600;
}

.regen-button {
  padding: 9px 14px;
  border: none;
  border-radius: 10px;
  background: #0f766e;
  color: white;
  cursor: pointer;
}

.regen-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.day-error {
  margin-bottom: 16px;
  padding: 12px 14px;
  border-radius: 12px;
  background: #fef2f2;
  color: #b91c1c;
  line-height: 1.6;
}

.overview-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
  margin-bottom: 18px;
}

.panel {
  padding: 16px;
  border-radius: 16px;
}

.theme-panel {
  background: #eff6ff;
}

.weather-panel {
  background: #f8fafc;
}

.budget-panel {
  background: #fff7ed;
}

.panel-label {
  display: block;
  margin-bottom: 8px;
  color: #64748b;
  font-size: 12px;
}

.panel strong {
  display: block;
  margin-bottom: 4px;
  font-size: 18px;
}

.content-grid {
  display: grid;
  grid-template-columns: minmax(0, 2fr) minmax(280px, 1fr);
  gap: 18px;
}

.section {
  background: #f8fafc;
  border-radius: 18px;
  padding: 16px;
}

.section-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 14px;
}

.section-head h3 {
  margin: 0;
}

.section-head span {
  color: #64748b;
  font-size: 13px;
}

.attraction-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.attraction-card {
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  padding: 16px;
  background: white;
}

.image-shell {
  position: relative;
  width: 100%;
  height: 190px;
  margin-bottom: 16px;
  overflow: hidden;
  border-radius: 14px;
  background: linear-gradient(135deg, #dbeafe 0%, #eff6ff 100%);
}

.image-shell-fallback {
  height: 48px;
  margin-bottom: 12px;
}

.attraction-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.compact-placeholder {
  display: inline-flex;
  align-items: center;
  min-height: 38px;
  margin-bottom: 14px;
  padding: 8px 12px;
  border-radius: 12px;
  background: #eef4ff;
  color: #1d4ed8;
  font-size: 13px;
  font-weight: 700;
}

.attraction-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
}

.title-wrap {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.title-wrap h4 {
  margin: 0 0 6px;
  font-size: 18px;
}

.order-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 44px;
  height: 28px;
  padding: 0 10px;
  border-radius: 999px;
  background: #1d4ed8;
  color: white;
  font-size: 12px;
  font-weight: 700;
}

.category-chip {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: 999px;
  background: #e8f1ff;
  color: #1d4ed8;
  font-size: 13px;
  font-weight: 600;
}

.action-group {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.icon-button {
  padding: 6px 10px;
  border: 1px solid #dbeafe;
  border-radius: 10px;
  background: #eff6ff;
  color: #1d4ed8;
  cursor: pointer;
}

.icon-button:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.icon-button.danger {
  border-color: #fecaca;
  background: #fef2f2;
  color: #dc2626;
}

.attraction-desc {
  margin: 12px 0 14px;
  color: #475569;
  line-height: 1.7;
}

.field-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.field-block {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 12px;
  border-radius: 12px;
  background: #f8fafc;
}

.field-block.full-width {
  grid-column: 1 / -1;
}

.field-label {
  font-size: 12px;
  color: #64748b;
}

.empty-state {
  padding: 16px;
  border-radius: 14px;
  background: #f8fafc;
  color: #475569;
  line-height: 1.6;
}

.empty-state.warm {
  background: #fff7ed;
  color: #9a3412;
}

.side-stack {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.info-card {
  padding: 16px;
  border-radius: 16px;
  background: white;
  border: 1px solid #e2e8f0;
}

.info-card p {
  margin: 8px 0 0;
  color: #475569;
  line-height: 1.6;
}

.info-primary {
  font-size: 18px;
  font-weight: 700;
  color: #0f172a;
}

.mini-budget {
  display: grid;
  gap: 10px;
}

.mini-budget-row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 12px;
  border-radius: 12px;
  background: #f8fafc;
}

.formula-note {
  margin-top: 12px;
  font-size: 12px;
  color: #64748b;
}

.meal-list {
  display: grid;
  gap: 12px;
}

.meal-item {
  padding: 12px;
  border-radius: 12px;
  background: #fefce8;
}

.meal-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 6px;
}

.meal-title {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.meal-type {
  font-size: 12px;
  color: #854d0e;
  font-weight: 700;
}

.source-badge {
  display: inline-flex;
  align-items: center;
  padding: 3px 8px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
}

.source-badge.real {
  background: #dcfce7;
  color: #166534;
}

.source-badge.fallback {
  background: #fee2e2;
  color: #b91c1c;
}

.meal-name {
  font-weight: 700;
  color: #0f172a;
}

.meal-category {
  margin-top: 4px;
  color: #1d4ed8;
  font-size: 12px;
  font-weight: 600;
}

.meal-desc,
.meal-address {
  margin-top: 4px;
  color: #475569;
  line-height: 1.6;
}

.tip-list {
  margin: 10px 0 0;
  padding-left: 18px;
  color: #475569;
  line-height: 1.7;
}

.transport-card {
  background: linear-gradient(180deg, #f8fbff 0%, #ffffff 100%);
}

.export-only {
  display: none;
}

@media (max-width: 900px) {
  .overview-grid,
  .content-grid,
  .field-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .day-head,
  .section-head,
  .title-wrap,
  .attraction-head,
  .meal-head,
  .mini-budget-row {
    flex-direction: column;
    align-items: flex-start;
  }

  .day-head-actions {
    width: 100%;
    align-items: flex-start;
  }

  .day-head h2 {
    font-size: 24px;
  }

  .image-shell {
    height: 160px;
  }
}
</style>
