<script setup lang="ts">
import { computed, ref, nextTick, watch } from "vue";
import PackingScene from "./components/PackingScene.vue";
import { BOX_CATALOG, PRODUCT_CATALOG } from "./data/catalog";
import { packIntoBox } from "./lib/packing/packItems";
import { isBundle } from "./types";
import type { Box, OrderLine, PackingResult, Product } from "./types";

const PRODUCT_COLORS = [
  "#60a5fa", "#34d399", "#fbbf24", "#f472b6",
  "#a78bfa", "#fb923c", "#38bdf8", "#4ade80",
  "#e879f9", "#f97316",
];

// ── product list ──────────────────────────────────────────────
const BUNDLE_CATEGORIES = new Set(["bundle", "kit"]);

const sortedProducts = computed(() =>
  [...PRODUCT_CATALOG].sort((a, b) => {
    const aIsBundle = BUNDLE_CATEGORIES.has(a.category) ? 1 : 0;
    const bIsBundle = BUNDLE_CATEGORIES.has(b.category) ? 1 : 0;
    if (aIsBundle !== bIsBundle) return aIsBundle - bIsBundle;
    return a.title.localeCompare(b.title);
  }),
);

// ── order state ───────────────────────────────────────────────
interface OrderEntry { product: Product; quantity: number }
const orderEntries = ref<OrderEntry[]>([]);

function isInOrder(product: Product) {
  return orderEntries.value.some((e) => e.product.id === product.id);
}

function toggleProduct(product: Product) {
  const idx = orderEntries.value.findIndex((e) => e.product.id === product.id);
  if (idx >= 0) {
    orderEntries.value.splice(idx, 1);
  } else {
    orderEntries.value.push({ product, quantity: 1 });
  }
}

function changeQty(product: Product, delta: number) {
  const entry = orderEntries.value.find((e) => e.product.id === product.id);
  if (!entry) return;
  entry.quantity = Math.max(1, entry.quantity + delta);
}

// ── box selector ──────────────────────────────────────────────
const selectedBoxId = ref<string>(BOX_CATALOG[0]?.id ?? "");
const selectedBox = computed<Box | undefined>(
  () => BOX_CATALOG.find((b) => b.id === selectedBoxId.value),
);

// ── packing ───────────────────────────────────────────────────
const packingResult = ref<PackingResult | null>(null);
const isAnimating = ref(false);
const isPacking = ref(false);
const sceneKey = ref(0);
/** Set when "Find proper box" is used so the result card shows the decision. */
const autoBoxDecision = ref<"small" | "large" | "none" | null>(null);

/** SKU → product lookup for resolving bundle components. */
const productBySku = Object.fromEntries(PRODUCT_CATALOG.map((p) => [p.sku, p]));

/**
 * Expand order entries into flat OrderLines.
 * Bundles are exploded into their individual component products.
 * Quantities multiply: 2× Lady Killer Kit → 2× each component.
 */
const orderLines = computed<OrderLine[]>(() => {
  const lines: Record<string, OrderLine> = {};

  for (const entry of orderEntries.value) {
    const { product, quantity } = entry;

    if (isBundle(product)) {
      for (const comp of product.components) {
        const compProduct = productBySku[comp.sku];
        if (!compProduct) continue;
        const key = compProduct.sku;
        if (lines[key]) {
          lines[key].quantity += comp.quantity * quantity;
        } else {
          lines[key] = { product: compProduct, quantity: comp.quantity * quantity };
        }
      }
    } else {
      const key = product.sku;
      if (lines[key]) {
        lines[key].quantity += quantity;
      } else {
        lines[key] = { product, quantity };
      }
    }
  }

  return Object.values(lines);
});

async function doPack() {
  if (!selectedBox.value || orderEntries.value.length === 0) return;
  isPacking.value = true;
  packingResult.value = null;
  autoBoxDecision.value = null;
  isAnimating.value = false;

  await new Promise<void>((r) => setTimeout(r, 30));

  packingResult.value = packIntoBox(orderLines.value, selectedBox.value);
  isPacking.value = false;
  isAnimating.value = true;
}

