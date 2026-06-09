import { getDimension, pack3D, RotationType } from "binpackingjs/3d";
import type { Box, Dimensions, OrderLine, PackingResult, PlacedItem, Product } from "../../types";

/** Bundles / kits should stay flat — only rotations that keep the short axis as height. */
const FLAT_CATEGORIES = new Set(["bundle", "kit"]);
const FLAT_ROTATIONS = [
  RotationType.WHD,
  RotationType.HWD,
  RotationType.WDH,
  RotationType.DWH,
];

/**
 * Inner padding so items don't press the walls (inches).
 * Kept small because our shippers are only ~3 in tall — aggressive padding
 * causes false negatives on borderline products.
 */
const PADDING = 0.03;

const round4 = (n: number) => Math.round(n * 10000) / 10000;

function paddedBox(box: Box) {
  const { length, width, height } = box.dimensions;
  return {
    name: box.id,
    width:  round4(length + PADDING),
    height: round4(height + PADDING),
    depth:  round4(width  + PADDING),
    maxWeight: 99999,
  };
}

function expandOrderLines(lines: OrderLine[]): Product[] {
  return lines.flatMap(({ product, quantity }) =>
    Array.from({ length: quantity }, () => product),
  );
}

function rotationDimensions(product: Product, rotationType: number): Dimensions {
  const dims = product.dimensions!;
  // binpackingjs item: width = product.length, height = product.height, depth = product.width
  const [rw, rh, rd] = getDimension(
    dims.length,
    dims.height,
    dims.width,
    rotationType,
  );
  return { length: rw, height: rh, width: rd };
}

export function packIntoBox(lines: OrderLine[], box: Box): PackingResult {
  if (lines.length === 0) {
    return {
      box: null,
      items: [],
      fits: false,
      unfittedProducts: [],
      message: "Add at least one product.",
    };
  }

  // Skip any products that somehow still lack dimensions (safety guard)
  const validLines = lines.filter((l) => !!l.product.dimensions);

  const products = expandOrderLines(validLines);

  const items = products.map((p, i) => ({
    name: `${p.id}__${i}`,
    width: p.dimensions!.length,
    height: p.dimensions!.height,
    depth: p.dimensions!.width,
    weight: p.unit_weight_lbs ?? 1,
    ...(FLAT_CATEGORIES.has(p.category) ? { allowedRotations: FLAT_ROTATIONS } : {}),
  }));

  const result = pack3D({
    bins: [paddedBox(box)],
    items,
  });

  const packedBin = result.packedBins[0];
  const unfitItems = result.unfitItems ?? [];

  const unfittedProducts = unfitItems.map((ui) => {
    const idx = parseInt(ui.name.split("__")[1] ?? "0", 10);
    return products[idx] ?? products[0];
  });

  const fits = unfitItems.length === 0 && packedBin != null;

  if (!packedBin) {
    return {
      box,
      items: [],
      fits: false,
      unfittedProducts,
      message: `Does not fit in ${box.name}.`,
    };
  }

  // half-extents for centering scene around origin
  const bHalfL = box.dimensions.length / 2;
  const bHalfW = box.dimensions.width / 2;

  const placed: PlacedItem[] = packedBin.items.map((pi) => {
    const idx = parseInt(pi.name.split("__")[1] ?? "0", 10);
    const product = products[idx] ?? products[0];
    const dims = rotationDimensions(product, pi.rotationType);

    // pi.position is [x, y, z] corner in bin space (origin = bottom-left-front)
    const [px, py, pz] = pi.position as [number, number, number];
    const centerX = px + dims.length / 2 - bHalfL;
    const centerY = py + dims.height / 2;
    const centerZ = pz + dims.width / 2 - bHalfW;

    return {
      product,
      dimensions: dims,
      position: [centerX, centerY, centerZ],
    };
  });

  const total = products.length;
  const message = fits
    ? `All ${total} item${total > 1 ? "s" : ""} fit in ${box.name}.`
    : `${unfittedProducts.length} item${unfittedProducts.length > 1 ? "s" : ""} did not fit in ${box.name}.`;

  return { box, items: placed, fits, unfittedProducts, message };
}
