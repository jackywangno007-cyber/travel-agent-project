<template>
  <div class="map-card">
    <div class="map-header">
      <div>
        <h3>景点地图</h3>
        <p>地图会根据每天景点顺序绘制轻量路线。点击某一天可高亮当天路线，点击景点卡片可定位到对应站点。</p>
      </div>

      <button
        v-if="activeDay !== null"
        type="button"
        class="reset-button"
        @click="$emit('clear-active-day')"
      >
        查看全部
      </button>
    </div>

    <p v-if="activeDay !== null" class="map-tip">当前高亮：Day {{ activeDay }} 路线</p>
    <p v-if="errorMessage" class="map-error">{{ errorMessage }}</p>
    <div v-else ref="mapRef" class="map-container"></div>
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from "vue";

import type { MapAttractionPoint } from "../types";

const props = defineProps<{
  points: MapAttractionPoint[];
  activeDay: number | null;
  focusedPointKey: string | null;
}>();

defineEmits<{
  (event: "clear-active-day"): void;
}>();

type AMapLngLat = [number, number];

interface AMapMarker {
  on: (event: string, handler: () => void) => void;
  setMap: (map: AMapMap | null) => void;
  setzIndex: (value: number) => void;
  setContent: (content: string) => void;
  getPosition: () => { lng: number; lat: number };
}

interface AMapPolyline {
  setMap: (map: AMapMap | null) => void;
  setOptions: (options: {
    strokeColor?: string;
    strokeWeight?: number;
    strokeOpacity?: number;
    strokeStyle?: "solid" | "dashed";
    zIndex?: number;
  }) => void;
}

interface AMapInfoWindow {
  open: (map: AMapMap, position: AMapLngLat) => void;
}

interface AMapTileLayer {
  setMap: (map: AMapMap) => void;
}

interface AMapMap {
  add: (items: Array<AMapMarker | AMapPolyline>) => void;
  clearMap: () => void;
  setFitView: (items?: Array<AMapMarker | AMapPolyline>) => void;
  setCenter: (center: AMapLngLat) => void;
  destroy: () => void;
}

interface AMapConstructor {
  Map: new (
    element: HTMLElement,
    options: {
      zoom: number;
      center: AMapLngLat;
      resizeEnable?: boolean;
      viewMode?: "2D" | "3D";
    }
  ) => AMapMap;
  Marker: new (options: {
    position: AMapLngLat;
    title: string;
    content?: string;
    offset?: [number, number];
  }) => AMapMarker;
  Polyline: new (options: {
    path: AMapLngLat[];
    strokeColor?: string;
    strokeWeight?: number;
    strokeOpacity?: number;
    strokeStyle?: "solid" | "dashed";
    lineJoin?: string;
    lineCap?: string;
    zIndex?: number;
  }) => AMapPolyline;
  InfoWindow: new (options: { content: string; offset?: [number, number] }) => AMapInfoWindow;
  TileLayer: new () => AMapTileLayer;
}

declare global {
  interface Window {
    AMap?: AMapConstructor;
    _AMapSecurityConfig?: {
      securityJsCode?: string;
    };
  }
}

const mapRef = ref<HTMLElement | null>(null);
const errorMessage = ref("");

const DAY_COLORS = ["#1677ff", "#ef4444", "#22c55e", "#f59e0b", "#8b5cf6", "#06b6d4"];

let mapInstance: AMapMap | null = null;
let scriptLoadingPromise: Promise<AMapConstructor> | null = null;
let amapConstructor: AMapConstructor | null = null;
let markerEntries: Array<{ marker: AMapMarker; point: MapAttractionPoint }> = [];
let polylineEntries: Array<{ day: number; polyline: AMapPolyline }> = [];

function dayColor(day: number) {
  return DAY_COLORS[(day - 1) % DAY_COLORS.length];
}

function escapeHtml(value: string) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function buildMarkerContent(point: MapAttractionPoint, isActive: boolean, isFocused: boolean) {
  const color = dayColor(point.day);
  const scale = isFocused ? 1.08 : isActive ? 1 : 0.9;
  const opacity = isFocused ? 1 : isActive ? 1 : 0.3;
  return `
    <div style="
      display:flex;
      flex-direction:column;
      align-items:center;
      transform:scale(${scale});
      transform-origin:center bottom;
      opacity:${opacity};
      transition:transform 0.18s ease, opacity 0.18s ease;
    ">
      <div style="
        min-width:52px;
        height:28px;
        padding:0 10px;
        border-radius:999px;
        background:${color};
        color:#fff;
        font-size:12px;
        font-weight:700;
        display:flex;
        align-items:center;
        justify-content:center;
        box-shadow:${isFocused ? "0 10px 22px rgba(0,0,0,0.22)" : "0 6px 14px rgba(0,0,0,0.18)"};
        border:2px solid #fff;
      ">${escapeHtml(point.sequenceLabel ?? ("第" + point.orderInDay + "站"))}</div>
      <div style="
        width:0;
        height:0;
        border-left:7px solid transparent;
        border-right:7px solid transparent;
        border-top:12px solid ${color};
        margin-top:-1px;
      "></div>
    </div>
  `;
}

