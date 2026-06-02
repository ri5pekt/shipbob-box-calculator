<script setup lang="ts">
import { OrbitControls } from "@tresjs/cientos";
import { TresCanvas } from "@tresjs/core";
import { computed, ref, watch } from "vue";
import type { PackingResult } from "../types";
import PackedItemMesh from "./PackedItemMesh.vue";

const props = defineProps<{
  result: PackingResult | null;
  isAnimating: boolean;
}>();

const emit = defineEmits<{ animated: [] }>();

const PRODUCT_COLORS = [
  "#60a5fa", "#34d399", "#fbbf24", "#f472b6",
  "#a78bfa", "#fb923c", "#38bdf8", "#4ade80",
  "#e879f9", "#f97316",
];

const box = computed(() => props.result?.box ?? null);
const items = computed(() => props.result?.items ?? []);

const boxDims = computed(() => box.value?.dimensions ?? null);

const cameraPosition = computed<[number, number, number]>(() => {
  if (!boxDims.value) return [12, 9, 12];
  const m = Math.max(boxDims.value.length, boxDims.value.width, boxDims.value.height);
  return [m * 2.2, m * 1.8, m * 2.6];
});

// Animate items flying into the box
const visibleCount = ref(0);
let animTimer: ReturnType<typeof setTimeout> | null = null;

watch(
  () => props.isAnimating,
  (animating) => {
    if (!animating) return;
    visibleCount.value = 0;
    if (animTimer) clearTimeout(animTimer);

    const total = items.value.length;
    const step = () => {
      if (visibleCount.value < total) {
        visibleCount.value++;
        animTimer = setTimeout(step, 120);
      } else {
        emit("animated");
      }
    };
    animTimer = setTimeout(step, 80);
  },
);

// When result is cleared (reset) stop any running animation and hide all items.
watch(
  () => props.result,
  (newResult) => {
    if (!newResult) {
      if (animTimer) { clearTimeout(animTimer); animTimer = null; }
      visibleCount.value = 0;
    } else {
      visibleCount.value = items.value.length;
    }
  },
);

function colorForIndex(i: number) {
  return PRODUCT_COLORS[i % PRODUCT_COLORS.length];
}
</script>

<template>
  <Suspense>
    <TresCanvas clear-color="#0a0d13">
      <TresPerspectiveCamera :position="cameraPosition" :fov="45" />
      <OrbitControls
        :max-polar-angle="Math.PI / 2.05"
        :enable-damping="true"
        :damping-factor="0.07"
      />

      <TresAmbientLight :intensity="0.6" />
      <TresDirectionalLight :position="[6, 12, 8]" :intensity="1.0" cast-shadow />
      <TresDirectionalLight :position="[-6, 4, -6]" :intensity="0.3" />

      <!-- Empty state placeholder -->
      <template v-if="!boxDims">
        <TresMesh :position="[0, 1.5, 0]">
          <TresBoxGeometry :args="[3, 3, 3]" />
          <TresMeshStandardMaterial color="#1e293b" wireframe />
        </TresMesh>
      </template>

      <template v-else>
        <!-- Box floor -->
        <TresMesh :rotation="[-Math.PI / 2, 0, 0]" :position="[0, 0.001, 0]">
          <TresPlaneGeometry :args="[boxDims.length, boxDims.width]" />
          <TresMeshStandardMaterial
            color="#0f172a"
            :transparent="true"
            :opacity="0.7"
          />
        </TresMesh>

        <!-- Box walls (wireframe shell) -->
        <TresMesh :position="[0, boxDims.height / 2, 0]">
          <TresBoxGeometry :args="[boxDims.length, boxDims.height, boxDims.width]" />
          <TresMeshStandardMaterial
            :color="result?.fits ? '#22d3ee' : '#f87171'"
            :transparent="true"
            :opacity="0.06"
            :depth-write="false"
          />
        </TresMesh>
        <TresMesh :position="[0, boxDims.height / 2, 0]">
          <TresBoxGeometry :args="[boxDims.length, boxDims.height, boxDims.width]" />
          <TresMeshStandardMaterial
            :color="result?.fits ? '#22d3ee' : '#f87171'"
            wireframe
            :transparent="true"
            :opacity="0.45"
          />
        </TresMesh>

        <!-- Packed items with top-face labels -->
        <PackedItemMesh
          v-for="(item, i) in items.slice(0, visibleCount)"
          :key="`item-${item.product.id}-${i}`"
          :label="item.product.title"
          :dimensions="item.dimensions"
          :position="item.position"
          :color="colorForIndex(i)"
          :item-index="i"
        />
      </template>
    </TresCanvas>
  </Suspense>

  <!-- Overlay when empty -->
  <div v-if="!result" class="scene-overlay">
    <p>Select products and a box, then press Pack</p>
  </div>
</template>

<style scoped>
.scene-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: none;
  color: #475569;
  font-size: 0.9rem;
}
</style>
