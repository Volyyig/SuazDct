<script setup lang="ts">
/** 设置下拉菜单组件 */
import type { Settings } from '../types';

const settings = defineModel<Settings>('settings', { required: true });
</script>

<template>
  <div class="settings-menu">
    <div class="menu-item">
      <label class="menu-label">
        <input type="checkbox" v-model="settings.traditionalEnabled" class="menu-checkbox" />
        <span class="menu-text">繁体启用</span>
      </label>
    </div>
    <div class="menu-separator"></div>
    <div class="menu-item">
      <div class="menu-group-title">密文格式</div>
      <div class="radio-group">
        <label class="radio-label">
          <input type="radio" v-model="settings.cipherFormat" value="4-letter" class="menu-radio" />
          <span class="radio-text">默认</span>
        </label>
        <label class="radio-label">
          <input type="radio" v-model="settings.cipherFormat" value="space" class="menu-radio" />
          <span class="radio-text">空格分割</span>
        </label>
        <label class="radio-label">
          <input type="radio" v-model="settings.cipherFormat" value="first-upper" class="menu-radio" />
          <span class="radio-text">首字大写</span>
        </label>
        <label class="radio-label">
          <input type="radio" v-model="settings.cipherFormat" value="pascal" class="menu-radio" />
          <span class="radio-text">大驼峰</span>
        </label>
        <label class="radio-label">
          <input type="radio" v-model="settings.cipherFormat" value="camel" class="menu-radio" />
          <span class="radio-text">小驼峰</span>
        </label>
      </div>
    </div>
  </div>
</template>

<style scoped>
.settings-menu {
  position: absolute;
  top: calc(100% + 0.5rem);
  right: 0;
  background: var(--surface-color);
  border: 1px solid var(--border-color);
  border-radius: 0.75rem;
  padding: 0.5rem;
  min-width: 140px;
  box-shadow: var(--shadow-md);
  animation: fadeIn 0.15s ease-out;
  z-index: 100;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-4px); }
  to { opacity: 1; transform: translateY(0); }
}

.menu-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  cursor: pointer;
  border-radius: 0.5rem;
  transition: var(--transition);
}

.menu-label:active { background: var(--bg-color); }

@media (hover: hover) {
  .menu-label:hover { background: var(--bg-color); }
}

.menu-separator {
  height: 1px;
  background-color: var(--border-color);
  margin: 0.5rem 0;
}

.menu-group-title {
  font-size: 0.75rem;
  font-weight: 500;
  color: var(--text-secondary);
  padding: 0.5rem 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.radio-group {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  padding: 0 0.75rem 0.5rem;
}

.radio-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.25rem 0;
  cursor: pointer;
}

.radio-text {
  font-size: 0.875rem;
  color: var(--text-primary);
}

.menu-text {
  font-size: 0.875rem;
  color: var(--text-primary);
}

.menu-checkbox,
.menu-radio {
  accent-color: var(--accent-color);
}
</style>
