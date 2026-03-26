export interface TripPlanRequest {
  origin: string;
  destination: string;
  start_date: string;
  end_date: string;
  budget?: number;
  preferences: string[];
}

export interface RegenerateDayRequest {
  trip_plan: TripPlanResponse;
  day: number;
  preferences: string[];
  guidance?: string | null;
}

export interface Location {
  longitude: number;
  latitude: number;
}

export interface AttractionInfo {
  name: string;
  address: string;
  location: Location;
  description: string;
  visit_duration: number;
  suggested_duration: string;
  category?: string | null;
  rating?: number | null;
  image_url?: string | null;
  ticket_price?: number | null;
  ticket_price_note?: string | null;
}

export interface MealInfo {
  meal_type: "breakfast" | "lunch" | "dinner" | "snack";
  name: string;
  address: string;
  description: string;
  estimated_cost: number;
  category?: string | null;
  rating?: number | null;
  source: "poi" | "fallback";
}

export interface DayMeals {
  breakfast?: MealInfo | null;
  lunch?: MealInfo | null;
  dinner?: MealInfo | null;
  snack?: MealInfo | null;
}

export interface HotelInfo {
  name: string;
  address: string;
  location: Location;
  price_per_night: number;
  location_summary: string;
  description: string;
  price_note?: string | null;
}

export interface WeatherInfo {
  date: string;
  weather: string;
  temperature: string;
}

export interface TransportationInfo {
  mode: string;
  route_summary: string;
  estimated_travel_time_minutes?: number | null;
  transport_tips: string[];
}

export interface DayPlan {
  day: number;
  date: string;
  theme: string;
  attractions: AttractionInfo[];
  meals?: DayMeals;
  transportation?: TransportationInfo;
  hotel?: HotelInfo;
  weather?: WeatherInfo;
  estimated_cost: number;
}

export interface MapAttractionPoint {
  key: string;
  day: number;
  date: string;
  orderInDay: number;
  name: string;
  address: string;
  location: Location;
  category?: string | null;
}

export interface TripPlanResponse {
  destination: string;
  total_days: number;
  total_budget_estimate: number;
  summary: string;
  daily_plan: DayPlan[];
  generation_source: "llm" | "fallback";
  fallback_reason?: string | null;
}
