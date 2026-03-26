<template>
  <div class="map-card">
    <div class="map-header">
      <div>
        <h3>景点地图</h3>
        <p>点击标记查看景点名称、地址和所属天数，点击某一天卡片可高亮当天路线。</p>
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

    <p v-if="activeDay !== null" class="map-tip">当前高亮：Day {{ activeDay }}</p>
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
}

interface AMapInfoWindow {
  open: (map: AMapMap, position: AMapLngLat) => void;
}

interface AMapTileLayer {
  setMap: (map: AMapMap) => void;
}

interface AMapMap {
  add: (markers: AMapMarker[]) => void;
  clearMap: () => void;
  setFitView: (items?: AMapMarker[]) => void;
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

function buildMarkerContent(point: MapAttractionPoint, isActive: boolean) {
  const color = dayColor(point.day);
  const scale = isActive ? 1 : 0.9;
  const opacity = isActive ? 1 : 0.35;
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
        min-width:26px;
        height:26px;
        padding:0 8px;
        border-radius:999px;
        background:${color};
        color:#fff;
        font-size:12px;
        font-weight:700;
        display:flex;
        align-items:center;
        justify-content:center;
        box-shadow:0 6px 14px rgba(0,0,0,0.18);
        border:2px solid #fff;
      ">D${point.day}-${point.orderInDay}</div>
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
    <div style="padding:8px 10px; max-width:260px; line-height:1.6;">
      <div style="font-size:15px; font-weight:700; margin-bottom:4px;">
        ${escapeHtml(point.name)}
      </div>
      <div style="color:#4b5563; margin-bottom:4px;">Day ${point.day} | ${escapeHtml(point.date)}</div>
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
    content: buildMarkerContent(point, true),
    offset: [-16, -38],
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
    entry.marker.setContent(buildMarkerContent(entry.point, isActive));
    entry.marker.setzIndex(isActive ? 120 : 90);
  });

  if (activeMarkers.length > 0) {
    mapInstance.setFitView(activeMarkers);
  } else {
    mapInstance.setFitView(markerEntries.map((entry) => entry.marker));
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

  const markers = markerEntries.map((entry) => entry.marker);
  if (markers.length > 0) {
    mapInstance.add(markers);
    mapInstance.setFitView(markers);
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
  () => props.activeDay,
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
});
</script>

<style scoped>
.map-card {
  background: white;
  padding: 20px;
  border-radius: 14px;
  margin-bottom: 24px;
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.06);
}

.map-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.map-header h3 {
  margin: 0 0 8px;
}

.map-header p {
  margin: 0 0 12px;
  color: #666;
}

.reset-button {
  padding: 8px 12px;
  border: none;
  border-radius: 10px;
  background: #1677ff;
  color: white;
  cursor: pointer;
}

.map-tip {
  margin: 0 0 12px;
  color: #1d4ed8;
  font-weight: 600;
}

.map-container {
  width: 100%;
  height: 360px;
  border-radius: 12px;
  overflow: hidden;
  background: #eef3f8;
}

.map-error {
  margin: 0;
  color: #d93025;
}

@media (max-width: 640px) {
  .map-header {
    flex-direction: column;
  }
}
</style>
