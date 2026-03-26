import axios from "axios";
import type { AxiosError } from "axios";

import type { DayPlan, RegenerateDayRequest, TripPlanRequest, TripPlanResponse } from "../types";

const requestTargets = [
  "http://127.0.0.1:8000",
  "http://localhost:8000",
];

function createClient(baseURL: string) {
  return axios.create({
    baseURL,
    timeout: 60000,
  });
}

function isNetworkError(error: unknown): error is AxiosError {
  return axios.isAxiosError(error) && !error.response;
}

export async function createTripPlan(
  payload: TripPlanRequest
): Promise<TripPlanResponse> {
  let lastError: unknown;

  for (const baseURL of requestTargets) {
    try {
      const client = createClient(baseURL);
      const response = await client.post<TripPlanResponse>("/api/trip/plan", payload);
      return response.data;
    } catch (error) {
      lastError = error;
      if (!isNetworkError(error)) {
        throw error;
      }
    }
  }

  throw lastError;
}

export async function regenerateTripDay(
  payload: RegenerateDayRequest
): Promise<DayPlan> {
  let lastError: unknown;

  for (const baseURL of requestTargets) {
    try {
      const client = createClient(baseURL);
      const response = await client.post<DayPlan>("/api/trip/regenerate-day", payload);
      return response.data;
    } catch (error) {
      lastError = error;
      if (!isNetworkError(error)) {
        throw error;
      }
    }
  }

  throw lastError;
}
