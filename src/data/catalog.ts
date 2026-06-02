import products from "../../data/products.json";
import boxes from "../../data/boxes.json";
import type { Box, Product } from "../types";

export const PRODUCT_CATALOG = products as Product[];
export const BOX_CATALOG = boxes as Box[];

export function findProductBySku(sku: string): Product | undefined {
  return PRODUCT_CATALOG.find((p) => p.sku === sku);
}

export function findProductById(id: number): Product | undefined {
  return PRODUCT_CATALOG.find((p) => p.id === id);
}

export function findBoxById(id: string): Box | undefined {
  return BOX_CATALOG.find((b) => b.id === id);
}
