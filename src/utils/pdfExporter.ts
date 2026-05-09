/**
 * PDF 导出工具模块。
 *
 * 使用 html2canvas + jsPDF 将科技树可视化为 PDF 文件。
 * 支持两种导出模式：
 * - exportViewport：导出当前视口截图
 * - exportFullView：导出全景（完整科技树），自动分页
 *
 * @module pdfExporter
 */

import html2canvas from 'html2canvas';
import { jsPDF } from 'jspdf';

/** A4 页面尺寸（毫米） */
const A4_WIDTH_MM = 210;
const A4_HEIGHT_MM = 297;

/** PDF 页边距（毫米） */
const PAGE_MARGIN_MM = 10;

/** 导出可用区域宽度（毫米） */
const CONTENT_WIDTH_MM = A4_WIDTH_MM - PAGE_MARGIN_MM * 2;

/** 导出可用区域高度（毫米） */
const CONTENT_HEIGHT_MM = A4_HEIGHT_MM - PAGE_MARGIN_MM * 2;

/** 截图缩放比例（提高清晰度） */
const CAPTURE_SCALE = 2;

/** 截图背景色 */
const BACKGROUND_COLOR = '#1a1a2e';

/**
 * 从源 canvas 中裁切指定区域，生成新的 canvas。
 *
 * @param source - 源 canvas
 * @param startX - 裁切起始 X（像素）
 * @param startY - 裁切起始 Y（像素）
 * @param width - 裁切宽度（像素）
 * @param height - 裁切高度（像素）
 * @returns 裁切后的新 canvas
 */
function sliceCanvas(
  source: HTMLCanvasElement,
  startX: number,
  startY: number,
  width: number,
  height: number,
): HTMLCanvasElement {
  const sliced = document.createElement('canvas');
  sliced.width = width;
  sliced.height = height;
  const ctx = sliced.getContext('2d');
  if (ctx) {
    ctx.drawImage(source, startX, startY, width, height, 0, 0, width, height);
  }
  return sliced;
}

/**
 * 导出当前视口截图为 PDF。
 *
 * 对传入的 DOM 元素进行截图，生成单页 A4 PDF 文件并触发下载。
 *
 * @param element - 要截图的 DOM 元素（通常是科技树容器）
 * @param fileName - 导出文件名（不含扩展名），默认 "tech-tree-viewport"
 */
export async function exportViewport(
  element: HTMLElement,
  fileName: string = 'tech-tree-viewport',
): Promise<void> {
  const canvas = await html2canvas(element, {
    scale: CAPTURE_SCALE,
    backgroundColor: BACKGROUND_COLOR,
    useCORS: true,
    logging: false,
  });

  const pdf = new jsPDF({
    orientation: 'portrait',
    unit: 'mm',
    format: 'a4',
  });

  addImageFitToPage(pdf, canvas);
  pdf.save(`${fileName}.pdf`);
}

/**
 * 导出全景（完整科技树）为 PDF。
 *
 * 会先临时调整容器样式以显示完整内容，截图后恢复。
 * 如果截图高度超过一页，自动分页处理。
 *
 * @param element - 要截图的 DOM 元素（通常是科技树容器）
 * @param fileName - 导出文件名（不含扩展名），默认 "tech-tree-full"
 */
export async function exportFullView(
  element: HTMLElement,
  fileName: string = 'tech-tree-full',
): Promise<void> {
  // 保存原始样式，以便恢复
  const originalOverflow = element.style.overflow;
  const originalWidth = element.style.width;
  const originalHeight = element.style.height;

  try {
    // 临时展开容器以捕获完整内容
    element.style.overflow = 'visible';
    const scrollWidth = element.scrollWidth;
    const scrollHeight = element.scrollHeight;
    element.style.width = `${scrollWidth}px`;
    element.style.height = `${scrollHeight}px`;

    const canvas = await html2canvas(element, {
      scale: CAPTURE_SCALE,
      backgroundColor: BACKGROUND_COLOR,
      useCORS: true,
      logging: false,
      width: scrollWidth,
      height: scrollHeight,
    });

    const pdf = new jsPDF({
      orientation: 'portrait',
      unit: 'mm',
      format: 'a4',
    });

    addImageMultiPage(pdf, canvas);
    pdf.save(`${fileName}.pdf`);
  } finally {
    // 恢复原始样式
    element.style.overflow = originalOverflow;
    element.style.width = originalWidth;
    element.style.height = originalHeight;
  }
}

