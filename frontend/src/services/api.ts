import axios from "axios";
import type { AxiosError } from "axios";

import type { DayPlan, RegenerateDayRequest, TripPlanRequest, TripPlanResponse } from "../types";

const configuredApiBaseUrl = import.meta.env.VITE_API_BASE_URL?.trim() || "";

function normalizeBaseUrl(value: string) {
  return value.replace(/\/+$/, "");
}

function getRequestTargets() {
  if (configuredApiBaseUrl) {
    return [normalizeBaseUrl(configuredApiBaseUrl)];
  }

  return ["/api"];
}

function createClient(baseURL: string) {
  return axios.create({
    baseURL,
    timeout: 60000,
  });
}

function isNetworkError(error: unknown): error is AxiosError {
  return axios.isAxiosError(error) && !error.response;
}

function wrapDeploymentHint(error: unknown) {
  if (configuredApiBaseUrl || import.meta.env.DEV || !axios.isAxiosError(error)) {
    return error;
  }

  if (error.response?.status === 404 || !error.response) {
    return new Error(
      "当前未配置 VITE_API_BASE_URL。线上部署时请在 Vercel 中配置后端 API 地址；本地开发请通过 Vite 代理访问 /api。"
    );
  }

  return error;
}

export async function createTripPlan(
  payload: TripPlanRequest
): Promise<TripPlanResponse> {
  let lastError: unknown;

  for (const baseURL of getRequestTargets()) {
    try {
      const client = createClient(baseURL);
      const response = await client.post<TripPlanResponse>("/api/trip/plan", payload);
      return response.data;
    } catch (error) {
      lastError = wrapDeploymentHint(error);
      if (!isNetworkError(error)) {
        throw lastError;
      }
    }
  }

  throw lastError;
}

export async function regenerateTripDay(
  payload: RegenerateDayRequest
): Promise<DayPlan> {
  let lastError: unknown;

  for (const baseURL of getRequestTargets()) {
    try {
      const client = createClient(baseURL);
      const response = await client.post<DayPlan>("/api/trip/regenerate-day", payload);
      return response.data;
    } catch (error) {
      lastError = wrapDeploymentHint(error);
      if (!isNetworkError(error)) {
        throw lastError;
      }
    }
  }

  throw lastError;
}
