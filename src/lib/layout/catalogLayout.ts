import { BOX_CATALOG, PRODUCT_CATALOG } from "../../data/catalog";
import type { Box, Dimensions, Product } from "../../types";
import { displayDimensions, formatDims } from "./displayDimensions";

export type SceneItemKind = "shipper" | "product";

export interface SceneItem {
  id: string;
  kind: SceneItemKind;
  label: string;
  subtitle: string;
  dimensions: Dimensions;
  position: [number, number, number];
}

const GAP = 1.25;
const PRODUCT_ROW_WIDTH = 80;
/** Gap between product grid front edge and shipper table (inches). */
const ZONE_GAP = 8;

function shortLabel(title: string): string {
  return title.replace(/^Particle\s+/i, "");
}

function layoutRow(
  items: Array<{ id: string; kind: SceneItemKind; label: string; subtitle: string; dimensions: Dimensions }>,
  startX: number,
  startZ: number,
  maxRowWidth: number,
): SceneItem[] {
  const placed: SceneItem[] = [];
  let x = startX;
  let z = startZ;
  let rowDepth = 0;

  for (const item of items) {
    const { length: l, width: w, height: h } = item.dimensions;

    if (x > startX && x + l > startX + maxRowWidth) {
      x = startX;
      z += rowDepth + GAP;
      rowDepth = 0;
    }

    placed.push({
      ...item,
      position: [x + l / 2, h / 2, z + w / 2],
    });

    x += l + GAP;
    rowDepth = Math.max(rowDepth, w);
  }

  return placed;
}

function layoutProducts(): { items: SceneItem[]; zone: ReturnType<typeof zoneBounds> } {
  const sorted = [...PRODUCT_CATALOG].sort((a, b) =>
    a.title.localeCompare(b.title),
  );

  const items = sorted
    .filter((product: Product) => !!product.dimensions)
    .map((product: Product) => {
      const dims = displayDimensions(product.dimensions!);
      return {
        id: String(product.id),
        kind: "product" as const,
        label: shortLabel(product.title),
        subtitle: formatDims(dims),
        dimensions: dims,
      };
    });

  const placed = layoutRow(items, 0, 0, PRODUCT_ROW_WIDTH);
  return { items: placed, zone: zoneBounds(placed) };
}

function layoutShippers(productZone: ReturnType<typeof zoneBounds>): {
  items: SceneItem[];
  zone: ReturnType<typeof zoneBounds>;
} {
  const [small, large] = BOX_CATALOG as Box[];
  const smallDims = displayDimensions(small.dimensions);
  const largeDims = displayDimensions(large.dimensions);
  const spacing = 6;

  const rowWidth = smallDims.length + spacing + largeDims.length;
  const productCenterX = (productZone.minX + productZone.maxX) / 2;
  const originX = productCenterX - rowWidth / 2;
  const originZ = productZone.maxZ + ZONE_GAP;

  const items: SceneItem[] = [
    {
      id: small.id,
      kind: "shipper",
      label: small.name,
      subtitle: formatDims(smallDims),
      dimensions: smallDims,
      position: [
        originX + smallDims.length / 2,
        smallDims.height / 2,
        originZ + Math.max(smallDims.width, largeDims.width) / 2,
      ],
    },
    {
      id: large.id,
      kind: "shipper",
      label: large.name,
      subtitle: formatDims(largeDims),
      dimensions: largeDims,
      position: [
        originX + smallDims.length + spacing + largeDims.length / 2,
        largeDims.height / 2,
        originZ + Math.max(smallDims.width, largeDims.width) / 2,
      ],
    },
  ];

  return { items, zone: zoneBounds(items) };
}

export interface CatalogSceneLayout {
  shippers: SceneItem[];
  products: SceneItem[];
  all: SceneItem[];
  bounds: {
    minX: number;
    maxX: number;
    minZ: number;
    maxZ: number;
    maxY: number;
  };
  shipperZone: { minX: number; maxX: number; minZ: number; maxZ: number };
  productZone: { minX: number; maxX: number; minZ: number; maxZ: number };
  sectionLabels: Array<{
    id: string;
    text: string;
    position: [number, number, number];
  }>;
}

function zoneBounds(items: SceneItem[]) {
  let minX = Infinity;
  let maxX = -Infinity;
  let minZ = Infinity;
  let maxZ = -Infinity;
  let maxY = 0;

  for (const item of items) {
    const [cx, cy, cz] = item.position;
    const { length: l, width: w, height: h } = item.dimensions;
    minX = Math.min(minX, cx - l / 2);
    maxX = Math.max(maxX, cx + l / 2);
    minZ = Math.min(minZ, cz - w / 2);
    maxZ = Math.max(maxZ, cz + w / 2);
    maxY = Math.max(maxY, cy + h / 2);
  }

  return { minX, maxX, minZ, maxZ, maxY };
}

export function buildCatalogLayout(): CatalogSceneLayout {
  const { items: products, zone: productZone } = layoutProducts();
  const { items: shippers, zone: shipperZone } = layoutShippers(productZone);

  const all = [...shippers, ...products];
  const bounds = zoneBounds(all);

  const shipperCenterX = (shipperZone.minX + shipperZone.maxX) / 2;
  const shipperCenterZ = (shipperZone.minZ + shipperZone.maxZ) / 2;
  const productCenterX = (productZone.minX + productZone.maxX) / 2;
  const productCenterZ = (productZone.minZ + productZone.maxZ) / 2;

  return {
    shippers,
    products,
    all,
    bounds: {
      minX: bounds.minX,
      maxX: bounds.maxX,
      minZ: bounds.minZ,
      maxZ: bounds.maxZ,
      maxY: bounds.maxY,
    },
    shipperZone,
    productZone,
    sectionLabels: [
      {
        id: "shippers-heading",
        text: "Shippers",
        position: [shipperCenterX, 0, shipperCenterZ],
      },
      {
        id: "products-heading",
        text: "Products",
        position: [productCenterX, 0, productCenterZ - 5],
      },
    ],
  };
}
