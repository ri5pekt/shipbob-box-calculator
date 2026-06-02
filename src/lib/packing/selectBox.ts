import type { Box, Dimensions, OrderLine, PackingResult, PlacedItem, Product } from "../../types";
import { BOX_CATALOG } from "../../data/catalog";

function volume(d: Dimensions): number {
  return d.length * d.width * d.height;
}

function sortedDims(d: Dimensions): [number, number, number] {
  return [d.length, d.width, d.height].sort((a, b) => b - a) as [number, number, number];
}

/** Check if a single item fits inside a box (any rotation). */
export function itemFitsInBox(product: Product, box: Box): boolean {
  const [pL, pW, pH] = sortedDims(product.dimensions!);
  const [bL, bW, bH] = sortedDims(box.dimensions);
  return pL <= bL && pW <= bW && pH <= bH;
}

/** Naive shelf placement for visualization — one row along X, stacked in Y. */
function placeItemsNaively(items: Product[], box: Box): PlacedItem[] {
  const placed: PlacedItem[] = [];
  let x = 0;
  let z = 0;
  let rowDepth = 0;
  let y = 0;
  let rowHeight = 0;

  const { length: boxL, width: boxW, height: boxH } = box.dimensions;

  for (const product of items) {
    const { length: l, width: w, height: h } = product.dimensions!;

    if (x + l > boxL) {
      x = 0;
      z += rowDepth;
      rowDepth = 0;
    }

    if (z + w > boxW) {
      x = 0;
      z = 0;
      y += rowHeight;
      rowHeight = 0;
    }

    placed.push({
      product,
      dimensions: product.dimensions!,
      position: [x + l / 2 - boxL / 2, y + h / 2, z + w / 2 - boxW / 2],
    });

    x += l;
    rowDepth = Math.max(rowDepth, w);
    rowHeight = Math.max(rowHeight, h);

    if (y + h > boxH) break;
  }

  return placed;
}

function expandOrderLines(lines: OrderLine[]): Product[] {
  return lines.flatMap(({ product, quantity }) =>
    Array.from({ length: quantity }, () => product),
  );
}

/** Pick smallest box that fits all items (volume + largest-dimension heuristic). */
export function selectBox(lines: OrderLine[]): PackingResult {
  if (lines.length === 0) {
    return {
      box: null,
      items: [],
      fits: false,
      unfittedProducts: [],
      message: "Add at least one product to the order.",
    };
  }

  const items = expandOrderLines(lines);
  const totalVolume = items.reduce((sum, p) => sum + volume(p.dimensions!), 0);

  const candidates = [...BOX_CATALOG].sort(
    (a, b) => a.inner_volume_cu_in - b.inner_volume_cu_in,
  );

  for (const box of candidates) {
    const allItemsFit = items.every((p) => itemFitsInBox(p, box));
    const volumeFits = totalVolume <= box.inner_volume_cu_in;

    if (allItemsFit && volumeFits) {
      return {
        box,
        items: placeItemsNaively(items, box),
        fits: true,
        unfittedProducts: [],
        message: `Fits in ${box.name}.`,
      };
    }
  }

  return {
    box: null,
    items: [],
    fits: false,
    unfittedProducts: items,
    message: "Order does not fit in any available shipper.",
  };
}
