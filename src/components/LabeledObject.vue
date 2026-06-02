<script setup lang="ts">
import { Edges } from "@tresjs/cientos";
import { DoubleSide } from "three";
import { computed, onBeforeUnmount, shallowRef, watch } from "vue";
import {
  createFaceLabelTexture,
  disposeFaceLabelTexture,
} from "../lib/label/createFaceLabelTexture";
import type { SceneItemKind } from "../lib/layout/catalogLayout";
import type { Dimensions } from "../types";

const props = defineProps<{
  id: string;
  dimensions: Dimensions;
  position: [number, number, number];
  label: string;
  subtitle: string;
  kind: SceneItemKind;
}>();

const colors = computed(() => {
  if (props.kind === "shipper") {
    if (props.id === "small-shipper") {
      return { fill: "#06b6d4", edge: "#22d3ee", labelBorder: "#22d3ee" };
    }
    return { fill: "#f59e0b", edge: "#fbbf24", labelBorder: "#fbbf24" };
  }
  return { fill: "#6366f1", edge: "#818cf8", labelBorder: "#818cf8" };
});

const labelTexture = shallowRef<ReturnType<typeof createFaceLabelTexture> | null>(null);

function rebuildLabel() {
  disposeFaceLabelTexture(labelTexture.value?.texture);
  labelTexture.value = createFaceLabelTexture({
    title: props.label,
    subtitle: props.subtitle,
    borderColor: colors.value.labelBorder,
    isShipper: props.kind === "shipper",
    maxPlaneWidth: props.dimensions.length * 0.94,
    maxPlaneHeight: props.dimensions.height * 0.94,
  });
}

watch(
  () => [props.label, props.subtitle, props.kind, props.id, props.dimensions],
  rebuildLabel,
  { immediate: true, deep: true },
);

onBeforeUnmount(() => {
  disposeFaceLabelTexture(labelTexture.value?.texture);
});

/** Sits flush on the front face (+Z), centered vertically and horizontally. */
const labelPosition = computed<[number, number, number]>(() => [
  0,
  0,
  props.dimensions.width / 2 + 0.012,
]);
</script>

<template>
  <TresGroup :position="position">
    <TresMesh>
      <TresBoxGeometry
        :args="[dimensions.length, dimensions.height, dimensions.width]"
      />
      <TresMeshBasicMaterial
        :color="colors.fill"
        :transparent="true"
        :opacity="kind === 'shipper' ? 0.22 : 0.18"
      />
      <Edges :color="colors.edge" :threshold="15" />
    </TresMesh>

    <TresMesh v-if="labelTexture" :position="labelPosition">
      <TresPlaneGeometry
        :args="[labelTexture.planeWidth, labelTexture.planeHeight]"
      />
      <TresMeshBasicMaterial
        :map="labelTexture.texture"
        :transparent="true"
        :side="DoubleSide"
        :depth-write="false"
        :polygon-offset="true"
        :polygon-offset-factor="-1"
        :polygon-offset-units="-1"
      />
    </TresMesh>
  </TresGroup>
</template>
