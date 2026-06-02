import {
  CanvasTexture,
  LinearFilter,
  MeshStandardMaterial,
  SRGBColorSpace,
} from "three";

const PX_PER_IN = 72;

/**
 * Creates a canvas texture for the top (+Y) face of a packed item box.
 * The label text is drawn centred; the background uses the item colour.
 */
export function createTopFaceTexture(
  text: string,
  faceW: number,   // Three.js X  (= product.dimensions.length after packing)
  faceH: number,   // Three.js Z  (= product.dimensions.width  after packing)
  color: string,
): CanvasTexture {
  const cw = Math.max(Math.round(faceW * PX_PER_IN), 64);
  const ch = Math.max(Math.round(faceH * PX_PER_IN), 64);

  const canvas = document.createElement("canvas");
  canvas.width  = cw;
  canvas.height = ch;
  const ctx = canvas.getContext("2d")!;

  // Base colour fill (matches box body)
  ctx.fillStyle = color;
  ctx.globalAlpha = 0.78;
  ctx.fillRect(0, 0, cw, ch);
  ctx.globalAlpha = 1;

  // Slightly lighter overlay so text stands out
  ctx.fillStyle = "rgba(255,255,255,0.08)";
  ctx.fillRect(0, 0, cw, ch);

  // Auto-fit font: start at 60% of the shorter dimension, shrink to fit width
  const maxW = cw * 0.88;
  let fontSize = Math.max(8, Math.min(22, Math.floor(ch * 0.55)));
  ctx.font = `600 ${fontSize}px system-ui, sans-serif`;
  while (fontSize > 7 && ctx.measureText(text).width > maxW) {
    fontSize -= 1;
    ctx.font = `600 ${fontSize}px system-ui, sans-serif`;
  }

  // Drop shadow for legibility
  ctx.shadowColor = "rgba(0,0,0,0.7)";
  ctx.shadowBlur  = 3;

  ctx.fillStyle   = "#f8fafc";
  ctx.textAlign   = "center";
  ctx.textBaseline = "middle";
  ctx.fillText(text, cw / 2, ch / 2);

  ctx.shadowBlur = 0;

  const tex = new CanvasTexture(canvas);
  tex.colorSpace = SRGBColorSpace;
  tex.minFilter  = LinearFilter;
  tex.magFilter  = LinearFilter;
  tex.needsUpdate = true;
  return tex;
}

/** Build 6 materials for BoxGeometry (order: +X -X +Y -Y +Z -Z). */
export function buildBoxMaterials(
  color: string,
  dims: { length: number; height: number; width: number },
  text: string,
): MeshStandardMaterial[] {
  const shared = {
    transparent: true,
    roughness: 0.35,
    metalness: 0.05,
  };

  const face = (w: number, h: number) =>
    new MeshStandardMaterial({
      map:     createTopFaceTexture(text, w, h, color),
      color:   "#ffffff",
      ...shared,
      opacity: 0.88,
    });

  // BoxGeometry face indices: 0=+X  1=-X  2=+Y(top)  3=-Y  4=+Z  5=-Z
  // Each face pair uses its own correctly-proportioned canvas texture:
  //   ±X  →  width(Z) × height(Y)
  //   ±Y  →  length(X) × width(Z)
  //   ±Z  →  length(X) × height(Y)
  const px = face(dims.width,  dims.height);  // +X
  const mx = face(dims.width,  dims.height);  // -X
  const py = face(dims.length, dims.width);   // +Y (top)
  const my = face(dims.length, dims.width);   // -Y (bottom)
  const pz = face(dims.length, dims.height);  // +Z (front)
  const mz = face(dims.length, dims.height);  // -Z (back)

  return [px, mx, py, my, pz, mz];
}

export function disposeBoxMaterials(mats: MeshStandardMaterial[]) {
  mats.forEach((m) => {
    m.map?.dispose();
    m.dispose();
  });
}
