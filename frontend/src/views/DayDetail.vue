<template>
  <div v-if="trip && dayPlan" class="page">
    <div class="container">
      <header class="detail-hero">
        <div class="hero-copy surface-card">
          <div class="hero-actions">
            <button type="button" class="back-button" @click="goBackToResult">返回结果页</button>
            <button type="button" class="text-button" @click="goHome">返回首页</button>
          </div>

          <div class="hero-title">
            <span class="day-badge">Day {{ dayPlan.day }}</span>
            <h1>{{ trip.destination }} · {{ dayPlan.date }}</h1>
            <p class="theme-text">{{ dayPlan.theme }}</p>
            <p class="intro-text">
              这是单日完整行程详情页。你可以从地图、站点顺序、餐饮安排和预算拆分四个角度快速理解这一天的节奏。
            </p>
          </div>
        </div>

        <div class="hero-metrics">
          <article class="metric-card surface-card">
            <span class="metric-label">天气</span>
            <strong>{{ dayPlan.weather?.weather ?? "待确认" }}</strong>
            <span>{{ dayPlan.weather?.temperature ?? "暂无天气信息" }}</span>
          </article>
          <article class="metric-card surface-card">
            <span class="metric-label">当日预算</span>
            <strong>¥{{ formatMoney(dayPlan.estimated_cost) }}</strong>
            <span>{{ dayPlan.attractions.length }} 个景点 · {{ mealEntries.length }} 个餐饮安排</span>
          </article>
          <article class="metric-card surface-card">
            <span class="metric-label">路线节奏</span>
            <strong>{{ routeRhythm }}</strong>
            <span>{{ transportation.mode }}</span>
          </article>
        </div>
      </header>

      <section class="overview-grid">
        <article class="overview-card surface-card">
          <span class="overview-label">日期</span>
          <strong>{{ dayPlan.date }}</strong>
          <span>围绕 {{ trip.destination }} 的单日路线安排</span>
        </article>
        <article class="overview-card surface-card">
          <span class="overview-label">主题</span>
          <strong>{{ dayPlan.theme }}</strong>
          <span>适合按当前顺序展开一天的游览节奏</span>
        </article>
        <article class="overview-card surface-card">
          <span class="overview-label">站点数量</span>
          <strong>{{ dayPlan.attractions.length }} 站</strong>
          <span>可在时间线与地图中对照查看</span>
        </article>
      </section>

      <section class="content-grid">
        <section class="main-column">
          <article class="section-card surface-card">
            <div class="section-head">
              <div>
                <span class="section-kicker">Route Overview</span>
                <h2>当天路线地图</h2>
                <p>地图会高亮当前这一天的点位与折线，帮助你从空间角度理解整条路线。</p>
              </div>
            </div>

            <MapView
              :points="dayMapPoints"
              :active-day="dayPlan.day"
              :focused-point-key="focusedPointKey"
              @clear-active-day="focusedPointKey = null"
            />
          </article>

          <article class="section-card surface-card">
            <div class="section-head">
              <div>
                <span class="section-kicker">Daily Steps</span>
                <h2>单日行程时间线</h2>
                <p>按照访问顺序查看每一站的图片、位置、停留建议，以及景点之间的通行方式。</p>
              </div>
            </div>

            <div v-if="timelineItems.length" class="timeline">
              <template v-for="item in timelineItems" :key="item.key">
                <article
                  v-if="item.type === 'stop'"
                  class="timeline-stop"
                  @click="focusAttraction(item.index)"
                >
                  <div class="timeline-rail">
                    <span class="stop-index">第{{ item.index + 1 }}站</span>
                    <span class="rail-dot"></span>
                  </div>

                  <div class="stop-card">
                    <div v-if="showImage(item.attraction.image_url, item.index)" class="image-shell">
                      <img
                        :src="item.attraction.image_url!"
                        :alt="item.attraction.name"
                        class="attraction-image"
                        loading="lazy"
                        referrerpolicy="no-referrer"
                        crossorigin="anonymous"
                        @error="handleImageError(item.index)"
                      />
                    </div>

                    <div class="stop-head">
                      <div class="title-wrap">
                        <h3>{{ item.attraction.name }}</h3>
                        <div class="meta-row">
                          <span v-if="item.attraction.category" class="category-chip">
                            {{ item.attraction.category }}
                          </span>
                          <span
                            v-if="item.attraction.rating !== null && item.attraction.rating !== undefined"
                            class="rating-chip"
                          >
                            评分 {{ item.attraction.rating }}
                          </span>
                        </div>
                      </div>
                      <button type="button" class="locate-button" @click.stop="focusAttraction(item.index)">
                        地图定位
                      </button>
                    </div>

                    <p class="attraction-desc">{{ item.attraction.description }}</p>

                    <div class="field-grid">
                      <div class="field-block">
                        <span class="field-label">地址</span>
                        <span>{{ item.attraction.address }}</span>
                      </div>
                      <div class="field-block">
                        <span class="field-label">位置坐标</span>
                        <span>
                          {{ formatCoordinate(item.attraction.location.longitude) }},
                          {{ formatCoordinate(item.attraction.location.latitude) }}
                        </span>
                      </div>
                      <div class="field-block">
                        <span class="field-label">建议停留</span>
                        <span>
                          {{ item.attraction.suggested_duration }}
                          <template v-if="item.attraction.visit_duration">
                            （{{ item.attraction.visit_duration }} 分钟）
                          </template>
                        </span>
                      </div>
                      <div class="field-block">
                        <span class="field-label">门票</span>
                        <span>{{ formatTicketPrice(item.attraction.ticket_price) }}</span>
                      </div>
                      <div v-if="item.attraction.ticket_price_note" class="field-block full-width">
                        <span class="field-label">门票说明</span>
                        <span>{{ item.attraction.ticket_price_note }}</span>
                      </div>
                    </div>
                  </div>
                </article>

                <div v-else class="timeline-transfer">
                  <div class="timeline-rail transfer-rail">
                    <span class="transfer-marker">→</span>
                  </div>
                  <div class="transfer-card">
                    <div class="transfer-head">
                      <span class="transfer-chip">{{ item.mode }}</span>
                      <strong>{{ item.timeLabel }}</strong>
                    </div>
                    <p>{{ item.summary }}</p>
                    <span class="transfer-distance">{{ item.distanceLabel }}</span>
                  </div>
                </div>
              </template>
            </div>

            <div v-else class="empty-card">
              当前这一天暂时没有景点安排，可返回结果页重新规划。
            </div>
          </article>
        </section>

        <aside class="side-column">
          <article class="section-card surface-card">
            <div class="section-head compact">
              <div>
                <span class="section-kicker">Transport</span>
                <h2>交通方式摘要</h2>
                <p>用来快速判断当天更适合步行、地铁衔接还是打车补足。</p>
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

          <article class="section-card surface-card">
            <div class="section-head compact">
              <div>
                <span class="section-kicker">Meals</span>
                <h2>餐饮安排</h2>
                <p>早餐、午餐、晚餐和小吃会按顺路原则展示在这里。</p>
              </div>
            </div>

            <div v-if="mealEntries.length" class="meal-list">
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
                <div class="meal-desc">{{ meal.description || "适合顺路安排的用餐点。" }}</div>
                <div v-if="meal.address" class="meal-address">{{ meal.address }}</div>
              </div>
            </div>

            <div v-else class="empty-card">当前没有可展示的餐饮安排。</div>
          </article>

          <article class="section-card surface-card">
            <div class="section-head compact">
              <div>
                <span class="section-kicker">Stay</span>
                <h2>酒店与结束信息</h2>
                <p>作为当天起止落点，也方便理解晚上回程与休息安排。</p>
              </div>
            </div>

            <template v-if="dayPlan.hotel">
              <p class="info-primary">{{ dayPlan.hotel.name }}</p>
              <p>¥{{ formatMoney(dayPlan.hotel.price_per_night) }} / 晚</p>
              <p>{{ dayPlan.hotel.location_summary }}</p>
              <p>{{ dayPlan.hotel.address }}</p>
              <p>{{ dayPlan.hotel.description }}</p>
              <p v-if="dayPlan.hotel.price_note" class="field-label">{{ dayPlan.hotel.price_note }}</p>
              <div class="end-note">
                建议在最后一站结束后，优先按当前交通方式返回酒店或就近用餐休息，让第二天衔接更从容。
              </div>
            </template>
            <div v-else class="empty-card">当前没有酒店推荐信息。</div>
          </article>

          <article class="section-card surface-card">
            <div class="section-head compact">
              <div>
                <span class="section-kicker">Budget</span>
                <h2>预算拆分</h2>
                <p>核对当天费用结构，方便和总预算一起对照。</p>
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
          </article>
        </aside>
      </section>
    </div>
  </div>

  <div v-else class="page">
    <div class="container empty-page">
      <h1>没有找到当天行程</h1>
      <p>当前没有可恢复的单日详情数据，请先返回结果页或重新生成旅行计划。</p>
      <div class="empty-actions">
        <button type="button" class="back-button" @click="goBackToResult">返回结果页</button>
        <button type="button" class="primary-button" @click="goHome">返回首页</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { useRoute, useRouter } from "vue-router";