async function findBestBox() {
  if (orderEntries.value.length === 0) return;
  isPacking.value = true;
  packingResult.value = null;
  autoBoxDecision.value = null;
  isAnimating.value = false;

  await new Promise<void>((r) => setTimeout(r, 30));

  // Try boxes smallest → largest
  for (const box of BOX_CATALOG) {
    const result = packIntoBox(orderLines.value, box);
    if (result.fits) {
      // 1. Switch box selection — packingResult is null so the watch no-ops
      selectedBoxId.value = box.id;
      // 2. Wait for the watch to flush (it sees null → early return, no clear)
      await nextTick();
      // 3. Now set the result safely
      packingResult.value = result;
      autoBoxDecision.value = box.id === "small-shipper" ? "small" : "large";
      isPacking.value = false;
      isAnimating.value = true;
      return;
    }
  }

  // Nothing fits — show the largest box attempt so products are visible
  const largest = BOX_CATALOG[BOX_CATALOG.length - 1];
  selectedBoxId.value = largest.id;
  await nextTick();
  packingResult.value = {
    ...packIntoBox(orderLines.value, largest),
    fits: false,
    message: "Products don't fit in any available box.",
  };
  autoBoxDecision.value = "none";
  isPacking.value = false;
}

// Clear the scene whenever the order or box selection changes after a pack
watch(
  [orderEntries, selectedBoxId],
  async () => {
    if (packingResult.value === null) return;
    packingResult.value = null;
    autoBoxDecision.value = null;
    isAnimating.value = false;
    await nextTick();
    sceneKey.value++;
  },
  { deep: true },
);

async function doReset() {
  packingResult.value = null;
  autoBoxDecision.value = null;
  isAnimating.value = false;
  orderEntries.value = [];
  selectedBoxId.value = BOX_CATALOG[0]?.id ?? "";
  await nextTick();
  sceneKey.value++;
}


function onAnimated() {
  isAnimating.value = false;
}

// ── helpers ───────────────────────────────────────────────────
function fmtDims(p: Product) {
  if (isBundle(p)) return `${p.components.length} items`;
  if (!p.dimensions) return "—";
  const { length: l, width: w, height: h } = p.dimensions;
  return `${l.toFixed(1)}×${w.toFixed(1)}×${h.toFixed(1)} in`;
}

function colorForEntry(idx: number) {
  return PRODUCT_COLORS[idx % PRODUCT_COLORS.length];
}

function displayName(title: string) {
  return title.replace(/^Particle\s+/i, "");
}
</script>

