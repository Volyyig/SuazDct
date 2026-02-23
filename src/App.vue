<script setup lang="ts">
/**
 * SuazDct — 应用壳组件
 *
 * 仅负责布局（顶部栏 / 主内容 / 底部导航）和页面切换。
 * 所有业务逻辑由子组件和组合式函数处理。
 */
import { computed, ref, onMounted } from 'vue';
import { useSettings } from './composables/useSettings';
import { useKeyboardOffset } from './composables/useKeyboardOffset';
import { releaseWindow } from './utils/cipher';

import AppHeader from './components/AppHeader.vue';
import BottomNav from './components/BottomNav.vue';
import SinglePage from './components/SinglePage.vue';
import SentencePage from './components/SentencePage.vue';

// 设置与主题
const { theme, settings, currentPage, toggleTheme, initSettings } = useSettings();

// 页面标题
const pageTitle = computed(() => (currentPage.value === 'single' ? '单字' : '字句'));

// 移动端键盘偏移
const navBarRef = ref<HTMLElement | null>(null);
const { keyboardOffset } = useKeyboardOffset(navBarRef);

onMounted(() => {
  initSettings();
  releaseWindow();
});
</script>

<template>
  <div class="app">
    <AppHeader
      :page-title="pageTitle"
      :theme="theme"
      v-model:settings="settings"
      @toggle-theme="toggleTheme"
    />

    <main class="content">
      <SinglePage v-show="currentPage === 'single'" :settings="settings" />
      <SentencePage v-show="currentPage === 'sentence'" :settings="settings" :keyboard-offset="keyboardOffset" />
    </main>

    <BottomNav ref="navBarRef" v-model:current-page="currentPage" />
  </div>
</template>

<style>
@import './assets/styles/variables.css';
@import './assets/styles/base.css';

.app {
  display: flex;
  flex-direction: column;
  height: 100vh;
  margin: 0 auto;
  position: relative;
}

.content {
  flex: 1;
  overflow-y: auto;
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
}
</style>
