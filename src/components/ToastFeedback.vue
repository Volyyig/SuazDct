<script setup lang="ts">
/** Toast 反馈提示组件 */
withDefaults(defineProps<{
  message: string;
  visible: boolean;
  keyboardOffset?: number;
}>(), {
  keyboardOffset: 0
});
</script>

<template>
  <Transition name="toast-fade">
    <div v-if="visible" class="toast-feedback"
      :style="{ transform: `translateX(-50%) translateY(-${keyboardOffset}px)` }">
      {{ message }}
    </div>
  </Transition>
</template>

<style scoped>
.toast-feedback {
  position: fixed;
  bottom: 120px;
  left: 50%;
  background: rgba(0, 0, 0, 0.8);
  color: white;
  padding: 0.6rem 1.2rem;
  border-radius: 2rem;
  font-size: 0.875rem;
  z-index: 1000;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  pointer-events: none;
  transition: transform 0.3s ease;
}

[data-theme="light"] .toast-feedback {
  background: rgba(0, 0, 0, 0.75);
}

.toast-fade-enter-active,
.toast-fade-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}

.toast-fade-enter-from,
.toast-fade-leave-to {
  opacity: 0;
  transform: translate(-50%, 10px);
}
</style>