<template>
  <div class="app">
    <header class="topbar">
      <span class="topbar-title">Particle — Box Calculator</span>
    </header>

    <div class="layout">
      <!-- ── LEFT PANEL ── -->
      <aside class="panel">

        <!-- Products -->
        <section class="section">
          <div class="section-head">
            <h2>Products</h2>
            <span class="badge">{{ orderEntries.length }} selected</span>
          </div>
          <div class="product-list">
            <template v-for="(p, idx) in sortedProducts" :key="p.id">
              <!-- Divider between products and bundles -->
              <div
                v-if="idx > 0 && BUNDLE_CATEGORIES.has(p.category) && !BUNDLE_CATEGORIES.has(sortedProducts[idx - 1].category)"
                class="list-divider"
              >
                Sets &amp; Bundles
              </div>
            <button
              type="button"
              class="product-row"
              :class="{ selected: isInOrder(p) }"
              @click="toggleProduct(p)"
            >
              <span class="product-check">
                <svg v-if="isInOrder(p)" viewBox="0 0 12 12" width="11" height="11">
                  <polyline points="1.5,6 4.5,9 10.5,3" stroke="currentColor" stroke-width="1.8" fill="none" stroke-linecap="round"/>
                </svg>
              </span>
              <span class="product-name">{{ displayName(p.title) }}</span>
              <span class="product-dim" :class="{ 'dim-bundle': isBundle(p) }">{{ fmtDims(p) }}</span>

              <!-- qty controls -->
              <span v-if="isInOrder(p)" class="qty-row" @click.stop>
                <button class="qty-btn" @click="changeQty(p, -1)">−</button>
                <span class="qty-val">{{ orderEntries.find(e => e.product.id === p.id)?.quantity }}</span>
                <button class="qty-btn" @click="changeQty(p, +1)">+</button>
              </span>
            </button>

            <!-- Bundle component list (shown when selected) -->
            <div
              v-if="isBundle(p) && isInOrder(p)"
              class="bundle-components"
            >
              <span
                v-for="comp in p.components"
                :key="comp.sku"
                class="bundle-comp-tag"
              >{{ comp.quantity > 1 ? `${comp.quantity}× ` : '' }}{{ comp.title }}</span>
            </div>
            </template>
          </div>
        </section>

        <!-- Box selector -->
        <section class="section">
          <h2>Select Box</h2>
          <div class="box-cards">
            <button
              v-for="box in BOX_CATALOG"
              :key="box.id"
              type="button"
              class="box-card"
              :class="{ active: selectedBoxId === box.id, cyan: box.id === 'small-shipper', amber: box.id === 'large-shipper' }"
              @click="selectedBoxId = box.id"
            >
              <span class="box-card-name">{{ box.name }}</span>
              <span class="box-card-dim">
                {{ +box.dimensions.length.toFixed(1) }}×{{ +box.dimensions.width.toFixed(1) }}×{{ +box.dimensions.height.toFixed(1) }} in
              </span>
              <span class="box-card-vol">{{ box.inner_volume_cu_in }} cu in</span>
            </button>
          </div>
        </section>

        <!-- Actions -->
        <section class="section actions">
          <button
            type="button"
            class="btn find"
            :disabled="orderEntries.length === 0 || isPacking"
            @click="findBestBox"
          >
            <span v-if="isPacking">Checking…</span>
            <span v-else>Find Box ✦</span>
          </button>
          <button
            type="button"
            class="btn pack"
            :disabled="orderEntries.length === 0 || isPacking"
            @click="doPack"
          >
            <span v-if="isPacking">Packing…</span>
            <span v-else>Pack →</span>
          </button>
          <button type="button" class="btn reset" @click="doReset">
            Reset
          </button>
        </section>

        <!-- Result -->
        <section
          v-if="packingResult"
          class="result-card"
          :class="packingResult.fits ? 'success' : 'fail'"
        >
          <!-- Auto-box decision banner -->
          <div v-if="autoBoxDecision" class="decision-banner" :class="autoBoxDecision">
            <template v-if="autoBoxDecision === 'small'">
              📦 Use <strong>Small Shipper</strong>
            </template>
            <template v-else-if="autoBoxDecision === 'large'">
              📦 Use <strong>Large Shipper</strong>
            </template>
            <template v-else>
              ⚠️ <strong>Need a bigger box</strong>
            </template>
          </div>

          <div class="result-status">
            {{ packingResult.fits ? "✓ Fits" : "✗ Doesn't fit" }}
          </div>
          <p class="result-msg">{{ packingResult.message }}</p>

          <ul v-if="packingResult.items.length" class="item-legend">
            <li
              v-for="(item, i) in packingResult.items"
              :key="`legend-${i}`"
              class="legend-row"
            >
              <span class="legend-swatch" :style="{ background: colorForEntry(i) }" />
              <span class="legend-name">{{ displayName(item.product.title) }}</span>
            </li>
          </ul>

          <div v-if="packingResult.unfittedProducts.length" class="unfitted">
            <p class="unfitted-label">Didn't fit:</p>
            <p
              v-for="(p, i) in packingResult.unfittedProducts"
              :key="`unfit-${i}`"
              class="unfitted-item"
            >
              {{ displayName(p.title) }}
            </p>
          </div>
        </section>

      </aside>

      <!-- ── 3D VIEWER ── -->
      <main class="viewer">
        <PackingScene
          :key="sceneKey"
          :result="packingResult"
          :is-animating="isAnimating"
          @animated="onAnimated"
        />

        <!-- Box label overlay -->
        <div v-if="packingResult?.box" class="box-label-overlay">
          <span
            class="box-pill"
            :class="packingResult.box.id === 'small-shipper' ? 'cyan' : 'amber'"
          >
            {{ packingResult.box.name }}
            &nbsp;·&nbsp;
            {{ +packingResult.box.dimensions.length.toFixed(1) }}×{{
              +packingResult.box.dimensions.width.toFixed(1)
            }}×{{ +packingResult.box.dimensions.height.toFixed(1) }} in
          </span>
        </div>
      </main>
    </div>
  </div>
