<script setup lang="ts">
import { OrbitControls } from "@tresjs/cientos";
import { TresCanvas } from "@tresjs/core";
import { computed } from "vue";
import { buildCatalogLayout } from "../lib/layout/catalogLayout";
import LabeledObject from "./LabeledObject.vue";
import SectionLabel from "./SectionLabel.vue";

const layout = buildCatalogLayout();

const sceneCenter = computed<[number, number, number]>(() => {
  const { minX, maxX, minZ, maxZ } = layout.bounds;
  return [(minX + maxX) / 2, 0, (minZ + maxZ) / 2];
});

const cameraPosition = computed<[number, number, number]>(() => {
  const { minX, maxX, minZ, maxZ, maxY } = layout.bounds;
  const span = Math.max(maxX - minX, maxZ - minZ, maxY, 20);
  const [cx, , cz] = sceneCenter.value;
  return [cx + span * 0.45, span * 0.7, cz + span * 0.95];
});

function zoneSize(zone: { minX: number; maxX: number; minZ: number; maxZ: number }) {
  return {
    width: zone.maxX - zone.minX + 8,
    depth: zone.maxZ - zone.minZ + 8,
    centerX: (zone.minX + zone.maxX) / 2,
    centerZ: (zone.minZ + zone.maxZ) / 2,
  };
}

const shipperPad = computed(() => zoneSize(layout.shipperZone));
const productPad = computed(() => zoneSize(layout.productZone));
</script>

<template>
  <Suspense>
    <TresCanvas clear-color="#0f1117">
      <TresPerspectiveCamera
        :position="cameraPosition"
        :look-at="sceneCenter"
      />
      <OrbitControls :target="sceneCenter" :max-polar-angle="Math.PI / 2.05" />

      <TresAmbientLight :intensity="0.85" />
      <TresDirectionalLight :position="[20, 30, 10]" :intensity="0.35" />

      <!-- Shipper zone floor -->
      <TresMesh
        :rotation="[-Math.PI / 2, 0, 0]"
        :position="[shipperPad.centerX, -0.02, shipperPad.centerZ]"
      >
        <TresPlaneGeometry :args="[shipperPad.width, shipperPad.depth]" />
        <TresMeshBasicMaterial color="#0c2a32" />
      </TresMesh>

      <!-- Product zone floor -->
      <TresMesh
        :rotation="[-Math.PI / 2, 0, 0]"
        :position="[productPad.centerX, -0.02, productPad.centerZ]"
      >
        <TresPlaneGeometry :args="[productPad.width, productPad.depth]" />
        <TresMeshBasicMaterial color="#14182a" />
      </TresMesh>

      <SectionLabel
        v-for="section in layout.sectionLabels"
        :key="section.id"
        :text="section.text"
        :position="section.position"
      />

      <LabeledObject
        v-for="item in layout.all"
        :key="item.id"
        :id="item.id"
        :dimensions="item.dimensions"
        :position="item.position"
        :label="item.label"
        :subtitle="item.subtitle"
        :kind="item.kind"
      />
    </TresCanvas>
  </Suspense>
</template>
