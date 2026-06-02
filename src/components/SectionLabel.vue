<script setup lang="ts">
import { DoubleSide } from "three";
import { computed, onBeforeUnmount, shallowRef, watch } from "vue";
import {
  createFaceLabelTexture,
  disposeFaceLabelTexture,
} from "../lib/label/createFaceLabelTexture";

const props = defineProps<{
  text: string;
  position: [number, number, number];
}>();

const labelTexture = shallowRef<ReturnType<typeof createFaceLabelTexture> | null>(null);

function rebuildLabel() {
  disposeFaceLabelTexture(labelTexture.value?.texture);
  labelTexture.value = createFaceLabelTexture({
    title: props.text,
    subtitle: "",
    borderColor: "#64748b",
    isShipper: true,
    maxPlaneWidth: 14,
    maxPlaneHeight: 4,
  });
}

watch(() => props.text, rebuildLabel, { immediate: true });

onBeforeUnmount(() => {
  disposeFaceLabelTexture(labelTexture.value?.texture);
});

/** Flat on the ground in front of each zone. */
const planePosition = computed<[number, number, number]>(() => [
  props.position[0],
  0.02,
  props.position[2] - 6,
]);
</script>

<template>
  <TresMesh
    v-if="labelTexture"
    :position="planePosition"
    :rotation="[-Math.PI / 2, 0, 0]"
  >
    <TresPlaneGeometry
      :args="[labelTexture.planeWidth, labelTexture.planeHeight]"
    />
    <TresMeshBasicMaterial
      :map="labelTexture.texture"
      :transparent="true"
      :side="DoubleSide"
      :depth-write="false"
    />
  </TresMesh>
</template>