/**
 * 将 canvas 图片适配添加到 PDF 单页中（居中显示）。
 *
 * @param pdf - jsPDF 实例
 * @param canvas - 截图 canvas
 */
function addImageFitToPage(pdf: jsPDF, canvas: HTMLCanvasElement): void {
  const imgData = canvas.toDataURL('image/png');
  const imgWidthPx = canvas.width;
  const imgHeightPx = canvas.height;

  // 计算按宽度适配时的高度
  const fitWidthMm = CONTENT_WIDTH_MM;
  const fitHeightMm = (imgHeightPx / imgWidthPx) * fitWidthMm;

  // 如果高度超出，则按高度适配
  if (fitHeightMm > CONTENT_HEIGHT_MM) {
    const actualHeightMm = CONTENT_HEIGHT_MM;
    const actualWidthMm = (imgWidthPx / imgHeightPx) * actualHeightMm;
    const offsetX = PAGE_MARGIN_MM + (CONTENT_WIDTH_MM - actualWidthMm) / 2;
    const offsetY = PAGE_MARGIN_MM;
    pdf.addImage(imgData, 'PNG', offsetX, offsetY, actualWidthMm, actualHeightMm);
  } else {
    const offsetX = PAGE_MARGIN_MM;
    const offsetY = PAGE_MARGIN_MM + (CONTENT_HEIGHT_MM - fitHeightMm) / 2;
    pdf.addImage(imgData, 'PNG', offsetX, offsetY, fitWidthMm, fitHeightMm);
  }
}

/**
 * 将 canvas 图片分页添加到 PDF 中。
 *
 * 当图片高度超过一页时，通过 canvas 切片实现分页。
 *
 * @param pdf - jsPDF 实例
 * @param canvas - 截图 canvas
 */
function addImageMultiPage(pdf: jsPDF, canvas: HTMLCanvasElement): void {
  const imgWidthPx = canvas.width;
  const imgHeightPx = canvas.height;

  // 按 A4 宽度适配，计算总高度（毫米）
  const totalHeightMm = (imgHeightPx / imgWidthPx) * CONTENT_WIDTH_MM;

  if (totalHeightMm <= CONTENT_HEIGHT_MM) {
    // 单页即可容纳
    addImageFitToPage(pdf, canvas);
    return;
  }

  // 计算每页对应的像素高度
  const pxPerMm = imgHeightPx / totalHeightMm;
  const pageHeightPx = Math.floor(CONTENT_HEIGHT_MM * pxPerMm);
  const totalPages = Math.ceil(imgHeightPx / pageHeightPx);

  for (let page = 0; page < totalPages; page++) {
    if (page > 0) {
      pdf.addPage();
    }

    const startY = page * pageHeightPx;
    const sliceH = Math.min(pageHeightPx, imgHeightPx - startY);

    const slicedCanvas = sliceCanvas(canvas, 0, startY, imgWidthPx, sliceH);
    const sliceData = slicedCanvas.toDataURL('image/png');

    // 计算该切片在 PDF 中的实际高度
    const sliceHeightMm = (sliceH / imgWidthPx) * CONTENT_WIDTH_MM;
    pdf.addImage(
      sliceData,
      'PNG',
      PAGE_MARGIN_MM,
      PAGE_MARGIN_MM,
      CONTENT_WIDTH_MM,
      sliceHeightMm,
    );
  }
}
