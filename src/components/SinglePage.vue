<script setup lang="ts">
/** 单字加解密页面组件 */
import { ref, onMounted } from 'vue';
import { openUrl } from '@tauri-apps/plugin-opener';
import type { Settings } from '../types';
import { encryptText, decryptText } from '../utils/cipher';
import { useToast } from '../composables/useToast';
import ToastFeedback from './ToastFeedback.vue';

const props = defineProps<{
  settings: Settings;
  keyboardOffset: number;
}>();

const plain = ref('');
const cipher = ref('');
const error = ref('');
let oldPlain = '';

const { showToast, toastMessage, toastVisible, toastType } = useToast();

/** 处理原文输入 —— 加密单个汉字 */
async function onPlainInput(event?: Event) {
  error.value = '';
  if (!plain.value) {
    cipher.value = '';
    oldPlain = '';
    return;
  }

  const chars = [...plain.value];
  let newText = plain.value;

  // 如果字符数 > 1，提取新输入的部分，用于包含上下文的繁体转换
  if (chars.length > 1) {
    const e = event as InputEvent;
    if (e && e.data) {
      newText = e.data;
    } else {
      if (oldPlain && plain.value.includes(oldPlain)) {
        newText = plain.value.replace(oldPlain, '');
      }
    }
    if (!newText) {
      newText = chars.join('');
    }
    // 视觉上先截断为取到的第一个字（临时）
    plain.value = [...newText][0] || chars[0];
  }

  oldPlain = plain.value;

  try {
    // 1. 将包含上下文（如“发行”/“发型”）的完整新输入传给后端计算
    const [_formatted, partsFull, processedFull] = await encryptText(
      newText,
      props.settings.traditionalEnabled,
      false, // 触发式分词，单字模式不启用
      'space',
    );

    // 2. 取后端带上下文转换后的第一个字（如“發” / “髮”）
    const finalChar = [...processedFull][0] || plain.value;

    // 3. 从 partsFull 提取该单字的密文，无需二次调用后端接口
    const isChinese = /[\u4E00-\u9FFF\u3400-\u4DBF\uF900-\uFAFF]/.test(finalChar);
    const finalCipher = isChinese ? (partsFull[0] || finalChar) : finalChar;

    cipher.value = finalCipher;
    // 回显处理后的文字
    if (finalChar !== plain.value) {
      plain.value = finalChar;
      oldPlain = finalChar;
    }
  } catch (e) {
    error.value = String(e);
  }
}

/** 处理密文输入 —— 解密 4 字母密码 */
async function onCipherInput() {
  error.value = '';
  if (!cipher.value) return;

  // 仅允许小写字母
  const clean = cipher.value.replace(/[^a-z]/g, '');
  if (clean !== cipher.value) {
    cipher.value = clean;
  }

  // 满 4 个字符时尝试解密
  if (clean.length >= 4) {
    try {
      const decrypted = await decryptText(clean.substring(0, 4));
      plain.value = decrypted;
      oldPlain = decrypted;
    } catch {
      // 解密失败静默处理，可能是输入中
    }
  }
}

/** 密文输入框失去焦点时，若字符数不足 4，则重新加密当前明文以恢复密文 */
function onCipherBlur() {
  if (cipher.value.length < 4) {
    onPlainInput();
  }
}

function generateRandomChar() {
  const rangeA = [0x3400, 0x4dbf];
  const rangeBasic = [0x4e00, 0x9fff];
  const countA = rangeA[1] - rangeA[0] + 1;
  const countBasic = rangeBasic[1] - rangeBasic[0] + 1;
  const totalCount = countA + countBasic;
  const randomIndex = Math.floor(Math.random() * totalCount);

  const randomCodePoint = randomIndex < countA
    ? rangeA[0] + randomIndex
    : rangeBasic[0] + (randomIndex - countA);

  plain.value = String.fromCodePoint(randomCodePoint);
  onPlainInput();
}

/** 启动时随机显示一个 CJK 汉字 */
onMounted(() => {
  generateRandomChar();
});

