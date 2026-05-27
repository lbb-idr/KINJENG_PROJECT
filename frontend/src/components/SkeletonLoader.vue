<template>
  <div class="skeleton" :class="[shape, { shimmer: !noShimmer }]" :style="{ width, height, borderRadius }">
    <div v-if="!noShimmer" class="skeleton-shimmer"></div>
  </div>
</template>

<script setup>
defineProps({
  width: { type: String, default: '100%' },
  height: { type: String, default: '20px' },
  shape: { type: String, default: 'rect' },
  borderRadius: { type: String, default: '8px' },
  noShimmer: { type: Boolean, default: false }
})
</script>

<style scoped>
.skeleton {
  background: var(--skeleton-bg, #e0e0e0);
  overflow: hidden;
  position: relative;
}
.skeleton.circle { border-radius: 50%; }
.skeleton.text { border-radius: 4px; height: 1em; margin-bottom: 8px; }
.skeleton-shimmer {
  position: absolute; inset: 0;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent);
  animation: shimmer 1.5s infinite;
}
@keyframes shimmer { 0% { transform: translateX(-100%) } 100% { transform: translateX(100%) } }
[data-theme='dark'] .skeleton { background: #333; }
[data-theme='dark'] .skeleton-shimmer { background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent); }
</style>
