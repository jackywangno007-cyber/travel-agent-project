<template>
  <div class="page">
    <div class="container">
      <h1>Travel Agent Planner</h1>
      <p class="subtitle">输入旅行需求，生成你的专属行程</p>

      <form class="form" @submit.prevent="handleSubmit">
        <label>
          出发地
          <input v-model="form.origin" type="text" placeholder="例如：西安" required />
        </label>

        <label>
          目的地
          <input v-model="form.destination" type="text" placeholder="例如：北京" required />
        </label>

        <label>
          开始日期
          <input v-model="form.start_date" type="date" required />
        </label>

        <label>
          结束日期
          <input v-model="form.end_date" type="date" required />
        </label>

        <label>
          预算
          <input v-model.number="form.budget" type="number" min="0" placeholder="例如：3000" />
        </label>

        <label>
          偏好（用中文逗号或英文逗号分隔）
          <input
            v-model="preferencesText"
            type="text"
            placeholder="例如：历史，美食，拍照"
          />
        </label>

        <button type="submit" :disabled="loading">
          {{ loading ? "正在生成..." : "生成旅行计划" }}
        </button>
      </form>

      <p v-if="error" class="error">{{ error }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import axios from "axios";
import { reactive, ref } from "vue";
import { useRouter } from "vue-router";

import { createTripPlan } from "../services/api";
import { useEditableTripPlan } from "../stores/trip";
import type { TripPlanRequest } from "../types";

const router = useRouter();
const loading = ref(false);
const error = ref("");
const preferencesText = ref("");

const { setTripPlan } = useEditableTripPlan();

const form = reactive<TripPlanRequest>({
  origin: "",
  destination: "",
  start_date: "",
  end_date: "",
  budget: undefined,
  preferences: [],
});

function validateDates(): string | null {
  if (!form.start_date || !form.end_date) {
    return null;
  }

  if (form.end_date < form.start_date) {
    return "结束日期不能早于开始日期。";
  }

  return null;
}

async function handleSubmit() {
  error.value = "";

  const dateError = validateDates();
  if (dateError) {
    error.value = dateError;
    return;
  }

  loading.value = true;

  try {
    form.preferences = preferencesText.value
      .split(/[，,]/)
      .map((item) => item.trim())
      .filter(Boolean);

    const result = await createTripPlan(form);

    // Store 会负责标准化 meals 并持久化到 sessionStorage。
    setTripPlan(result);
    await router.push("/result");
  } catch (err) {
    console.error(err);

    if (axios.isAxiosError(err)) {
      if (!err.response) {
        error.value = `无法连接后端服务，请确认 backend 正在运行在 127.0.0.1:8000。${
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
  }
}
</script>

<style scoped>
.page {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
}

.container {
  width: 100%;
  max-width: 600px;
  background: white;
  padding: 32px;
  border-radius: 16px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
}

h1 {
  margin-bottom: 8px;
}

.subtitle {
  color: #666;
  margin-bottom: 24px;
}

.form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

label {
  display: flex;
  flex-direction: column;
  font-size: 14px;
  gap: 6px;
}

input {
  padding: 10px 12px;
  border: 1px solid #dcdfe6;
  border-radius: 8px;
  font-size: 14px;
}

button {
  margin-top: 8px;
  padding: 12px;
  border: none;
  border-radius: 10px;
  background: #1677ff;
  color: white;
  font-size: 15px;
  cursor: pointer;
}

button:disabled {
  background: #9bbcff;
  cursor: not-allowed;
}

.error {
  margin-top: 16px;
  color: #d93025;
  white-space: pre-wrap;
}
</style>