</template>

<style scoped>
/* ── layout ──────────────────────────────────────── */
.app {
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
  background: #0a0d13;
  color: #e2e8f0;
  font-family: system-ui, -apple-system, sans-serif;
}

.topbar {
  display: flex;
  align-items: center;
  padding: 0 1.25rem;
  height: 44px;
  border-bottom: 1px solid #1e293b;
  flex-shrink: 0;
}

.topbar-title {
  font-size: 0.875rem;
  font-weight: 600;
  color: #94a3b8;
  letter-spacing: 0.03em;
}

.layout {
  display: grid;
  grid-template-columns: 340px 1fr;
  flex: 1;
  min-height: 0;
}

/* ── panel ───────────────────────────────────────── */
.panel {
  border-right: 1px solid #1e293b;
  display: flex;
  flex-direction: column;
  gap: 0;
  overflow-y: auto;
  padding: 0;
}

.section {
  padding: 1rem 1rem 0.75rem;
  border-bottom: 1px solid #1a2030;
}

.section-head {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

h2 {
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #64748b;
  margin-bottom: 0.5rem;
}

.section-head h2 { margin-bottom: 0; }

.badge {
  font-size: 0.68rem;
  background: #1e293b;
  color: #94a3b8;
  padding: 1px 6px;
  border-radius: 10px;
}

/* ── product list ────────────────────────────────── */
.product-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
  max-height: 300px;
  overflow-y: auto;
}

.product-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 5px 6px;
  border-radius: 5px;
  border: 1px solid transparent;
  background: transparent;
  color: #cbd5e1;
  cursor: pointer;
  text-align: left;
  font-size: 0.78rem;
  transition: background 0.1s;
}

.list-divider {
  font-size: 0.65rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #475569;
  padding: 8px 6px 3px;
  border-top: 1px solid #1e293b;
  margin-top: 4px;
}

