<script setup lang="ts">
/** 单字加解密页面组件 */
import { ref, onMounted } from 'vue';
import type { Settings } from '../types';
import { encryptText, decryptText } from '../utils/cipher';

const props = defineProps<{
  settings: Settings;
}>();

const plain = ref('');
const cipher = ref('');
const error = ref('');
let oldPlain = '';

/** 处理原文输入 —— 加密单个汉字 */
async function onPlainInput(event?: Event) {
  error.value = '';
  if (!plain.value) {
    cipher.value = '';
    oldPlain = '';
    return;
  }

  const chars = [...plain.value];

  // 限制为 1 个字符
  if (chars.length > 1) {
    const e = event as InputEvent;
    if (e && e.data) {
      plain.value = [...e.data][0];
    } else {
      if (oldPlain && plain.value.includes(oldPlain)) {
        const added = plain.value.replace(oldPlain, '');
        plain.value = [...added][0] || chars[0];
      } else {
        plain.value = chars[0];
      }
    }
  }

  oldPlain = plain.value;

  try {
    const [formatted, _parts, processed] = await encryptText(
      plain.value,
      props.settings.traditionalEnabled,
      'space',
    );
    cipher.value = formatted;
    // 回显处理后的文字（如繁体转换结果）
    if (processed !== plain.value) {
      plain.value = processed;
      oldPlain = processed;
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
</script>

<template>
  <div class="page single-page">
    <div class="single-card">
      <div class="cipher-input-area">
        <input v-model="cipher" type="text" class="minimal-input cipher-text" placeholder="输入4字母密文" maxlength="4"
          @input="onCipherInput" @blur="onCipherBlur" />
      </div>

      <div class="big-char-area">
        <input v-model="plain" type="text" class="minimal-input big-char vffqsulc" placeholder="字" @input="onPlainInput"
          @blur="onPlainBlur" />
      </div>

      <div v-if="error" class="error-toast">{{ error }}</div>
    </div>
  </div>
</template>

<style scoped>
.single-page {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
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
</style>
