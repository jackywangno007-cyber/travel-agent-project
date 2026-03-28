<template>
  <article class="day-card" :class="{ active, faded, expanded }">
    <div class="day-head">
      <button type="button" class="accordion-trigger" @click="handleHeaderToggle">
        <div class="day-title-group">
          <span class="day-kicker">Day {{ day.day }}</span>
          <div class="day-title-copy">
            <div class="day-title-line">
              <h2>{{ day.date }}</h2>
              <span class="expand-indicator">{{ expanded ? "收起" : "展开" }}</span>
            </div>
            <p class="day-theme">{{ day.theme }}</p>
          </div>
        </div>

        <div class="summary-pills">
          <span class="summary-pill">{{ weatherSummary }}</span>
          <span class="summary-pill">{{ day.attractions.length }} 个景点</span>
          <span class="summary-pill">路线 {{ routeSummary }}</span>
          <span class="summary-pill accent">预算 ¥{{ formatMoney(day.estimated_cost) }}</span>
        </div>
      </button>

      <div class="day-head-actions">
        <button
          type="button"
          class="detail-button"
          @click.stop="$emit('view-detail', day.day)"
        >
          查看详情
        </button>
        <button
          type="button"
          class="regen-button"
          :disabled="regenerating"
          @click.stop="$emit('regenerate-day', day.day)"
        >
          {{ regenerating ? "重规划中..." : "重规划当天" }}
        </button>
      </div>
    </div>

    <div v-if="regenerateError" class="day-error">
      {{ regenerateError }}
    </div>

    <div v-show="expanded" class="accordion-body">
      <div class="overview-grid">
        <section class="overview-card weather-card">
          <span class="overview-label">天气</span>
          <strong v-if="day.weather">{{ day.weather.weather }}</strong>
          <span v-if="day.weather">{{ day.weather.temperature }}</span>
          <span v-else>暂无天气信息</span>
        </section>

        <section class="overview-card budget-card">
          <span class="overview-label">当日预算</span>
          <strong>¥{{ formatMoney(day.estimated_cost) }}</strong>
          <div class="overview-subline">
            <span>酒店 ¥{{ formatMoney(dayBudget.hotel) }}</span>
            <span>门票 ¥{{ formatMoney(dayBudget.tickets) }}</span>
          </div>
          <div class="overview-subline">
            <span>餐饮 ¥{{ formatMoney(dayBudget.meals) }}</span>
            <span>其他 ¥{{ formatMoney(dayBudget.other) }}</span>
          </div>
        </section>

        <section class="overview-card stats-card">
          <span class="overview-label">行程概览</span>
          <strong>{{ day.attractions.length }} 个景点</strong>
          <span>{{ mealEntries.length }} 个餐饮安排</span>
        </section>
      </div>

      <div class="content-grid">
        <section class="main-column">
          <section class="section-card attractions-section">
            <div class="section-head">
              <div>
                <h3>景点安排</h3>
                <p>按访问顺序浏览。点击景点卡片可在地图中定位对应站点。</p>
              </div>
              <span class="section-meta">{{ day.attractions.length }} 个景点</span>
            </div>

            <div class="attraction-list">
              <article
                v-for="(attraction, index) in day.attractions"
                :key="`${day.day}-${attraction.name}-${attraction.address}-${index}`"
                class="attraction-card"
                @click.stop="$emit('focus-attraction', { day: day.day, orderInDay: index + 1 })"
              >
                <div class="attraction-top">
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

                  <div class="title-row">
                    <div class="title-wrap">
                      <span class="order-badge">{{ stationLabel(index + 1) }}</span>
                      <div>
                        <h4>{{ attraction.name }}</h4>
                        <div class="meta-row">
                          <span v-if="attraction.category" class="category-chip">
                            {{ attraction.category }}
                          </span>
                          <span
                            v-if="attraction.rating !== null && attraction.rating !== undefined"
                            class="rating-chip"
                          >
                            评分 {{ attraction.rating }}
                          </span>
                        </div>
                      </div>
                    </div>

                    <div class="action-group">
                      <button
                        type="button"
                        class="ghost-button"
                        :disabled="index === 0"
                        @click.stop="$emit('move-attraction', day.day, index, 'up')"
                      >
                        上移
                      </button>
                      <button
                        type="button"
                        class="ghost-button"
                        :disabled="index === day.attractions.length - 1"
                        @click.stop="$emit('move-attraction', day.day, index, 'down')"
                      >
                        下移
                      </button>
                      <button
                        type="button"
                        class="ghost-button danger"
                        @click.stop="$emit('delete-attraction', day.day, index)"
                      >
                        删除
                      </button>
                    </div>
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
          </section>

          <article class="section-card export-only export-meals-card">
            <div class="section-head">
              <div>
                <h3>餐饮安排</h3>
              </div>
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

        <aside class="side-column">
          <article class="section-card info-card transport-card">
            <div class="section-head compact">
              <div>
                <h3>交通方式</h3>
                <p>帮助理解当天景点之间如何连接。</p>
              </div>
            </div>
            <p class="info-primary">{{ transportation.mode }}</p>
            <p>{{ transportation.route_summary }}</p>
            <p v-if="transportation.estimated_travel_time_minutes !== null">
              预计交通耗时：{{ transportation.estimated_travel_time_minutes }} 分钟
            </p>
            <ul v-if="transportation.transport_tips.length" class="tip-list">
              <li v-for="tip in transportation.transport_tips" :key="tip">{{ tip }}</li>
            </ul>
          </article>

          <article class="section-card info-card screen-meals-card">
            <div class="section-head compact">
              <div>
                <h3>餐饮安排</h3>
                <p>早餐、午餐、晚餐和小吃建议。</p>
              </div>
              <span class="section-meta">{{ mealSummary }}</span>
            </div>

            <div v-if="mealEntries.length > 0" class="meal-list compact-meal-list">
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
                <div class="meal-desc clamp-two-lines">
                  {{ meal.description || "适合安排在当天行程附近顺路就餐。" }}
                </div>
                <div v-if="meal.address" class="meal-address clamp-one-line">{{ meal.address }}</div>
              </div>
            </div>

            <div v-else class="empty-state">当前没有可展示的餐饮安排。</div>
          </article>

          <article class="section-card info-card">
            <div class="section-head compact">
              <div>
                <h3>酒店</h3>
                <p>默认作为当天住宿与出行落点。</p>
              </div>
            </div>
            <p v-if="day.hotel" class="info-primary">{{ day.hotel.name }}</p>
            <p v-if="day.hotel">¥{{ formatMoney(day.hotel.price_per_night) }} / 晚</p>
            <p v-if="day.hotel">{{ day.hotel.location_summary }}</p>
            <p v-if="day.hotel">{{ day.hotel.address }}</p>
            <p v-if="day.hotel">{{ day.hotel.description }}</p>
            <p v-if="day.hotel?.price_note" class="field-label">{{ day.hotel.price_note }}</p>
            <p v-else>暂无酒店推荐</p>
          </article>

          <article class="section-card info-card budget-breakdown-card">
            <div class="section-head compact">
              <div>
                <h3>预算拆分</h3>
                <p>实时汇总当前这一天的费用结构。</p>
              </div>
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
            <div class="formula-note">当日预算 = 酒店 + 门票 + 餐饮 + 其他预估</div>
          </article>
        </aside>
      </div>
    </div>
  </article>
