<script setup lang="ts">
/** 字句加解密页面组件 */
import { ref, watch } from 'vue';
import type { Settings } from '../types';
import { encryptText, decryptText, formatCipher } from '../utils/cipher';
import { useHistory } from '../composables/useHistory';
import { useClipboard } from '../composables/useClipboard';
import { useToast } from '../composables/useToast';
import ToastFeedback from './ToastFeedback.vue';

const props = defineProps<{
  settings: Settings;
  keyboardOffset: number;
}>();

const { showToast, toastMessage, toastVisible } = useToast();

const plain = ref('');
const cipher = ref('');
const error = ref('');

// 缓存当前密文部件列表，用于格式切换时避免重新加密
let cachedParts: string[] = [];

const { saveHistory, undo, redo, canUndo, canRedo } = useHistory();
const { copy, paste } = useClipboard();

// 自动触发计时器
let timer: number | null = null;

/** 加密字句 */
async function encrypt() {
  error.value = '';
  if (!plain.value.trim()) return;

  try {
    const [formatted, parts, processed] = await encryptText(
      plain.value,
      props.settings.traditionalEnabled,
      props.settings.cipherFormat,
    );
    cipher.value = formatted;
    cachedParts = parts;
    plain.value = processed; // 回显繁体
    saveHistory({ plain: plain.value, cipher: cipher.value });
  } catch (e) {
    error.value = String(e);
  }
}

/** 解密字句 */
async function decrypt() {
  error.value = '';
  if (!cipher.value.trim()) return;

  try {
    const decrypted = await decryptText(cipher.value);
    plain.value = decrypted;
    saveHistory({ plain: plain.value, cipher: cipher.value });
  } catch (e) {
    error.value = String(e);
  }
}

/** 原文输入事件（防抖触发加密） */
function onPlainInput() {
  if (!plain.value.trim()) {
    cipher.value = '';
    return;
  }
  if (timer) clearTimeout(timer);
  timer = window.setTimeout(encrypt, 100);
}

/** 密文输入事件（防抖触发解密） */
function onCipherInput() {
  if (!cipher.value.trim()) return;
  if (timer) clearTimeout(timer);
  timer = window.setTimeout(decrypt, 100);
}

/** 清空全部 */
function clearAll() {
  plain.value = '';
  cipher.value = '';
  error.value = '';
  cachedParts = [];
  saveHistory({ plain: '', cipher: '' });
  showToast('已清空');
}

/** 撤销 */
function handleUndo() {
  if (timer) clearTimeout(timer);
  const state = undo();
  if (state) {
    plain.value = state.plain;
    cipher.value = state.cipher;
    showToast('已撤销');
  }
}

/** 重做 */
function handleRedo() {
  if (timer) clearTimeout(timer);
  const state = redo();
  if (state) {
    plain.value = state.plain;
    cipher.value = state.cipher;
    showToast('已重做');
  }
}

/** 复制文本 */
async function handleCopy(text: string) {
  if (!text) return;
  const ok = await copy(text);
  showToast(ok ? '已复制' : '复制失败');
}

/** 粘贴文本 */
async function handlePaste(type: 'plain' | 'cipher') {
  const text = await paste();
  if (text === null) {
    error.value = '粘贴失败';
    return;
  }
  if (type === 'plain') {
    plain.value += text;
    onPlainInput();
  } else {
    cipher.value += text;
    onCipherInput();
  }
  showToast('已粘贴');
}

// 监听密文格式变化 —— 使用缓存部件直接格式化，无需重新加密
watch(() => props.settings.cipherFormat, async (newFormat) => {
  if (cachedParts.length > 0) {
    try {
      cipher.value = await formatCipher(cachedParts, newFormat);
    } catch {
      // 回退：重新加密
      if (plain.value) await encrypt();
    }
  }
});

// 初始化历史
saveHistory({ plain: '', cipher: '' });
</script>

