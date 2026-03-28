import { computed, ref } from "vue";

import type { AttractionInfo, DayMeals, DayPlan, HotelInfo, MealInfo, TripPlanResponse } from "../types";

type DayOtherBudgetMap = Record<number, number>;

const tripPlan = ref<TripPlanResponse | null>(null);
const dayOtherBudget = ref<DayOtherBudgetMap>({});

function cloneTrip(raw: TripPlanResponse): TripPlanResponse {
  return JSON.parse(JSON.stringify(raw)) as TripPlanResponse;
}

function fallbackMeal(
  mealType: MealInfo["meal_type"],
  destination: string,
  dayIndex: number
): MealInfo {
  const config = {
    breakfast: {
      label: "早餐",
      cost: 18,
      description: `第 ${dayIndex} 天的轻量早餐推荐，适合在上午行程开始前快速用餐。`,
    },
    lunch: {
      label: "午餐",
      cost: 42,
      description: `第 ${dayIndex} 天的午餐兜底安排，优先考虑景点附近便于衔接的餐饮。`,
    },
    dinner: {
      label: "晚餐",
      cost: 58,
      description: `第 ${dayIndex} 天的晚餐推荐，适合作为全天行程结束后的正餐安排。`,
    },
    snack: {
      label: "小吃",
      cost: 22,
      description: `第 ${dayIndex} 天的小吃补充安排，可在下午或晚间灵活调整。`,
    },
  }[mealType];

  return {
    meal_type: mealType,
    name: `${destination}${config.label}推荐`,
    address: `${destination}热门商圈附近`,
    description: config.description,
    estimated_cost: config.cost,
    category: config.label,
    rating: null,
    source: "fallback",
  };
}

function normalizeMeals(
  meals: DayMeals | undefined,
  destination: string,
  dayIndex: number
): DayMeals {
  return {
    breakfast: meals?.breakfast ?? fallbackMeal("breakfast", destination, dayIndex),
    lunch: meals?.lunch ?? fallbackMeal("lunch", destination, dayIndex),
    dinner: meals?.dinner ?? fallbackMeal("dinner", destination, dayIndex),
    snack: meals?.snack ?? fallbackMeal("snack", destination, dayIndex),
  };
}

function normalizeHotel(hotel: DayPlan["hotel"], destination: string): HotelInfo | undefined {
  if (!hotel) {
    return undefined;
  }

  const rawLocation = hotel.location as unknown;
  const location =
    rawLocation && typeof rawLocation === "object" && "longitude" in (rawLocation as object)
      ? (rawLocation as HotelInfo["location"])
      : { longitude: 116.397428, latitude: 39.90923 };

  const legacySummary =
    typeof rawLocation === "string" && rawLocation.trim() ? rawLocation.trim() : undefined;

  return {
    ...hotel,
    address: hotel.address ?? `${destination}核心城区`,
    location,
    location_summary: hotel.location_summary ?? legacySummary ?? `${destination}热门住宿区`,
    description:
      hotel.description ?? `${hotel.name} 可作为 ${destination} 行程中的稳定住宿落点。`,
    price_note: hotel.price_note ?? null,
  };
}

function dayHotelCost(day: DayPlan) {
  return day.hotel?.price_per_night ?? 0;
}

function dayTicketCost(day: DayPlan) {
  return day.attractions.reduce((sum, item) => sum + (item.ticket_price ?? 0), 0);
}

function dayMealCost(meals: DayMeals) {
  return [meals.breakfast, meals.lunch, meals.dinner, meals.snack].reduce(
    (sum, item) => sum + (item?.estimated_cost ?? 0),
    0
  );
}

function buildOtherBudgetMap(plan: TripPlanResponse): DayOtherBudgetMap {
  const result: DayOtherBudgetMap = {};

  for (const day of plan.daily_plan) {
    const normalizedMeals = normalizeMeals(day.meals, plan.destination, day.day);
    result[day.day] = Math.max(
      day.estimated_cost - dayHotelCost(day) - dayTicketCost(day) - dayMealCost(normalizedMeals),
      0
    );
  }

  return result;
}

function normalizeTripPlan(raw: TripPlanResponse): TripPlanResponse {
  const plan = cloneTrip(raw);

  plan.daily_plan = plan.daily_plan.map((day) => ({
    ...day,
    meals: normalizeMeals(day.meals, plan.destination, day.day),
    hotel: normalizeHotel(day.hotel, plan.destination),
  }));

  return plan;
}

