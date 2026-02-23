<script setup lang="ts">
/** 底部导航栏组件 */
import type { PageType } from '../types';

defineProps<{
  currentPage: PageType;
}>();

const emit = defineEmits<{
  (e: 'update:currentPage', page: PageType): void;
}>();
</script>

<template>
  <nav class="bottom-nav">
    <button type="button" class="nav-btn" :class="{ active: currentPage === 'single' }"
      @click="emit('update:currentPage', 'single')">
      <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none"
        stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M4 7h16M4 12h16M4 17h16" />
      </svg>
      <span class="nav-label">单字</span>
    </button>
    <button type="button" class="nav-btn" :class="{ active: currentPage === 'sentence' }"
      @click="emit('update:currentPage', 'sentence')">
      <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none"
        stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
        <polyline points="14 2 14 8 20 8" />
        <line x1="16" y1="13" x2="8" y2="13" />
        <line x1="16" y1="17" x2="8" y2="17" />
        <polyline points="10 9 9 9 8 9" />
      </svg>
      <span class="nav-label">字句</span>
    </button>
  </nav>
</template>

<style scoped>
.bottom-nav {
  display: flex;
  background: var(--surface-color);
  border-top: 1px solid var(--border-color);
  padding: 0.5rem 1rem;
  padding-bottom: max(0.5rem, env(safe-area-inset-bottom));
}

.nav-btn {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.25rem;
  padding: 0.5rem;
  background: transparent;
  border: none;
  border-radius: 0.75rem;
  color: var(--text-secondary);
  cursor: pointer;
  transition: var(--transition);
}

@media (hover: hover) {
  .nav-btn:hover {
    color: var(--text-primary);
    background: var(--bg-color);
  }
}

.nav-btn.active {
  color: var(--accent-color);
}

.nav-label {
  font-size: 0.75rem;
  font-weight: 500;
}
</style>