import MapView from "../components/MapView.vue";
import { useEditableTripPlan } from "../stores/trip";
import type { AttractionInfo, MapAttractionPoint, MealInfo, TransportationInfo } from "../types";

type TimelineStopItem = {
  type: "stop";
  key: string;
  index: number;
  attraction: AttractionInfo;
};

type TimelineTransferItem = {
  type: "transfer";
  key: string;
  mode: string;
  summary: string;
  timeLabel: string;
  distanceLabel: string;
};

type TimelineItem = TimelineStopItem | TimelineTransferItem;

const route = useRoute();
const router = useRouter();
const failedImageIndexes = ref<number[]>([]);
const focusedPointKey = ref<string | null>(null);

const { tripPlan, loadFromSessionStorage, getDayPlan } = useEditableTripPlan();

if (typeof window !== "undefined") {
  loadFromSessionStorage();
}

const trip = computed(() => tripPlan.value);
const dayIndex = computed(() => Number(route.params.dayIndex));
const dayPlan = computed(() => {
  if (!Number.isFinite(dayIndex.value)) {
    return null;
  }
  return getDayPlan(dayIndex.value);
});

const transportation = computed<TransportationInfo>(() => ({
  mode: dayPlan.value?.transportation?.mode ?? "城市内灵活出行",
  route_summary:
    dayPlan.value?.transportation?.route_summary ??
    "建议围绕当天景点顺路游览，优先选择距离更近的路线。",
  estimated_travel_time_minutes: dayPlan.value?.transportation?.estimated_travel_time_minutes ?? null,
  transport_tips:
    dayPlan.value?.transportation?.transport_tips?.length
      ? dayPlan.value.transportation.transport_tips
      : ["可优先结合地铁、步行和短途打车灵活衔接。"],
}));