<template>
  <div class="page sentence-page">
    <div class="sentence-container">
      <!-- 原文区 -->
      <div class="card">
        <div class="card-header">
          <span class="card-title">原文</span>
          <div class="card-actions">
            <button @click="handleUndo" :disabled="!canUndo()" class="text-btn"
              :class="{ disabled: !canUndo() }">撤销</button>
            <button @click="handleRedo" :disabled="!canRedo()" class="text-btn"
              :class="{ disabled: !canRedo() }">重做</button>
            <button @click="handleCopy(plain)" class="text-btn">复制</button>
            <button @click="handlePaste('plain')" class="text-btn">粘贴</button>
          </div>
        </div>
        <textarea v-model="plain" class="pure-textarea" placeholder="输入原文..." rows="4" @input="onPlainInput" />
      </div>

      <!-- 密文区 -->
      <div class="card">
        <div class="card-header">
          <span class="card-title">密文</span>
          <div class="card-actions">
            <button @click="handleUndo" :disabled="!canUndo()" class="text-btn"
              :class="{ disabled: !canUndo() }">撤销</button>
            <button @click="handleRedo" :disabled="!canRedo()" class="text-btn"
              :class="{ disabled: !canRedo() }">重做</button>
            <button @click="handleCopy(cipher)" class="text-btn">复制</button>
            <button @click="handlePaste('cipher')" class="text-btn">粘贴</button>
          </div>
        </div>
        <textarea v-model="cipher" class="pure-textarea" placeholder="输入密文..." rows="4" @input="onCipherInput" />
      </div>

      <div v-if="error" class="error-toast">{{ error }}</div>

      <!-- 清空按钮 -->
      <button type="button" class="floating-clear-btn" @click="clearAll" @mousedown.prevent title="清空全部"
        :style="{ transform: `translateY(-${keyboardOffset}px)` }">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none"
          stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M3 6h18m-2 0v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6m3 0V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2m-6 9l4-4m0 4l-4-4" />
        </svg>
      </button>
    </div>

    <!-- 页面级 Toast -->
    <ToastFeedback :message="toastMessage" :visible="toastVisible" :keyboard-offset="keyboardOffset" />
  </div>
</template>

<style scoped>
.sentence-page {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.sentence-container {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  position: relative;
}

.card {
  background: var(--surface-color);
  border: 1px solid var(--border-color);
  border-radius: 1rem;
  padding: 1rem;
  box-shadow: var(--shadow-sm);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.card-title {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05rem;
}

.card-actions {
  display: flex;
  gap: 0.5rem;
}

.pure-textarea {
  width: 100%;
  background: transparent;
  border: none;
  resize: none;
  color: var(--text-primary);
  font-size: 1rem;
  line-height: 1.6;
  padding: 0;
}

.pure-textarea:focus {
  outline: none;
}

.text-btn {
  background: transparent;
  border: none;
  color: var(--accent-color);
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
  transition: var(--transition);
}

.text-btn:active {
  background: var(--bg-color);
  color: var(--accent-hover);
  opacity: 0.7;
}

@media (hover: hover) {
  .text-btn:hover:not(:disabled) {
    background: var(--bg-color);
    color: var(--accent-hover);
  }
}

.text-btn.disabled,
.text-btn:disabled {
  color: var(--text-secondary);
  opacity: 0.4;
  cursor: not-allowed;
}

.floating-clear-btn {
  position: fixed;
  bottom: calc(5.5rem + env(safe-area-inset-bottom));
  right: 1.5rem;
  width: 3.5rem;
  height: 3.5rem;
  border-radius: 50%;
  background: var(--accent-color);
  color: white;
  border: none;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: var(--transition);
  z-index: 100;
}

@media (hover: hover) {
  .floating-clear-btn:hover {
    background: var(--accent-hover);
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(99, 102, 241, 0.5);
  }
}

.floating-clear-btn:active {
  transform: translateY(-2px) scale(0.95);
  background: var(--accent-hover);
  box-shadow: 0 6px 16px rgba(99, 102, 241, 0.5);
}

.error-toast {
  margin-top: 1rem;
  padding: 0.75rem 1rem;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.2);
  border-radius: 0.5rem;
  color: var(--error-color);
  font-size: 0.875rem;
  text-align: center;
}

.error-toast {
  margin-top: 1rem;
  padding: 0.75rem 1rem;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.2);
  border-radius: 0.5rem;
  color: var(--error-color);
  font-size: 0.875rem;
  text-align: center;
}
</style>
