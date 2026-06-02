<script setup lang="ts">
import { shallowRef, watch, onBeforeUnmount } from "vue";
import {
  buildBoxMaterials,
  disposeBoxMaterials,
} from "../lib/label/createItemLabel";
import type { Dimensions } from "../types";

const props = defineProps<{
  label: string;
  dimensions: Dimensions;
  position: [number, number, number];
  color: string;
  itemIndex: number;
}>();

// ── materials (one per BoxGeometry face) ─────────────────────
import type { MeshStandardMaterial } from "three";
const materials = shallowRef<MeshStandardMaterial[]>([]);

function rebuildMaterials() {
  disposeBoxMaterials(materials.value);
  const shortName = props.label.replace(/^Particle\s+/i, "");
  materials.value = buildBoxMaterials(props.color, props.dimensions, shortName);
}

watch(
  () => [props.label, props.color, props.dimensions],
  rebuildMaterials,
  { immediate: true, deep: true },
);

onBeforeUnmount(() => disposeBoxMaterials(materials.value));
</script>

<template>
  <TresGroup :position="position">
    <!-- Solid fill with top-face label baked in as texture -->
    <TresMesh :material="materials">
      <TresBoxGeometry
        :args="[dimensions.length, dimensions.height, dimensions.width]"
      />
    </TresMesh>

    <!-- Wireframe edges -->
    <TresMesh>
      <TresBoxGeometry
        :args="[
          dimensions.length + 0.006,
          dimensions.height + 0.006,
          dimensions.width  + 0.006,
        ]"
      />
      <TresMeshBasicMaterial
        :color="color"
        wireframe
        :transparent="true"
        :opacity="0.3"
      />
    </TresMesh>
  </TresGroup>
</template>