const mealEntries = computed<MealInfo[]>(() =>
  [
    dayPlan.value?.meals?.breakfast,
    dayPlan.value?.meals?.lunch,
    dayPlan.value?.meals?.dinner,
    dayPlan.value?.meals?.snack,
  ].filter((item): item is MealInfo => Boolean(item))
);

const dayBudget = computed(() => {
  if (!dayPlan.value) {
    return { hotel: 0, tickets: 0, meals: 0, other: 0 };
  }

  const hotel = dayPlan.value.hotel?.price_per_night ?? 0;
  const tickets = dayPlan.value.attractions.reduce((sum, item) => sum + (item.ticket_price ?? 0), 0);
  const meals = mealEntries.value.reduce((sum, meal) => sum + (meal.estimated_cost ?? 0), 0);
  const other = Math.max(dayPlan.value.estimated_cost - hotel - tickets - meals, 0);

  return { hotel, tickets, meals, other };
});

const routeRhythm = computed(() => {
  if (!dayPlan.value) {
    return "待确认";
  }
  if (dayPlan.value.attractions.length <= 1) {
    return "单点轻行程";
  }
  if (dayPlan.value.attractions.length === 2) {
    return "双站串联";
  }
  return `${dayPlan.value.attractions.length} 站顺路游览`;
});

