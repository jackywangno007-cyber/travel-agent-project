<template>
  <div class="export-actions">
    <button type="button" :disabled="isExporting" @click="exportAsPng">
      {{ isExporting ? "导出中..." : "导出图片" }}
    </button>
    <button type="button" :disabled="isExporting" @click="exportAsPdf">
      {{ isExporting ? "导出中..." : "导出 PDF" }}
    </button>
    <p v-if="feedback" class="feedback" :class="{ error: feedbackType === 'error' }">
      {{ feedback }}
    </p>
  </div>
</template>

<script setup lang="ts">
import html2canvas from "html2canvas";
import jsPDF from "jspdf";
import { ref } from "vue";

const props = defineProps<{
  targetId: string;
  fileBaseName: string;
}>();

const isExporting = ref(false);
const feedback = ref("");
const feedbackType = ref<"success" | "error">("success");

function setFeedback(message: string, type: "success" | "error") {
  feedback.value = message;
  feedbackType.value = type;
}

function getTargetElement() {
  return document.getElementById(props.targetId);
}

function buildFileName(extension: string) {
  const safeName = props.fileBaseName.trim().replace(/\s+/g, "-") || "trip-plan";
  return `${safeName}.${extension}`;
}

function injectExportStyles(clonedDocument: Document) {
  const style = clonedDocument.createElement("style");
  style.textContent = `
    #${props.targetId} {
      width: 1120px !important;
      max-width: none !important;
      margin: 0 auto !important;
      overflow: visible !important;
    }

    #${props.targetId} .hero-grid,
    #${props.targetId} .overview-grid,
    #${props.targetId} .content-grid,
    #${props.targetId} .field-grid {
      grid-template-columns: 1fr !important;
    }

    #${props.targetId} .summary-top,
    #${props.targetId} .budget-grid,
    #${props.targetId} .mini-budget {
      grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
    }

    #${props.targetId} .section,
    #${props.targetId} .info-card,
    #${props.targetId} .attraction-card,
    #${props.targetId} .meal-item,
    #${props.targetId} .day-card,
    #${props.targetId} .day-anchor-section,
    #${props.targetId} .summary-card {
      break-inside: avoid !important;
      page-break-inside: avoid !important;
    }

    #${props.targetId} .side-section,
    #${props.targetId} .side-stack,
    #${props.targetId} .meal-list,
    #${props.targetId} .attraction-list,
    #${props.targetId} .day-list,
    #${props.targetId} .export-content {
      overflow: visible !important;
    }

    #${props.targetId} .day-head,
    #${props.targetId} .section-head,
    #${props.targetId} .attraction-head,
    #${props.targetId} .meal-head {
      align-items: flex-start !important;
    }

    #${props.targetId} .anchor-nav,
    #${props.targetId} .back-to-top,
    #${props.targetId} .header-actions > button,
    #${props.targetId} .day-action,
    #${props.targetId} .action-group {
      display: none !important;
    }

    #${props.targetId} .export-only {
      display: block !important;
      margin-top: 16px !important;
    }

    #${props.targetId} .screen-meals-card,
    #${props.targetId} .attraction-image {
      display: none !important;
    }

    #${props.targetId} .image-shell {
      height: 72px !important;
      background: linear-gradient(135deg, #dbeafe 0%, #f8fafc 100%) !important;
    }

    #${props.targetId} .image-placeholder {
      display: flex !important;
      align-items: center !important;
      justify-content: center !important;
      color: #1d4ed8 !important;
      background: transparent !important;
    }
  `;
  clonedDocument.head.appendChild(style);
}

function replaceMapForExport(clonedDocument: Document) {
  const exportMapBlocks = clonedDocument.querySelectorAll("[data-export-map]");

  exportMapBlocks.forEach((block) => {
    const element = block as HTMLElement;
    element.innerHTML = `
      <div style="
        border: 1px dashed #cbd5e1;
        border-radius: 16px;
        padding: 20px;
        background: #f8fafc;
        color: #334155;
        line-height: 1.7;
      ">
        <strong style="display:block; margin-bottom:8px;">景点地图</strong>
        为了保证图片和 PDF 导出的稳定性，导出版本暂时使用文字占位，
        不直接渲染高德地图。页面中的交互地图不受影响。
      </div>
    `;
  });
}