.product-row:hover { background: #0f172a; }
.product-row.selected {
  background: #0f1e35;
  border-color: #1e3a5f;
  color: #e2e8f0;
}

.product-check {
  width: 14px;
  height: 14px;
  border: 1px solid #334155;
  border-radius: 3px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: #60a5fa;
  background: #0f172a;
}

.product-row.selected .product-check {
  border-color: #3b82f6;
  background: #1e3a5f;
}

.product-name {
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.product-dim {
  font-size: 0.68rem;
  color: #475569;
  flex-shrink: 0;
  font-variant-numeric: tabular-nums;
}

.qty-row {
  display: flex;
  align-items: center;
  gap: 3px;
  flex-shrink: 0;
}

.qty-btn {
  width: 18px;
  height: 18px;
  border-radius: 3px;
  border: 1px solid #334155;
  background: #1e293b;
  color: #94a3b8;
  cursor: pointer;
  font-size: 0.75rem;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  line-height: 1;
}

.qty-btn:hover { background: #273549; color: #e2e8f0; }

.qty-val {
  font-size: 0.75rem;
  min-width: 16px;
  text-align: center;
  color: #e2e8f0;
}

/* ── box cards ───────────────────────────────────── */
.box-cards {
  display: flex;
  gap: 0.5rem;
}

.box-card {
  flex: 1;
  padding: 0.6rem 0.75rem;
  border-radius: 7px;
  border: 1.5px solid #1e293b;
  background: #0d1117;
  color: #94a3b8;
  cursor: pointer;
  text-align: left;
  display: flex;
  flex-direction: column;
  gap: 2px;
  transition: all 0.12s;
}

.box-card:hover { border-color: #334155; }

.box-card.active.cyan { border-color: #22d3ee; background: #0a2030; color: #e2e8f0; }
.box-card.active.amber { border-color: #fbbf24; background: #1a1500; color: #e2e8f0; }

.box-card-name { font-size: 0.8rem; font-weight: 600; }
.box-card-dim  { font-size: 0.68rem; color: #64748b; }
.box-card.active .box-card-dim { color: #94a3b8; }
.box-card-vol  { font-size: 0.65rem; color: #475569; }

/* ── actions ─────────────────────────────────────── */
.actions {
  display: flex;
  gap: 0.5rem;
}

.btn {
  flex: 1;
  padding: 0.6rem;
  border-radius: 7px;
  border: 1px solid transparent;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.12s;
}

.btn.find {
  background: #6d28d9;
  color: #fff;
  border-color: #7c3aed;
  flex: 1.4;
}
.btn.find:hover:not(:disabled) { background: #5b21b6; }
.btn.find:disabled { opacity: 0.45; cursor: not-allowed; }

.btn.pack {
  background: #2563eb;
  color: #fff;
  border-color: #3b82f6;
}
.btn.pack:hover:not(:disabled) { background: #1d4ed8; }
.btn.pack:disabled { opacity: 0.45; cursor: not-allowed; }

.btn.reset {
  background: #1e293b;
  color: #94a3b8;
  border-color: #334155;
  flex: 0.7;
}
.btn.reset:hover { background: #273549; color: #e2e8f0; }

/* ── decision banner ─────────────────────────────── */
.decision-banner {
  font-size: 0.82rem;
  padding: 6px 10px;
  border-radius: 6px;
  margin-bottom: 0.625rem;
  border: 1px solid;
}
.decision-banner.small {
  background: #0a2030;
  border-color: #22d3ee;
  color: #67e8f9;
}
.decision-banner.large {
  background: #1a1500;
  border-color: #fbbf24;
  color: #fde68a;
}
.decision-banner.none {
  background: #1f0a0a;
  border-color: #f87171;
  color: #fca5a5;
}

/* ── result card ─────────────────────────────────── */
.result-card {
  padding: 0.875rem 1rem;
  border-top: none;
}

.result-card.success { background: #052e16; border-top: 2px solid #22c55e; }
.result-card.fail    { background: #1f0a0a; border-top: 2px solid #f87171; }

.result-status {
  font-size: 0.9rem;
  font-weight: 700;
  margin-bottom: 0.25rem;
}
.result-card.success .result-status { color: #4ade80; }
.result-card.fail    .result-status { color: #f87171; }

.result-msg { font-size: 0.78rem; color: #94a3b8; margin-bottom: 0.625rem; }

.item-legend {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 3px;
  margin-bottom: 0.5rem;
}

.legend-row {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.legend-swatch {
  width: 10px;
  height: 10px;
  border-radius: 2px;
  flex-shrink: 0;
}

.legend-name { font-size: 0.73rem; color: #cbd5e1; }

.dim-bundle {
  color: #7c3aed;
  font-weight: 600;
}

.bundle-components {
  display: flex;
  flex-wrap: wrap;
  gap: 3px;
  padding: 4px 6px 6px 26px;
}

.bundle-comp-tag {
  font-size: 0.64rem;
  background: #160d2a;
  border: 1px solid #3b1d6e;
  color: #a78bfa;
  padding: 1px 6px;
  border-radius: 10px;
  white-space: nowrap;
}

.unfitted { margin-top: 0.375rem; }
.unfitted-label { font-size: 0.7rem; color: #f87171; margin-bottom: 2px; }
.unfitted-item  { font-size: 0.73rem; color: #fca5a5; }

/* ── viewer ──────────────────────────────────────── */
.viewer {
  position: relative;
  min-height: 0;
}

.box-label-overlay {
  position: absolute;
  top: 1rem;
  left: 50%;
  transform: translateX(-50%);
  pointer-events: none;
}

.box-pill {
  display: inline-block;
  padding: 4px 14px;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.03em;
  backdrop-filter: blur(8px);
  background: rgba(10, 13, 19, 0.75);
  border: 1px solid;
}

.box-pill.cyan  { border-color: #22d3ee; color: #67e8f9; }
.box-pill.amber { border-color: #fbbf24; color: #fde68a; }
</style>