const dayMapPoints = computed<MapAttractionPoint[]>(() => {
  if (!dayPlan.value) {
    return [];
  }

  return dayPlan.value.attractions.map((attraction, index) => ({
    key: `${dayPlan.value!.day}-${index + 1}`,
    day: dayPlan.value!.day,
    date: dayPlan.value!.date,
    orderInDay: index + 1,
    sequenceLabel: `第${index + 1}站`,
    name: attraction.name,
    address: attraction.address,
    location: attraction.location,
    category: attraction.category,
  }));
});

const timelineItems = computed<TimelineItem[]>(() => {
  if (!dayPlan.value) {
    return [];
  }

  const attractions = dayPlan.value.attractions;
  const items: TimelineItem[] = [];

  attractions.forEach((attraction, index) => {
    items.push({
      type: "stop",
      key: `stop-${index}`,
      index,
      attraction,
    });

    if (index < attractions.length - 1) {
      const nextAttraction = attractions[index + 1];
      const distanceKm = haversineKm(attraction, nextAttraction);
      const transfer = buildTransferInfo(distanceKm, transportation.value.mode, index === 0);

      items.push({
        type: "transfer",
        key: `transfer-${index}`,
        mode: transfer.mode,
        summary: `${attraction.name} → ${nextAttraction.name}`,
        timeLabel: transfer.timeLabel,
        distanceLabel: transfer.distanceLabel,
      });
    }
  });

  if (attractions.length === 1) {
    const transfer = buildArrivalInfo(transportation.value.mode);
    items.push({
      type: "transfer",
      key: "arrival-only",
      mode: transfer.mode,
      summary: `建议从酒店或出发点前往 ${attractions[0].name}`,
      timeLabel: transfer.timeLabel,
      distanceLabel: transfer.distanceLabel,
    });
  }

  return items;
});

function goBackToResult() {
  router.push("/result");
}

function goHome() {
  router.push("/");
}

function focusAttraction(index: number) {
  if (!dayPlan.value) {
    return;
  }
  focusedPointKey.value = `${dayPlan.value.day}-${index + 1}`;
}

function formatMoney(value: number) {
  return Math.round(value);
}

function formatCoordinate(value: number) {
  return value.toFixed(6);
}

function formatTicketPrice(price?: number | null) {
  if (price === null || price === undefined) {
    return "待确认";
  }
  if (price === 0) {
    return "免费或无单独门票";
  }
  return `¥${price}`;
}

function mealLabel(type: MealInfo["meal_type"]) {
  return {
    breakfast: "早餐",
    lunch: "午餐",
    dinner: "晚餐",
    snack: "小吃",
  }[type];
}

function showImage(imageUrl?: string | null, index?: number) {
  if (typeof index === "number" && failedImageIndexes.value.includes(index)) {
    return false;
  }
  return Boolean(imageUrl && imageUrl.trim());
}

function handleImageError(index: number) {
  return () => {
    if (!failedImageIndexes.value.includes(index)) {
      failedImageIndexes.value = [...failedImageIndexes.value, index];
    }
  };
}

function haversineKm(first: AttractionInfo, second: AttractionInfo) {
  const toRadians = (value: number) => (value * Math.PI) / 180;
  const lon1 = toRadians(first.location.longitude);
  const lat1 = toRadians(first.location.latitude);
  const lon2 = toRadians(second.location.longitude);
  const lat2 = toRadians(second.location.latitude);

  const dlon = lon2 - lon1;
  const dlat = lat2 - lat1;
  const value =
    Math.sin(dlat / 2) ** 2 +
    Math.cos(lat1) * Math.cos(lat2) * Math.sin(dlon / 2) ** 2;
  return 6371 * 2 * Math.asin(Math.sqrt(value));
}