</template>

<script setup lang="ts">
import { computed } from "vue";

import type { AttractionInfo, DayPlan, MealInfo, TransportationInfo } from "../types";

const emit = defineEmits<{
  (event: "toggle-day", day: number): void;
  (event: "toggle-expand", day: number): void;
  (event: "delete-attraction", day: number, attractionIndex: number): void;
  (event: "move-attraction", day: number, attractionIndex: number, direction: "up" | "down"): void;
  (event: "regenerate-day", day: number): void;
  (event: "focus-attraction", payload: { day: number; orderInDay: number }): void;
  (event: "view-detail", day: number): void;
}>();

const props = defineProps<{
  day: DayPlan;
  active: boolean;
  faded: boolean;
  expanded: boolean;
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

const weatherSummary = computed(() =>
  props.day.weather ? `${props.day.weather.weather} · ${props.day.weather.temperature}` : "暂无天气"
);

const routeSummary = computed(() => {
  if (props.day.attractions.length <= 1) {
    return "单点行程";
  }
  return `${props.day.attractions.length - 1} 段路线`;
});

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

function handleHeaderToggle() {
  emit("toggle-expand", props.day.day);
  emit("toggle-day", props.day.day);
}

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

function stationLabel(order: number) {
  return "第" + order + "站";
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
  border-radius: 26px;
  border: 1px solid rgba(226, 232, 240, 0.9);
  box-shadow: 0 18px 42px rgba(15, 23, 42, 0.08);
  transition:
    box-shadow 0.18s ease,
    opacity 0.18s ease,
    border-color 0.18s ease,
    transform 0.18s ease;
}

.day-card.active {
  box-shadow: 0 22px 48px rgba(29, 78, 216, 0.14);
  border-color: #bfd3ff;
}

.day-card.faded {
  opacity: 0.58;
}

.day-card.expanded {
  padding-bottom: 26px;
  transform: translateY(-1px);
}

.day-head {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 16px;
  align-items: start;
}

.accordion-trigger {
  width: 100%;
  border: none;
  background: transparent;
  padding: 0;
  text-align: left;
  cursor: pointer;
  display: grid;
  gap: 14px;
  border-radius: 20px;
}

.day-title-group {
  display: flex;
  align-items: flex-start;
  gap: 14px;
}

.day-kicker {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 72px;
  height: 34px;
  padding: 0 14px;
  border-radius: 999px;
  background: linear-gradient(135deg, #dbeafe 0%, #e8f1ff 100%);
  color: #1d4ed8;
  font-size: 12px;
  font-weight: 700;
}

.day-title-copy {
  display: grid;
  gap: 8px;
  min-width: 0;
}

.day-title-line {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.day-title-copy h2 {
  margin: 0;
  font-size: 30px;
  line-height: 1.05;
}

.day-theme {
  margin: 0;
  color: #475569;
  font-size: 15px;
  line-height: 1.7;
}

.expand-indicator {
  flex-shrink: 0;
  padding: 6px 12px;
  border-radius: 999px;
  background: #f1f5f9;
  color: #334155;
  font-size: 12px;
  font-weight: 700;
}

.summary-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.summary-pill {
  display: inline-flex;
  align-items: center;
  padding: 8px 12px;
  border-radius: 999px;
  background: #f8fafc;
  color: #475569;
  font-size: 13px;
  font-weight: 600;
  border: 1px solid rgba(226, 232, 240, 0.8);
}

.summary-pill.accent {
  background: #fff7ed;
  color: #9a3412;
}

.day-head-actions {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 10px;
}

.detail-button {
  padding: 9px 14px;
  border: 1px solid #dbeafe;
  border-radius: 14px;
  background: #eff6ff;
  color: #1d4ed8;
  cursor: pointer;
  font-weight: 600;
}

.regen-button {
  padding: 9px 14px;
  border: none;
  border-radius: 14px;
  background: #0f766e;
  color: white;
  cursor: pointer;
  box-shadow: 0 10px 22px rgba(15, 118, 110, 0.18);
  font-weight: 700;
}

.regen-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.day-error {
  margin-top: 14px;
  padding: 12px 14px;
  border-radius: 12px;
  background: #fef2f2;
  color: #b91c1c;
  line-height: 1.6;
}

.accordion-body {
  margin-top: 20px;
  display: grid;
  gap: 20px;
}

.overview-grid {
  display: grid;
  grid-template-columns: 1fr 1.1fr 0.9fr;
  gap: 14px;
}

.overview-card {
  padding: 18px;
  border-radius: 20px;
  border: 1px solid rgba(226, 232, 240, 0.72);
}

.weather-card {
  background: #f8fafc;
}

.budget-card {
  background: #fff7ed;
}

.stats-card {
  background: #eff6ff;
}

.overview-label {
  display: block;
  margin-bottom: 8px;
  color: #64748b;
  font-size: 12px;
}

.overview-card strong {
  display: block;
  margin-bottom: 8px;
  color: #0f172a;
  font-size: 22px;
}

.overview-card span {
  color: #475569;
}

.overview-subline {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 6px;
  font-size: 13px;
}

.content-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.7fr) minmax(320px, 0.95fr);
  gap: 18px;
}

.main-column,
.side-column {
  display: grid;
  gap: 16px;
}

.section-card {
  padding: 20px;
  border-radius: 22px;
  background: #f8fafc;
}

.info-card {
  background: white;
  border: 1px solid #e2e8f0;
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.04);
}

