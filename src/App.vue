<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from "vue";
import { invoke } from "@tauri-apps/api/core";

const currentPage = ref<"single" | "sentence">("single");

// Theme management
const theme = ref<"light" | "dark">("dark");
const toggleTheme = () => {
  theme.value = theme.value === "light" ? "dark" : "light";
  localStorage.setItem("theme", theme.value);
  document.documentElement.setAttribute("data-theme", theme.value);
};

// 设置
const settings = ref({
  traditionalEnabled: true  // 默认启用繁体
});
const showSettingsMenu = ref(false);
const settingsRef = ref<HTMLElement | null>(null);

// 页面 1：单字加解密状态
const singlePlain = ref(""); // 大字输入
const singleCipher = ref(""); // 密文输入
const singleError = ref("");

// 页面 2：字句加解密状态
const sentencePlain = ref("");
const sentenceCipher = ref("");
const sentenceError = ref("");

// 计算属性：当前页面标题
const pageTitle = computed(() => {
  return currentPage.value === "single" ? "单字" : "字句";
});

// 监听单字输入（原文）
async function onSinglePlainInput() {
  singleError.value = "";
  if (!singlePlain.value) {
    singleCipher.value = "";
    return;
  }

  // 限制为1个字符
  if (singlePlain.value.length > 1) {
    singlePlain.value = singlePlain.value[0];
  }

  try {
    // 调用加密，获取 (密文, 处理后的原文)
    const [cipher, processed] = await invoke<[string, string]>("encrypt_text", {
      plain: singlePlain.value,
      useTraditional: settings.value.traditionalEnabled
    });

    singleCipher.value = cipher;
    // 更新原文为处理后的（如繁体）
    if (processed !== singlePlain.value) {
      singlePlain.value = processed;
    }
  } catch (e) {
    singleError.value = String(e);
  }
}

// 监听单字密文输入
async function onSingleCipherInput() {
  singleError.value = "";
  if (!singleCipher.value) {
    return; // 不清空原文，保留显示？或者也清空？按逻辑应该是清空
  }

  // 简单的正则检查，只允许 a-z
  const cleanCipher = singleCipher.value.replace(/[^a-z]/g, "");
  if (cleanCipher !== singleCipher.value) {
    singleCipher.value = cleanCipher;
  }

  // 当输入满4个字符时尝试解密
  if (cleanCipher.length >= 4) {
    try {
      // 截取前4个
      const toDecrypt = cleanCipher.substring(0, 4);
      const decrypted = await invoke<string>("decrypt_text", { cipher: toDecrypt });
      singlePlain.value = decrypted; // 解密出的字
    } catch (e) {
      // 解密失败暂不报错，可能是输入中
    }
  }
}

// 页面2：字句加密
async function encryptSentence() {
  sentenceError.value = "";
  if (!sentencePlain.value.trim()) return;

  try {
    const [cipher, processed] = await invoke<[string, string]>("encrypt_text", {
      plain: sentencePlain.value,
      useTraditional: settings.value.traditionalEnabled
    });
    sentenceCipher.value = cipher;
    sentencePlain.value = processed; // 回显繁体
  } catch (e) {
    sentenceError.value = String(e);
  }
}

// 页面2：字句解密
async function decryptSentence() {
  sentenceError.value = "";
  if (!sentenceCipher.value.trim()) return;

  try {
    // 自动分组逻辑
    const input = sentenceCipher.value;
    const processed = input.replace(/([a-z]+)/g, (match) => {
      if (match.length % 4 === 0 && match.length >= 4) {
        return match.match(/.{1,4}/g)?.join(" ") || match;
      }
      return match;
    });

    const decrypted = await invoke<string>("decrypt_text", { cipher: processed });
    sentencePlain.value = decrypted;
  } catch (e) {
    sentenceError.value = String(e);
  }
}

// 页面2：自动触发处理
let sentenceTimer: number | null = null;

function onSentencePlainInput() {
  if (!sentencePlain.value.trim()) {
    sentenceCipher.value = "";
    return;
  }
  if (sentenceTimer) clearTimeout(sentenceTimer);
  sentenceTimer = window.setTimeout(encryptSentence, 100);
}

function onSentenceCipherInput() {
  if (!sentenceCipher.value.trim()) {
    return;
  }
  if (sentenceTimer) clearTimeout(sentenceTimer);
  sentenceTimer = window.setTimeout(decryptSentence, 100);
}