/** 输入框失去焦点时，如果为空则随机生成一个字 */
function onPlainBlur() {
  if (!plain.value) {
    generateRandomChar();
  }
}

/** 打开字统网查询 */
async function openZiTools() {
  if (!plain.value) return;
  const url = `https://zi.tools/zi/${encodeURIComponent(plain.value)}`;
  try {
    await openUrl(url);
  } catch (e) {
    showToast('无法打开浏览器: ' + String(e), 'error');
  }
}
</script>

<template>
  <div class="page single-page">
    <div class="single-card">
      <div class="cipher-input-area">
        <input v-model="cipher" type="text" class="minimal-input cipher-text" placeholder="输入4字母密文" maxlength="4"
          @input="onCipherInput" @blur="onCipherBlur" @keydown.ctrl.q.exact.prevent="cipher = ''; onCipherInput()"
          @keydown.meta.q.exact.prevent="cipher = ''; onCipherInput()" />
      </div>

      <div class="big-char-area">
        <input v-model="plain" type="text" class="minimal-input big-char vffqsulc" placeholder="字" @input="onPlainInput"
          @blur="onPlainBlur" @keydown.ctrl.q.exact.prevent="plain = ''; onPlainInput()"
          @keydown.meta.q.exact.prevent="plain = ''; onPlainInput()" />
      </div>

      <div v-if="error" class="error-toast">{{ error }}</div>

      <!-- 字典查询按钮 -->
      <button type="button" class="floating-dict-btn" @click="openZiTools" @mousedown.prevent title="在字统网查询"
        :class="{ disabled: !plain }" :style="{ transform: `translateY(-${keyboardOffset}px)` }" tabindex="-1">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none"
          stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="11" cy="11" r="8" />
          <path d="m21 21-4.3-4.3" />
        </svg>
      </button>
    </div>

    <!-- 页面级 Toast -->
    <ToastFeedback :message="toastMessage" :visible="toastVisible" :type="toastType" :keyboard-offset="keyboardOffset" />
  </div>
</template>

<style scoped>
.single-page {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
  align-items: center;
  padding-top: 15vh;
  position: relative;
}

.single-card {
  width: 100%;
  max-width: 320px;
  padding: 2.5rem;
  background: var(--surface-color);
  border: 1px solid var(--border-color);
  border-radius: 1.5rem;
  box-shadow: var(--shadow-md);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2rem;
}

.minimal-input {
  background: transparent;
  border: none;
  text-align: center;
  color: var(--text-primary);
  width: 100%;
}

.minimal-input:focus {
  outline: none;
}

.cipher-text {
  font-family: 'JetBrains Mono', monospace;
  font-size: 1.5rem;
  letter-spacing: 0.25rem;
  color: var(--accent-color);
}

.big-char {
  font-size: 10rem;
  font-weight: 200;
  line-height: 1;
  transition: var(--transition);
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

@media (max-width: 640px) {
  .big-char {
    font-size: 8rem;
  }

  .single-card {
    padding: 1.5rem;
  }
}

@media (max-height: 700px) {
  .big-char {
    font-size: 6rem;
  }

  .single-card {
    gap: 1rem;
    padding: 1.5rem;
  }
}

.floating-dict-btn {
  position: fixed;
  bottom: calc(5.5rem + env(safe-area-inset-bottom));
  right: 1.5rem;
  width: 3.5rem;
  height: 3.5rem;
  border-radius: 50%;
  background: #8b5cf6;
  color: white;
  border: none;
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.4);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: var(--transition);
  z-index: 100;
}

@media (hover: hover) {
  .floating-dict-btn:hover:not(.disabled) {
    background: #7c3aed;
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(139, 92, 246, 0.5);
  }
}

.floating-dict-btn:active:not(.disabled) {
  transform: translateY(-2px) scale(0.95);
  background: #7c3aed;
  box-shadow: 0 6px 16px rgba(139, 92, 246, 0.5);
}

.floating-dict-btn.disabled {
  background: var(--border-color);
  color: var(--text-secondary);
  cursor: not-allowed;
  box-shadow: none;
  opacity: 0.7;
}
</style>
