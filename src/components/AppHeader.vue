<script setup lang="ts">
/** 顶部标题栏组件 */
import { ref, onMounted, onUnmounted } from 'vue';
import type { Settings, ThemeType } from '../types';
import SettingsMenu from './SettingsMenu.vue';

defineProps<{
  pageTitle: string;
  theme: ThemeType;
}>();

const emit = defineEmits<{
  (e: 'toggleTheme'): void;
}>();

const settings = defineModel<Settings>('settings', { required: true });

const showSettingsMenu = ref(false);
const settingsRef = ref<HTMLElement | null>(null);

/** 点击外部关闭设置菜单 */
function handleClickOutside(event: MouseEvent) {
  if (settingsRef.value && !settingsRef.value.contains(event.target as Node)) {
    showSettingsMenu.value = false;
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside);
});

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside);
});
</script>

<template>
  <header class="top-bar">
    <div class="top-bar-left">
      <h1 class="page-title">{{ pageTitle }}</h1>
    </div>

    <div class="top-bar-right">
      <!-- 切换主题按钮 -->
      <button type="button" class="icon-btn theme-toggle" @click="emit('toggleTheme')"
        :title="theme === 'light' ? '切换到暗色模式' : '切换到亮色模式'">
        <svg v-if="theme === 'dark'" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24"
          fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="5" />
          <path
            d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42" />
        </svg>
        <svg v-else xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none"
          stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
        </svg>
      </button>

      <!-- 设置按钮 -->
      <div class="settings-container" ref="settingsRef">
        <button type="button" class="icon-btn settings-btn" :class="{ active: showSettingsMenu }"
          @click.stop="showSettingsMenu = !showSettingsMenu" title="设置">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none"
            stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="3" />
            <path
              d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
          </svg>
        </button>

        <SettingsMenu v-if="showSettingsMenu" v-model:settings="settings" />
      </div>
    </div>
  </header>
</template>

<style scoped>
.top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  padding-top: max(1rem, env(safe-area-inset-top));
  border-bottom: 1px solid var(--border-color);
  background: var(--surface-color);
  z-index: 50;
  position: relative;
}

.settings-container {
  position: relative;
}

.page-title {
  font-size: 1.125rem;
  font-weight: 600;
  margin: 0;
  color: var(--text-primary);
}

.top-bar-right {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.icon-btn {
  background: transparent;
  border: 1px solid transparent;
  border-radius: 0.5rem;
  color: var(--text-secondary);
  padding: 0.5rem;
  cursor: pointer;
  transition: var(--transition);
  display: flex;
  align-items: center;
  justify-content: center;
}

@media (hover: hover) {
  .icon-btn:hover {
    background-color: var(--bg-color);
    color: var(--text-primary);
    border-color: var(--border-color);
  }
}

.icon-btn.active {
  background-color: var(--bg-color);
  color: var(--text-primary);
  border-color: var(--border-color);
  opacity: 0.7;
}
</style>