function recalculateBudgets() {
  if (!tripPlan.value) {
    return;
  }

  let totalBudget = 0;

  for (const day of tripPlan.value.daily_plan) {
    day.meals = normalizeMeals(day.meals, tripPlan.value.destination, day.day);
    const hotel = dayHotelCost(day);
    const tickets = dayTicketCost(day);
    const meals = dayMealCost(day.meals);
    const other = dayOtherBudget.value[day.day] ?? 0;
    day.estimated_cost = hotel + tickets + meals + other;
    totalBudget += day.estimated_cost;
  }

  tripPlan.value.total_budget_estimate = totalBudget;
}

function persist() {
  if (!tripPlan.value) {
    sessionStorage.removeItem("trip_result");
    return;
  }

  sessionStorage.setItem("trip_result", JSON.stringify(tripPlan.value));
}

function findDay(dayNumber: number) {
  return tripPlan.value?.daily_plan.find((item) => item.day === dayNumber) ?? null;
}

function swapAttractions(items: AttractionInfo[], fromIndex: number, toIndex: number) {
  const next = [...items];
  const [moved] = next.splice(fromIndex, 1);
  next.splice(toIndex, 0, moved);
  return next;
}

export function useEditableTripPlan() {
  function setTripPlan(nextPlan: TripPlanResponse) {
    const plan = normalizeTripPlan(nextPlan);
    tripPlan.value = plan;
    dayOtherBudget.value = buildOtherBudgetMap(plan);
    recalculateBudgets();
    persist();
  }

  function loadFromSessionStorage() {
    try {
      const raw = sessionStorage.getItem("trip_result");
      if (!raw) {
        tripPlan.value = null;
        dayOtherBudget.value = {};
        return;
      }

      const parsed = JSON.parse(raw) as TripPlanResponse;
      const plan = normalizeTripPlan(parsed);
      tripPlan.value = plan;
      dayOtherBudget.value = buildOtherBudgetMap(plan);
      recalculateBudgets();
      persist();
    } catch (error) {
      console.error("[trip_store] failed to load trip_result", error);
      tripPlan.value = null;
      dayOtherBudget.value = {};
    }
  }

  function deleteAttraction(dayNumber: number, attractionIndex: number) {
    const day = findDay(dayNumber);
    if (!day) {
      return;
    }

    day.attractions = day.attractions.filter((_, index) => index !== attractionIndex);
    recalculateBudgets();
    persist();
  }

  function moveAttraction(dayNumber: number, attractionIndex: number, direction: "up" | "down") {
    const day = findDay(dayNumber);
    if (!day) {
      return;
    }

    const targetIndex = direction === "up" ? attractionIndex - 1 : attractionIndex + 1;
    if (targetIndex < 0 || targetIndex >= day.attractions.length) {
      return;
    }

    day.attractions = swapAttractions(day.attractions, attractionIndex, targetIndex);
    recalculateBudgets();
    persist();
  }

  function replaceDayPlan(nextDay: DayPlan) {
    if (!tripPlan.value) {
      return;
    }

    const index = tripPlan.value.daily_plan.findIndex((item) => item.day === nextDay.day);
    if (index === -1) {
      return;
    }

    const normalizedDay: DayPlan = {
      ...nextDay,
      meals: normalizeMeals(nextDay.meals, tripPlan.value.destination, nextDay.day),
    };

    tripPlan.value.daily_plan.splice(index, 1, normalizedDay);
    dayOtherBudget.value[nextDay.day] = Math.max(
      normalizedDay.estimated_cost -
        dayHotelCost(normalizedDay) -
        dayTicketCost(normalizedDay) -
        dayMealCost(normalizedDay.meals!),
      0
    );
    recalculateBudgets();
    persist();
  }

  function getDayPlan(dayNumber: number) {
    return findDay(dayNumber);
  }

  const totalAttractions = computed(() =>
    tripPlan.value?.daily_plan.reduce((sum, day) => sum + day.attractions.length, 0) ?? 0
  );

  return {
    tripPlan,
    totalAttractions,
    dayOtherBudget,
    setTripPlan,
    loadFromSessionStorage,
    deleteAttraction,
    moveAttraction,
    replaceDayPlan,
    getDayPlan,
  };
}