function buildTransferInfo(distanceKm: number, overallMode: string, isFirstLeg: boolean) {
  if (distanceKm <= 1.2) {
    return {
      mode: "步行",
      timeLabel: `约 ${Math.max(8, Math.round(distanceKm * 15))} 分钟`,
      distanceLabel: `距离约 ${distanceKm.toFixed(1)} km`,
    };
  }

  if (distanceKm <= 4.5) {
    return {
      mode: overallMode.includes("地铁") ? "地铁 + 步行" : "步行 / 短程打车",
      timeLabel: `约 ${Math.max(12, Math.round(distanceKm * 8))} 分钟`,
      distanceLabel: `距离约 ${distanceKm.toFixed(1)} km`,
    };
  }

  return {
    mode: overallMode.includes("打车") || isFirstLeg ? "打车 / 地铁" : "地铁 + 步行",
    timeLabel: `约 ${Math.max(18, Math.round(distanceKm * 6))} 分钟`,
    distanceLabel: `距离约 ${distanceKm.toFixed(1)} km`,
  };
}

function buildArrivalInfo(overallMode: string) {
  return {
    mode: overallMode || "地铁 / 打车",
    timeLabel: "按酒店或出发点灵活前往",
    distanceLabel: "单点行程，不展示景点间连线",
  };
}
</script>

<style scoped>
.page {
  min-height: 100vh;
  padding: 34px 18px 64px;
}

.container {
  max-width: 1240px;
  margin: 0 auto;
}

.surface-card {
  background: rgba(255, 255, 255, 0.94);
  border: 1px solid rgba(219, 234, 254, 0.9);
  box-shadow: 0 22px 54px rgba(15, 23, 42, 0.08);
  backdrop-filter: blur(12px);
}

.detail-hero {
  display: grid;
  grid-template-columns: minmax(0, 1.25fr) minmax(340px, 0.85fr);
  gap: 22px;
  align-items: stretch;
  margin-bottom: 28px;
}

.hero-copy {
  padding: 28px;
  border-radius: 30px;
  display: grid;
  gap: 20px;
}

.hero-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.back-button,
.text-button,
.locate-button,
.primary-button {
  width: fit-content;
  padding: 10px 16px;
  border-radius: 14px;
  cursor: pointer;
  font-weight: 600;
}

.back-button,
.locate-button {
  border: 1px solid #dbeafe;
  background: #eff6ff;
  color: #1d4ed8;
}

.text-button {
  border: 1px solid transparent;
  background: transparent;
  color: #475569;
}

.primary-button {
  border: none;
  background: linear-gradient(135deg, #1677ff 0%, #1d4ed8 100%);
  color: white;
}

.hero-title {
  display: grid;
  gap: 12px;
}

.day-badge {
  display: inline-flex;
  width: fit-content;
  padding: 6px 12px;
  border-radius: 999px;
  background: linear-gradient(135deg, #dbeafe 0%, #e8f1ff 100%);
  color: #1d4ed8;
  font-size: 12px;
  font-weight: 700;
}

.hero-title h1 {
  margin: 0;
  font-size: clamp(34px, 5vw, 52px);
  line-height: 1.04;
  letter-spacing: -0.04em;
}

.theme-text {
  margin: 0;
  color: #0f172a;
  font-size: 19px;
  font-weight: 600;
  line-height: 1.6;
}

.intro-text {
  margin: 0;
  color: #475569;
  line-height: 1.85;
}

.hero-metrics {
  display: grid;
  gap: 16px;
}

.metric-card {
  padding: 20px;
  border-radius: 24px;
  display: grid;
  gap: 6px;
}

.metric-label,
.field-label,
.overview-label,
.section-kicker {
  color: #64748b;
  font-size: 12px;
}

.metric-card strong,
.overview-card strong,
.info-primary {
  color: #0f172a;
  font-size: 24px;
}

.metric-card span:not(.metric-label),
.overview-card span:not(.overview-label) {
  color: #475569;
  line-height: 1.6;
}

.overview-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 18px;
  margin-bottom: 28px;
}

.overview-card {
  padding: 20px 22px;
  border-radius: 24px;
  display: grid;
  gap: 8px;
}

.content-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.72fr) minmax(320px, 0.92fr);
  gap: 22px;
}

.main-column,
.side-column {
  display: grid;
  gap: 18px;
}

.section-card {
  padding: 24px;
  border-radius: 28px;
}

.section-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 14px;
  margin-bottom: 18px;
}