async function renderCanvas() {
  const target = getTargetElement();
  if (!target) {
    throw new Error("未找到可导出的行程内容区域。");
  }

  return html2canvas(target, {
    backgroundColor: "#ffffff",
    scale: 1.6,
    useCORS: false,
    logging: false,
    windowWidth: Math.max(target.scrollWidth, 1280),
    windowHeight: Math.max(target.scrollHeight, 1800),
    onclone: (clonedDocument) => {
      injectExportStyles(clonedDocument);
      replaceMapForExport(clonedDocument);
    },
  });
}

function downloadDataUrl(dataUrl: string, fileName: string) {
  const link = document.createElement("a");
  link.href = dataUrl;
  link.download = fileName;
  link.click();
}

function canvasToJpeg(canvas: HTMLCanvasElement, quality = 0.9) {
  return canvas.toDataURL("image/jpeg", quality);
}

function createSliceCanvas(
  sourceCanvas: HTMLCanvasElement,
  startY: number,
  sliceHeight: number
) {
  const sliceCanvas = document.createElement("canvas");
  sliceCanvas.width = sourceCanvas.width;
  sliceCanvas.height = sliceHeight;

  const ctx = sliceCanvas.getContext("2d");
  if (!ctx) {
    throw new Error("无法创建导出画布。");
  }

  ctx.fillStyle = "#ffffff";
  ctx.fillRect(0, 0, sliceCanvas.width, sliceCanvas.height);
  ctx.drawImage(
    sourceCanvas,
    0,
    startY,
    sourceCanvas.width,
    sliceHeight,
    0,
    0,
    sliceCanvas.width,
    sliceCanvas.height
  );

  return sliceCanvas;
}

async function exportAsPng() {
  isExporting.value = true;
  setFeedback("", "success");

  try {
    const canvas = await renderCanvas();
    downloadDataUrl(canvas.toDataURL("image/png"), buildFileName("png"));
    setFeedback("图片导出成功。", "success");
  } catch (error) {
    setFeedback(error instanceof Error ? error.message : "图片导出失败。", "error");
  } finally {
    isExporting.value = false;
  }
}

async function exportAsPdf() {
  isExporting.value = true;
  setFeedback("", "success");

  try {
    const canvas = await renderCanvas();
    const pdf = new jsPDF("p", "mm", "a4");
    const pageWidth = pdf.internal.pageSize.getWidth();
    const pageHeight = pdf.internal.pageSize.getHeight();
    const margin = 8;
    const usableWidth = pageWidth - margin * 2;
    const usableHeight = pageHeight - margin * 2;

    const pxPerMm = canvas.width / usableWidth;
    const sliceHeightPx = Math.floor(usableHeight * pxPerMm);

    let startY = 0;
    let pageIndex = 0;

    while (startY < canvas.height) {
      const currentSliceHeight = Math.min(sliceHeightPx, canvas.height - startY);
      const sliceCanvas = createSliceCanvas(canvas, startY, currentSliceHeight);
      const imageData = canvasToJpeg(sliceCanvas, 0.86);
      const renderedHeight = currentSliceHeight / pxPerMm;

      if (pageIndex > 0) {
        pdf.addPage();
      }

      pdf.addImage(
        imageData,
        "JPEG",
        margin,
        margin,
        usableWidth,
        renderedHeight,
        undefined,
        "FAST"
      );

      startY += currentSliceHeight;
      pageIndex += 1;
    }

    pdf.save(buildFileName("pdf"));
    setFeedback("PDF 导出成功。", "success");
  } catch (error) {
    setFeedback(error instanceof Error ? error.message : "PDF 导出失败。", "error");
  } finally {
    isExporting.value = false;
  }
}
</script>

<style scoped>
.export-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.feedback {
  margin: 0;
  color: #15803d;
  font-size: 13px;
}

.feedback.error {
  color: #dc2626;
}
</style>
