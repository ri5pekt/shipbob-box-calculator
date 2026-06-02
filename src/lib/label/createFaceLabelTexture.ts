import { CanvasTexture, LinearFilter, SRGBColorSpace } from "three";

const PIXELS_PER_INCH = 28;

export interface FaceLabelTextureResult {
  texture: CanvasTexture;
  planeWidth: number;
  planeHeight: number;
}

export interface FaceLabelOptions {
  title: string;
  subtitle: string;
  borderColor: string;
  isShipper: boolean;
  maxPlaneWidth: number;
  maxPlaneHeight: number;
}

function wrapText(ctx: CanvasRenderingContext2D, text: string, maxWidth: number): string[] {
  const words = text.split(" ");
  const lines: string[] = [];
  let line = "";

  for (const word of words) {
    const test = line ? `${line} ${word}` : word;
    if (ctx.measureText(test).width > maxWidth && line) {
      lines.push(line);
      line = word;
    } else {
      line = test;
    }
  }

  if (line) lines.push(line);
  return lines.length ? lines : [text];
}

export function createFaceLabelTexture(options: FaceLabelOptions): FaceLabelTextureResult {
  const {
    title,
    subtitle,
    borderColor,
    isShipper,
    maxPlaneWidth,
    maxPlaneHeight,
  } = options;

  const titleSize = isShipper ? 26 : 22;
  const subSize = isShipper ? 17 : 15;
  const pad = 10;
  const lineGap = 6;

  const canvas = document.createElement("canvas");
  const ctx = canvas.getContext("2d")!;

  const contentWidthIn = maxPlaneWidth * 0.92;
  const maxTextWidthPx = contentWidthIn * PIXELS_PER_INCH - pad * 2;

  ctx.font = `600 ${titleSize}px system-ui, sans-serif`;
  const titleLines = wrapText(ctx, title, maxTextWidthPx);

  const hasSubtitle = subtitle.trim().length > 0;
  let subLines: string[] = [];

  if (hasSubtitle) {
    ctx.font = `400 ${subSize}px system-ui, sans-serif`;
    subLines = wrapText(ctx, subtitle, maxTextWidthPx);
  }

  const titleBlockHeight = titleLines.length * titleSize + (titleLines.length - 1) * lineGap;
  const subBlockHeight = hasSubtitle
    ? subLines.length * subSize + (subLines.length - 1) * 4
    : 0;

  canvas.width = Math.ceil(maxTextWidthPx + pad * 2);
  canvas.height = Math.ceil(
    pad + titleBlockHeight + (hasSubtitle ? 8 + subBlockHeight : 0) + pad,
  );

  ctx.fillStyle = "rgba(10, 12, 18, 0.94)";
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  ctx.strokeStyle = borderColor;
  ctx.lineWidth = 2;
  ctx.strokeRect(1, 1, canvas.width - 2, canvas.height - 2);

  let y = pad;

  ctx.fillStyle = "#f8fafc";
  ctx.font = `600 ${titleSize}px system-ui, sans-serif`;
  ctx.textAlign = "center";
  ctx.textBaseline = "top";

  for (const line of titleLines) {
    ctx.fillText(line, canvas.width / 2, y);
    y += titleSize + lineGap;
  }

  y += 4;

  if (hasSubtitle) {
    ctx.fillStyle = "#cbd5e1";
    ctx.font = `400 ${subSize}px system-ui, sans-serif`;

    for (const line of subLines) {
      ctx.fillText(line, canvas.width / 2, y);
      y += subSize + 4;
    }
  }

  let planeWidth = canvas.width / PIXELS_PER_INCH;
  let planeHeight = canvas.height / PIXELS_PER_INCH;

  const scale = Math.min(1, maxPlaneWidth / planeWidth, maxPlaneHeight / planeHeight);
  planeWidth *= scale;
  planeHeight *= scale;

  const texture = new CanvasTexture(canvas);
  texture.colorSpace = SRGBColorSpace;
  texture.minFilter = LinearFilter;
  texture.magFilter = LinearFilter;
  texture.needsUpdate = true;

  return { texture, planeWidth, planeHeight };
}

export function disposeFaceLabelTexture(texture: CanvasTexture | null | undefined) {
  texture?.dispose();
}