function clearAll() {
  sentencePlain.value = "";
  sentenceCipher.value = "";
  sentenceError.value = "";
  singlePlain.value = "";
  singleCipher.value = "";
  singleError.value = "";
}

// 剪贴板功能
async function copySentence(text: string) {
  if (!text) return;
  try {
    await navigator.clipboard.writeText(text);
  } catch (e) {
    sentenceError.value = "复制失败";
  }
}

async function pasteSentence(type: 'plain' | 'cipher') {
  try {
    const text = await navigator.clipboard.readText();
    if (type === 'plain') {
      sentencePlain.value += text;
      onSentencePlainInput();
    } else {
      sentenceCipher.value += text;
      onSentenceCipherInput();
    }
  } catch (e) {
    sentenceError.value = "粘贴失败";
  }
}

// 点击外部关闭设置菜单
function handleClickOutside(event: MouseEvent) {
  if (settingsRef.value && !settingsRef.value.contains(event.target as Node)) {
    showSettingsMenu.value = false;
  }
}

onMounted(() => {
  // listen click outside
  document.addEventListener('click', handleClickOutside);

  // Initialize theme
  const savedTheme = localStorage.getItem("theme") as "light" | "dark" | null;
  if (savedTheme) {
    theme.value = savedTheme;
  } else if (window.matchMedia("(prefers-color-scheme: light)").matches) {
    theme.value = "light";
  }
  document.documentElement.setAttribute("data-theme", theme.value);

  // 启动时随机显示一个字
  const rangeA = [0x3400, 0x4DBF];
  const rangeBasic = [0x4E00, 0x9FFF];
  const countA = rangeA[1] - rangeA[0] + 1;
  const countBasic = rangeBasic[1] - rangeBasic[0] + 1;
  const totalCount = countA + countBasic;
  const randomIndex = Math.floor(Math.random() * totalCount);

  let randomCodePoint;
  if (randomIndex < countA) {
    randomCodePoint = rangeA[0] + randomIndex;
  } else {
    randomCodePoint = rangeBasic[0] + (randomIndex - countA);
  }

  const randomChar = String.fromCodePoint(randomCodePoint);
  singlePlain.value = randomChar;
  onSinglePlainInput();

  // invoke window
  invoke("release_window");
});

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside);
});
</script>

<template>
  <div class="app">
    <!-- 顶部标题栏 -->
    <header class="top-bar">
      <div class="top-bar-left">
        <h1 class="page-title">{{ pageTitle }}</h1>
      </div>

      <div class="top-bar-right">
        <!-- 切换主题按钮 -->
        <button type="button" class="icon-btn theme-toggle" @click="toggleTheme"
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
          <button type="button" class="icon-btn settings-btn" @click.stop="showSettingsMenu = !showSettingsMenu"
            title="设置">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none"
              stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="3" />
              <path
                d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
            </svg>
          </button>

          <!-- 设置菜单 -->
          <div v-if="showSettingsMenu" class="settings-menu">
            <div class="menu-item">
              <label class="menu-label">
                <input type="checkbox" v-model="settings.traditionalEnabled" class="menu-checkbox" />
                <span class="menu-text">繁体启用</span>
              </label>
            </div>
          </div>
        </div>
      </div>
    </header>

    <!-- 主内容区 -->
    <main class="content">
      <!-- 页面 1：单字加解密 -->
      <div v-show="currentPage === 'single'" class="page single-page">
        <div class="single-card">
          <div class="cipher-input-area">
            <input v-model="singleCipher" type="text" class="minimal-input cipher-text" placeholder="输入4字母密文"
              maxlength="4" @input="onSingleCipherInput" />
          </div>

          <div class="big-char-area">
            <input v-model="singlePlain" type="text" class="minimal-input big-char" placeholder="字" maxlength="1"
              @input="onSinglePlainInput" />
          </div>

          <div v-if="singleError" class="error-toast">{{ singleError }}</div>
        </div>
      </div>

      <!-- 页面 2：字句加解密 -->
      <div v-show="currentPage === 'sentence'" class="page sentence-page">
        <div class="sentence-container">
          <!-- 原文区 -->
          <div class="card">
            <div class="card-header">
              <span class="card-title">原文</span>
              <div class="card-actions">
                <button @click="copySentence(sentencePlain)" class="text-btn">复制</button>
                <button @click="pasteSentence('plain')" class="text-btn">粘贴</button>
              </div>
            </div>
            <textarea v-model="sentencePlain" class="pure-textarea" placeholder="输入原文..." rows="4"
              @input="onSentencePlainInput" />
          </div>

          <!-- 密文区 -->
          <div class="card">
            <div class="card-header">
              <span class="card-title">密文</span>
              <div class="card-actions">
                <button @click="copySentence(sentenceCipher)" class="text-btn">复制</button>
                <button @click="pasteSentence('cipher')" class="text-btn">粘贴</button>
              </div>
            </div>
            <textarea v-model="sentenceCipher" class="pure-textarea" placeholder="输入密文..." rows="4"
              @input="onSentenceCipherInput" />
          </div>

          <div v-if="sentenceError" class="error-toast">{{ sentenceError }}</div>

          <!-- 固定清空按钮 -->
          <button type="button" class="floating-clear-btn" @click="clearAll" title="清空全部">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none"
              stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path
                d="M3 6h18m-2 0v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6m3 0V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2m-6 9l4-4m0 4l-4-4" />
            </svg>
          </button>
        </div>
      </div>
    </main>

    <!-- 底部导航 -->
    <nav class="bottom-nav">
      <button type="button" class="nav-btn" :class="{ active: currentPage === 'single' }"
        @click="currentPage = 'single'">
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none"
          stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M4 7h16M4 12h16M4 17h16" />
        </svg>
        <span class="nav-label">单字</span>
      </button>
      <button type="button" class="nav-btn" :class="{ active: currentPage === 'sentence' }"
        @click="currentPage = 'sentence'">
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
  </div>