function buildInfoContent(point: MapAttractionPoint) {
  return `
    <div style="padding:8px 10px; max-width:280px; line-height:1.6;">
      <div style="font-size:15px; font-weight:700; margin-bottom:4px;">
        ${escapeHtml(point.name)}
      </div>
      <div style="color:#4b5563; margin-bottom:4px;">
        Day ${point.day} | ${escapeHtml(point.date)} | ${escapeHtml(point.sequenceLabel ?? ("第" + point.orderInDay + "站"))}
      </div>
      <div style="color:#111827;">${escapeHtml(point.address)}</div>
    </div>
  `;
}

function loadAmap(): Promise<AMapConstructor> {
  if (window.AMap) {
    return Promise.resolve(window.AMap);
  }

  if (scriptLoadingPromise) {
    return scriptLoadingPromise;
  }

  const apiKey = import.meta.env.VITE_AMAP_API_KEY;
  if (!apiKey) {
    return Promise.reject(new Error("缺少 VITE_AMAP_API_KEY，暂时无法加载地图。"));
  }

  const securityJsCode = import.meta.env.VITE_AMAP_SECURITY_JS_CODE;
  if (securityJsCode) {
    window._AMapSecurityConfig = { securityJsCode };
  }

  scriptLoadingPromise = new Promise((resolve, reject) => {
    const existingScript = document.querySelector<HTMLScriptElement>(
      'script[data-amap-loader="true"]'
    );

    if (existingScript) {
      existingScript.addEventListener("load", () => {
        if (window.AMap) {
          resolve(window.AMap);
        } else {
          reject(new Error("高德地图脚本已加载，但 AMap 不可用。"));
        }
      });
      existingScript.addEventListener("error", () => {
        reject(new Error("高德地图脚本加载失败。"));
      });
      return;
    }

    const script = document.createElement("script");
    script.src = `https://webapi.amap.com/maps?v=2.0&key=${apiKey}`;
    script.async = true;
    script.defer = true;
    script.dataset.amapLoader = "true";
    script.onload = () => {
      if (window.AMap) {
        resolve(window.AMap);
      } else {
        reject(new Error("高德地图脚本已加载，但 AMap 不可用。"));
      }
    };
    script.onerror = () => reject(new Error("高德地图脚本加载失败。"));
    document.head.appendChild(script);
  });

  return scriptLoadingPromise;
}

function createMarker(AMap: AMapConstructor, point: MapAttractionPoint) {
  const position: AMapLngLat = [point.location.longitude, point.location.latitude];
  const marker = new AMap.Marker({
    position,
    title: point.name,
    content: buildMarkerContent(point, true, false),
    offset: [-26, -40],
  });

  const infoWindow = new AMap.InfoWindow({
    content: buildInfoContent(point),
    offset: [0, -10],
  });

  marker.on("click", () => {
    infoWindow.open(mapInstance as AMapMap, position);
  });

  return marker;
}

function renderPolylines(AMap: AMapConstructor) {
  if (!mapInstance) {
    return;
  }

  polylineEntries = [];
  const grouped = new Map<number, MapAttractionPoint[]>();

  props.points.forEach((point) => {
    const points = grouped.get(point.day) ?? [];
    points.push(point);
    grouped.set(point.day, points);
  });

  grouped.forEach((points, day) => {
    const ordered = [...points].sort((a, b) => a.orderInDay - b.orderInDay);
    if (ordered.length < 2) {
      return;
    }

    const path = ordered.map(
      (point) => [point.location.longitude, point.location.latitude] as AMapLngLat
    );

    const polyline = new AMap.Polyline({
      path,
      strokeColor: dayColor(day),
      strokeWeight: 5,
      strokeOpacity: 0.42,
      strokeStyle: "solid",
      lineJoin: "round",
      lineCap: "round",
      zIndex: 70,
    });

    polylineEntries.push({ day, polyline });
  });

  if (polylineEntries.length > 0) {
    mapInstance.add(polylineEntries.map((entry) => entry.polyline));
  }
}