.section-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 14px;
  margin-bottom: 16px;
}

.section-head h3 {
  margin: 0;
  font-size: 20px;
}

.section-head p {
  margin: 6px 0 0;
  color: #64748b;
  line-height: 1.6;
  font-size: 13px;
}

.section-meta {
  color: #64748b;
  font-size: 13px;
  white-space: nowrap;
}

.section-head.compact h3 {
  font-size: 18px;
}

.attraction-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.attraction-card {
  border: 1px solid #e2e8f0;
  border-radius: 20px;
  padding: 16px;
  background: white;
  box-shadow: 0 12px 28px rgba(15, 23, 42, 0.04);
}

.attraction-top {
  margin-bottom: 12px;
}

.image-shell {
  position: relative;
  width: 100%;
  height: 190px;
  margin-bottom: 14px;
  overflow: hidden;
  border-radius: 18px;
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
  min-height: 40px;
  margin-bottom: 14px;
  padding: 8px 12px;
  border-radius: 14px;
  background: #eef4ff;
  color: #1d4ed8;
  font-size: 13px;
  font-weight: 700;
}

.title-row {
  display: flex;
  justify-content: space-between;
  gap: 14px;
  align-items: flex-start;
}

.title-wrap {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.title-wrap h4 {
  margin: 0;
  color: #0f172a;
  font-size: 22px;
  line-height: 1.2;
}

.meta-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
}