</template>

<style>
:root {
  /* Dark Theme (Default) */
  --bg-color: #0a0a0b;
  --surface-color: #161618;
  --border-color: #27272a;
  --text-primary: #f8fafc;
  --text-secondary: #94a3b8;
  --accent-color: #6366f1;
  --accent-hover: #818cf8;
  --error-color: #ef4444;
  --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
  --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
  --transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

[data-theme="light"] {
  --bg-color: #f8fafc;
  --surface-color: #ffffff;
  --border-color: #e2e8f0;
  --text-primary: #0f172a;
  --text-secondary: #64748b;
  --accent-color: #4f46e5;
  --accent-hover: #4338ca;
  --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
  --shadow-md: 0 10px 15px -3px rgb(0 0 0 / 0.1);
}

* {
  box-sizing: border-box;
  -webkit-tap-highlight-color: transparent;
  user-select: none;
}

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  background-color: var(--bg-color);
  color: var(--text-primary);
  transition: background-color 0.3s ease, color 0.3s ease;
  overflow: hidden;
}

.app {
  display: flex;
  flex-direction: column;
  height: 100vh;
  /* max-width: 600px; */
  margin: 0 auto;
  position: relative;
}

/* Header */
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

.icon-btn:hover {
  background-color: var(--bg-color);
  color: var(--text-primary);
  border-color: var(--border-color);
}

/* Content */
.content {
  flex: 1;
  overflow-y: auto;
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
}

.page {
  flex: 1;
  display: flex;
  flex-direction: column;
}

/* Single Page */
.single-page {
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
  font-family: "JetBrains Mono", monospace;
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

/* Sentence Page */
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

.text-btn:hover {
  background: var(--bg-color);
  color: var(--accent-hover);
}

/* Floating Clear */
.floating-clear-btn {
  position: fixed;
  bottom: 6rem;
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

.floating-clear-btn:hover {
  background: var(--accent-hover);
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(99, 102, 241, 0.5);
}

.floating-clear-btn:active {
  transform: scale(0.95);
}

/* Settings Menu */
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

/* Restore selection for inputs */
input,
textarea {
  user-select: text;
  -webkit-user-select: text;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-4px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
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

.menu-label:hover {
  background: var(--bg-color);
}

.menu-text {
  font-size: 0.875rem;
  color: var(--text-primary);
}

.menu-checkbox {
  accent-color: var(--accent-color);
}

/* Navigation */
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

.nav-btn:hover {
  color: var(--text-primary);
  background: var(--bg-color);
}

.nav-btn.active {
  color: var(--accent-color);
}

.nav-label {
  font-size: 0.75rem;
  font-weight: 500;
}

/* Error */
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

/* Responsive */
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