function applyHighlight() {
  if (!mapInstance || markerEntries.length === 0) {
    return;
  }

  const activeMarkers =
    props.activeDay === null
      ? markerEntries.map((entry) => entry.marker)
      : markerEntries
          .filter((entry) => entry.point.day === props.activeDay)
          .map((entry) => entry.marker);

  markerEntries.forEach((entry) => {
    const isActive = props.activeDay === null || entry.point.day === props.activeDay;
    const isFocused = props.focusedPointKey === `${entry.point.day}-${entry.point.orderInDay}`;
    entry.marker.setContent(buildMarkerContent(entry.point, isActive, isFocused));
    entry.marker.setzIndex(isFocused ? 160 : isActive ? 120 : 90);
  });

  polylineEntries.forEach((entry) => {
    const isActive = props.activeDay === null || entry.day === props.activeDay;
    entry.polyline.setOptions({
      strokeColor: dayColor(entry.day),
      strokeWeight: isActive ? 6 : 4,
      strokeOpacity: isActive ? 0.85 : 0.18,
      zIndex: isActive ? 110 : 60,
    });
  });

  const activeOverlays =
    activeMarkers.length > 0
      ? [
          ...activeMarkers,
          ...polylineEntries
            .filter((entry) => props.activeDay === null || entry.day === props.activeDay)
            .map((entry) => entry.polyline),
        ]
      : [
          ...markerEntries.map((entry) => entry.marker),
          ...polylineEntries.map((entry) => entry.polyline),
        ];

  if (activeOverlays.length > 0) {
    mapInstance.setFitView(activeOverlays);
  }

  if (props.focusedPointKey) {
    const focused = markerEntries.find(
      (entry) => `${entry.point.day}-${entry.point.orderInDay}` === props.focusedPointKey
    );
    if (focused) {
      const position = focused.marker.getPosition();
      mapInstance.setCenter([position.lng, position.lat]);
      focused.marker.setzIndex(180);
    }
  }
}

function renderMarkers(AMap: AMapConstructor) {
  if (!mapInstance) {
    return;
  }

  mapInstance.clearMap();
  markerEntries = props.points.map((point) => ({
    point,
    marker: createMarker(AMap, point),
  }));
  renderPolylines(AMap);

  const overlays = [
    ...markerEntries.map((entry) => entry.marker),
    ...polylineEntries.map((entry) => entry.polyline),
  ];

  if (overlays.length > 0) {
    mapInstance.add(overlays);
    mapInstance.setFitView(overlays);
    applyHighlight();
  }
}

async function initMap() {
  errorMessage.value = "";

  if (!mapRef.value) {
    return;
  }

  try {
    const AMap = await loadAmap();
    amapConstructor = AMap;
    const firstPoint = props.points[0];

    if (!firstPoint) {
      errorMessage.value = "当前没有可展示的景点坐标。";
      return;
    }

    const center: AMapLngLat = [firstPoint.location.longitude, firstPoint.location.latitude];

    if (!mapInstance) {
      mapInstance = new AMap.Map(mapRef.value, {
        zoom: 11,
        center,
        resizeEnable: true,
        viewMode: "2D",
      });

      const tileLayer = new AMap.TileLayer();
      tileLayer.setMap(mapInstance);
    } else {
      mapInstance.setCenter(center);
    }

    renderMarkers(AMap);
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : "地图初始化失败。";
  }
}

watch(
  () => props.points,
  async () => {
    if (mapInstance || props.points.length > 0) {
      await initMap();
    }
  },
  { deep: true }
);

watch(
  () => [props.activeDay, props.focusedPointKey],
  () => {
    if (amapConstructor && markerEntries.length > 0) {
      applyHighlight();
    }
  }
);

onMounted(async () => {
  await initMap();
});

onBeforeUnmount(() => {
  mapInstance?.destroy();
  mapInstance = null;
  amapConstructor = null;
  markerEntries = [];
  polylineEntries = [];
});
</script>

<style scoped>
.map-card {
  background: rgba(255, 255, 255, 0.94);
  padding: 22px;
  border-radius: 24px;
  margin-bottom: 24px;
  border: 1px solid rgba(219, 234, 254, 0.92);
  box-shadow: 0 22px 54px rgba(15, 23, 42, 0.08);
  backdrop-filter: blur(12px);
}

.map-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.map-header h3 {
  margin: 0 0 8px;
  font-size: 24px;
  letter-spacing: -0.02em;
}

.map-header p {
  margin: 0 0 12px;
  color: #64748b;
  line-height: 1.7;
}

.reset-button {
  padding: 10px 14px;
  border: none;
  border-radius: 14px;
  background: linear-gradient(135deg, #1677ff 0%, #1d4ed8 100%);
  color: white;
  cursor: pointer;
  font-weight: 700;
  box-shadow: 0 14px 28px rgba(29, 78, 216, 0.18);
}

.map-tip {
  margin: 0 0 14px;
  color: #1d4ed8;
  font-weight: 600;
  padding: 10px 14px;
  border-radius: 14px;
  background: #eff6ff;
  border: 1px solid rgba(191, 219, 254, 0.92);
}

.map-container {
  width: 100%;
  height: 380px;
  border-radius: 18px;
  overflow: hidden;
  background: linear-gradient(180deg, #eef3f8 0%, #e7eef8 100%);
  border: 1px solid rgba(226, 232, 240, 0.8);
}

.map-error {
  margin: 0;
  color: #d93025;
  padding: 14px 16px;
  border-radius: 16px;
  background: #fef2f2;
  border: 1px solid rgba(254, 202, 202, 0.9);
  line-height: 1.7;
}

@media (max-width: 640px) {
  .map-card {
    padding: 18px;
    border-radius: 20px;
  }

  .map-header {
    flex-direction: column;
  }

  .map-container {
    height: 320px;
  }
}
</style>