.section-kicker {
  display: inline-block;
  margin-bottom: 8px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.section-head h2 {
  margin: 0;
  font-size: 24px;
  line-height: 1.2;
}

.section-head p {
  margin: 8px 0 0;
  color: #64748b;
  line-height: 1.7;
}

.timeline {
  display: grid;
  gap: 14px;
}

.timeline-stop,
.timeline-transfer {
  display: grid;
  grid-template-columns: 112px minmax(0, 1fr);
  gap: 16px;
}

.timeline-stop {
  align-items: start;
  cursor: pointer;
}

.timeline-rail {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding-top: 6px;
}

.stop-index {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 86px;
  height: 34px;
  padding: 0 14px;
  border-radius: 999px;
  background: #1d4ed8;
  color: white;
  font-size: 12px;
  font-weight: 700;
}

.rail-dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  background: #60a5fa;
  box-shadow: 0 0 0 6px rgba(96, 165, 250, 0.16);
}

.stop-card {
  border: 1px solid #e2e8f0;
  border-radius: 24px;
  padding: 16px;
  background: white;
  box-shadow: 0 14px 30px rgba(15, 23, 42, 0.05);
}

.image-shell {
  width: 100%;
  height: 220px;
  overflow: hidden;
  border-radius: 20px;
  margin-bottom: 14px;
  background: linear-gradient(135deg, #dbeafe 0%, #eff6ff 100%);
}

.attraction-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.stop-head {
  display: flex;
  justify-content: space-between;
  gap: 14px;
  align-items: flex-start;
}

.title-wrap {
  display: grid;
  gap: 8px;
}

.title-wrap h3 {
  margin: 0;
  font-size: 25px;
  line-height: 1.2;
}

.meta-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.category-chip,
.rating-chip,
.source-badge,
.transfer-chip {
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

.attraction-desc {
  margin: 14px 0;
  color: #475569;
  line-height: 1.75;
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

.transfer-rail {
  padding-top: 0;
}

.transfer-marker {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  border-radius: 999px;
  background: #eff6ff;
  color: #1d4ed8;
  font-weight: 800;
}

.transfer-card {
  padding: 14px 16px;
  border-radius: 20px;
  background: linear-gradient(180deg, #f8fbff 0%, #f8fafc 100%);
  border: 1px dashed #cbd5e1;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.8);
}

.transfer-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
  margin-bottom: 6px;
}

.transfer-chip {
  background: #eff6ff;
  color: #1d4ed8;
}

.transfer-card p {
  margin: 0 0 6px;
  color: #334155;
}

.transfer-distance {
  color: #64748b;
  font-size: 12px;
}

.meal-list {
  display: grid;
  gap: 12px;
}

.meal-item {
  padding: 12px;
  border-radius: 18px;
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
.meal-address,
.section-card p {
  color: #475569;
  line-height: 1.65;
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

.end-note {
  margin-top: 14px;
  padding: 12px 14px;
  border-radius: 14px;
  background: #eff6ff;
  color: #1e3a8a;
  line-height: 1.7;
}

.tip-list {
  margin: 10px 0 0;
  padding-left: 18px;
  color: #475569;
  line-height: 1.7;
}

.empty-card {
  padding: 16px;
  border-radius: 16px;
  background: #f8fafc;
  color: #475569;
  line-height: 1.6;
}

.empty-page {
  min-height: 70vh;
  display: grid;
  place-items: center;
  text-align: center;
}

.empty-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  justify-content: center;
  margin-top: 20px;
}

@media (max-width: 1024px) {
  .detail-hero,
  .overview-grid,
  .content-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 820px) {
  .field-grid,
  .timeline-stop,
  .timeline-transfer {
    grid-template-columns: 1fr;
  }

  .timeline-rail {
    flex-direction: row;
    justify-content: flex-start;
    padding-top: 0;
  }
}

@media (max-width: 640px) {
  .page {
    padding: 20px 12px 42px;
  }

  .hero-copy,
  .section-card {
    padding: 18px;
    border-radius: 20px;
  }

  .hero-title h1 {
    font-size: 36px;
  }

  .stop-head,
  .meal-head,
  .mini-budget-row,
  .section-head,
  .transfer-head {
    flex-direction: column;
    align-items: flex-start;
  }

  .image-shell {
    height: 180px;
  }
}
</style>
