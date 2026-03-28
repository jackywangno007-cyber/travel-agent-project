<template>
  <section class="budget-panel">
    <div class="panel-head">
      <div>
        <h3>预算概览</h3>
        <p>
          当前预算基于酒店、景点门票、餐饮安排和每日其他预估实时汇总。即使某一项显示为
          `¥0`，也表示这是当前计算结果，而不是未接通的占位值。
        </p>
      </div>
      <div class="total-box">
        <span class="total-label">总预算估算</span>
        <strong>¥{{ formatMoney(totalBudget) }}</strong>
      </div>
    </div>

    <div class="budget-grid">
      <article class="budget-card hotel">
        <span class="budget-label">酒店</span>
        <strong>¥{{ formatMoney(breakdown.hotel) }}</strong>
        <p>按每日酒店价格累计。</p>
      </article>

      <article class="budget-card ticket">
        <span class="budget-label">景点门票</span>
        <strong>¥{{ formatMoney(breakdown.tickets) }}</strong>
        <p>来自景点门票字段；部分景点可能为经验估算。</p>
      </article>

      <article class="budget-card meal">
        <span class="budget-label">餐饮</span>
        <strong>¥{{ formatMoney(breakdown.meals) }}</strong>
        <p>来自早餐、午餐、晚餐和小吃的预计费用汇总。</p>
      </article>

      <article class="budget-card other">
        <span class="budget-label">其他预估</span>
        <strong>¥{{ formatMoney(breakdown.other) }}</strong>
        <p>通常包含市内交通、零散支出和临时消费。</p>
      </article>
    </div>
  </section>
</template>

<script setup lang="ts">
defineProps<{
  totalBudget: number;
  breakdown: {
    hotel: number;
    tickets: number;
    meals: number;
    other: number;
  };
}>();

function formatMoney(value: number) {
  return Math.round(value);
}
</script>

<style scoped>
.budget-panel {
  background: rgba(255, 255, 255, 0.94);
  padding: 24px;
  border-radius: 26px;
  border: 1px solid rgba(219, 234, 254, 0.9);
  box-shadow: 0 22px 54px rgba(15, 23, 42, 0.08);
  backdrop-filter: blur(12px);
}

.panel-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 20px;
}

.panel-head h3 {
  margin: 0 0 8px;
  font-size: 24px;
  letter-spacing: -0.02em;
}

.panel-head p {
  margin: 0;
  color: #64748b;
  line-height: 1.7;
}

.total-box {
  min-width: 180px;
  padding: 16px 18px;
  border-radius: 18px;
  background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
  color: #1d4ed8;
  border: 1px solid rgba(191, 219, 254, 0.92);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.7);
}

.total-label {
  display: block;
  margin-bottom: 6px;
  font-size: 12px;
  color: #475569;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.total-box strong {
  font-size: 30px;
  letter-spacing: -0.03em;
}

.budget-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
}

.budget-card {
  padding: 18px;
  border-radius: 20px;
  border: 1px solid rgba(226, 232, 240, 0.92);
  box-shadow: 0 12px 24px rgba(15, 23, 42, 0.04);
}

.budget-card strong {
  display: block;
  margin: 8px 0;
  font-size: 28px;
  letter-spacing: -0.03em;
}

.budget-card p {
  margin: 0;
  color: #64748b;
  line-height: 1.6;
}

.budget-label {
  font-size: 13px;
  font-weight: 700;
  color: #334155;
  letter-spacing: 0.02em;
}

.hotel {
  background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
}

.ticket {
  background: linear-gradient(180deg, #fffaf4 0%, #fff7ed 100%);
}

.meal {
  background: linear-gradient(180deg, #fffef3 0%, #fefce8 100%);
}

.other {
  background: linear-gradient(180deg, #f7fff9 0%, #f0fdf4 100%);
}

@media (max-width: 860px) {
  .panel-head {
    flex-direction: column;
  }

  .budget-grid {
    grid-template-columns: 1fr;
  }

  .budget-panel {
    padding: 20px;
    border-radius: 22px;
  }
}
</style>