.order-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 72px;
  height: 30px;
  padding: 0 12px;
  border-radius: 999px;
  background: #1d4ed8;
  color: white;
  font-size: 12px;
  font-weight: 700;
  white-space: nowrap;
}

.category-chip,
.rating-chip {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
}

.category-chip {
  background: #e8f1ff;
  color: #1d4ed8;
}

.rating-chip {
  background: #fef3c7;
  color: #92400e;
}

.action-group {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.ghost-button {
  padding: 6px 10px;
  border: 1px solid #dbe5f3;
  border-radius: 12px;
  background: #f8fafc;
  color: #475569;
  cursor: pointer;
  font-size: 12px;
  font-weight: 600;
}

.ghost-button:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.ghost-button.danger {
  border-color: #fecaca;
  color: #dc2626;
}

.attraction-desc {
  margin: 0 0 14px;
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
  border-radius: 16px;
  background: #f8fafc;
  border: 1px solid rgba(226, 232, 240, 0.7);
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

.info-primary {
  margin: 0;
  color: #0f172a;
  font-size: 19px;
  font-weight: 700;
}

.info-card p {
  margin: 8px 0 0;
  color: #475569;
  line-height: 1.65;
}

.transport-card {
  background: linear-gradient(180deg, #f8fbff 0%, #ffffff 100%);
}

.meal-list {
  display: grid;
  gap: 12px;
}

.compact-meal-list {
  max-height: 420px;
  overflow: auto;
  padding-right: 4px;
}

.meal-item {
  padding: 12px;
  border-radius: 16px;
  background: #fefce8;
  border: 1px solid rgba(253, 230, 138, 0.45);
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

.clamp-one-line {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.clamp-two-lines {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
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
  border-radius: 14px;
  background: #f8fafc;
  border: 1px solid rgba(226, 232, 240, 0.72);
}

.formula-note {
  margin-top: 12px;
  font-size: 12px;
  color: #64748b;
}

.tip-list {
  margin: 10px 0 0;
  padding-left: 18px;
  color: #475569;
  line-height: 1.7;
}

.export-only {
  display: none;
}

@media (max-width: 980px) {
  .day-head,
  .overview-grid,
  .content-grid,
  .field-grid {
    grid-template-columns: 1fr;
  }

  .compact-meal-list {
    max-height: none;
    overflow: visible;
  }
}

@media (max-width: 640px) {
  .day-card {
    padding: 18px;
  }

  .day-head,
  .title-row,
  .meal-head,
  .mini-budget-row,
  .section-head {
    flex-direction: column;
    align-items: flex-start;
  }

  .day-title-group {
    flex-direction: column;
    gap: 10px;
  }

  .day-title-copy h2 {
    font-size: 24px;
  }

  .day-head-actions {
    align-items: flex-start;
  }

  .image-shell {
    height: 160px;
  }
}
</style>
