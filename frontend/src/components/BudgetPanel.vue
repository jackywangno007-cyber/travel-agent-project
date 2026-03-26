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
  background: white;
  padding: 20px;
  border-radius: 18px;
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.08);
}

.panel-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 18px;
}

.panel-head h3 {
  margin: 0 0 8px;
}

.panel-head p {
  margin: 0;
  color: #64748b;
  line-height: 1.7;
}

.total-box {
  min-width: 180px;
  padding: 14px 16px;
  border-radius: 14px;
  background: linear-gradient(135deg, #eff6ff, #dbeafe);
  color: #1d4ed8;
}

.total-label {
  display: block;
  margin-bottom: 6px;
  font-size: 12px;
  color: #475569;
}

.budget-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
}

.budget-card {
  padding: 16px;
  border-radius: 16px;
  border: 1px solid #e5e7eb;
}

.budget-card strong {
  display: block;
  margin: 8px 0;
  font-size: 24px;
}

.budget-card p {
  margin: 0;
  color: #64748b;
  line-height: 1.6;
}

.budget-label {
  font-size: 13px;
  font-weight: 600;
  color: #334155;
}

.hotel {
  background: #f8fafc;
}

.ticket {
  background: #fff7ed;
}

.meal {
  background: #fefce8;
}

.other {
  background: #f0fdf4;
}

@media (max-width: 860px) {
  .panel-head {
    flex-direction: column;
  }

  .budget-grid {
    grid-template-columns: 1fr;
  }
}
</style>
