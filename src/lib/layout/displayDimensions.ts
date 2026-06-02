import type { Dimensions } from "../../types";

/**
 * Catalog view orientation: shortest side = height (Y),
 * so items appear in typical flat packing pose and compare fairly to shippers.
 */
export function displayDimensions(d: Dimensions): Dimensions {
  const sorted = [d.length, d.width, d.height].sort((a, b) => b - a);
  return {
    length: sorted[0],
    width: sorted[1],
    height: sorted[2],
  };
}

export function formatDims(d: Dimensions): string {
  return `${d.length.toFixed(1)} × ${d.width.toFixed(1)} × ${d.height.toFixed(1)} in`;
}
