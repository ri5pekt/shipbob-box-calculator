export interface Dimensions {
  length: number;
  width: number;
  height: number;
}

export interface BundleComponent {
  sku: string;
  title: string;
  quantity: number;
}

export interface Product {
  id: number;
  title: string;
  sku: string;
  /** Present on individual products; absent on bundles (use components instead). */
  dimensions?: Dimensions;
  unit?: "in";
  category: string;
  dimensions_source?: string;
  unit_volume_cu_in?: number;
  unit_weight_lbs?: number;
  inventory_sku?: string | null;
  /** Bundle only: ordered list of component products. */
  components?: BundleComponent[];
}

/** True if this product is a bundle with resolved component list. */
export function isBundle(p: Product): p is Product & { components: BundleComponent[] } {
  return Array.isArray(p.components) && p.components.length > 0;
}

export interface Box {
  id: string;
  name: string;
  description: string;
  dimensions: Dimensions;
  dimensions_cm: Dimensions;
  unit: "in";
  dimension_type: "inner";
  inner_volume_cu_in: number;
  inventory_sku?: string | null;
  aliases?: string[];
  source?: string;
}

export interface OrderLine {
  product: Product;
  quantity: number;
}

export interface PlacedItem {
  product: Product;
  /** Bottom-left-front corner position (scene coords, centered on box). */
  position: [number, number, number];
  /** Actual rendered dimensions after rotation. */
  dimensions: Dimensions;
}

export interface PackingResult {
  box: Box | null;
  items: PlacedItem[];
  fits: boolean;
  unfittedProducts: Product[];
  message: string;
}
