<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from "vue";
import { invoke } from "@tauri-apps/api/core";

const currentPage = ref<"single" | "sentence">("single");

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
  return currentPage.value === "single" ? "单字加解密" : "字句加解密";
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
  document.addEventListener('click', handleClickOutside);

  // 启动时随机显示一个字
  // 定义两个区域：[起始, 结束]
  const rangeA = [0x3400, 0x4DBF]; // 扩展 A 区 (6592 字)
  const rangeBasic = [0x4E00, 0x9FFF]; // 基本区 (20992 字)

  // 计算总的字符数量
  const countA = rangeA[1] - rangeA[0] + 1;
  const countBasic = rangeBasic[1] - rangeBasic[0] + 1;
  const totalCount = countA + countBasic;

  // 在总数范围内取一个随机索引
  const randomIndex = Math.floor(Math.random() * totalCount);

  let randomCodePoint;
  if (randomIndex < countA) {
    // 如果落在 A 区范围内
    randomCodePoint = rangeA[0] + randomIndex;
  } else {
    // 如果落在 基本区 范围内 (偏移掉 A 区的数量)
    randomCodePoint = rangeBasic[0] + (randomIndex - countA);
  }

  const randomChar = String.fromCodePoint(randomCodePoint);
  singlePlain.value = randomChar;
  onSinglePlainInput(); // 触发加密
});

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside);
});
</script>

<template>
  <div class="app">
    <!-- 顶部标题栏 -->
    <header class="top-bar">
      <h1 class="page-title">{{ pageTitle }}</h1>

      <!-- 设置按钮 -->
      <div class="settings-container" ref="settingsRef">
        <button type="button" class="settings-btn" @click.stop="showSettingsMenu = !showSettingsMenu" title="设置">
          ⚙️
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
    </header>

    <!-- 主内容区 -->
    <main class="content">
      <!-- 页面 1：单字加解密 -->
      <div v-if="currentPage === 'single'" class="page single-page">
        <!-- 密文输入区 (上方) -->
        <div class="cipher-input-area">
          <input v-model="singleCipher" type="text" class="bare-input cipher-text" placeholder="输入4字母密文" maxlength="4"
            @input="onSingleCipherInput" />
        </div>

        <!-- 大字输入区 (中心) -->
        <div class="big-char-area">
          <input v-model="singlePlain" type="text" class="bare-input big-char" placeholder="字" maxlength="1"
            @input="onSinglePlainInput" />
        </div>

        <!-- 错误提示 -->
        <div v-if="singleError" class="error">{{ singleError }}</div>
      </div>

      <!-- 页面 2：字句加解密 -->
      <div v-else class="page sentence-page">
        <div class="input-section">
          <!-- 原文区 -->
          <div class="section">
            <label class="label">原文</label>
            <div class="input-row">
              <textarea v-model="sentencePlain" class="textarea" placeholder="输入原文..." rows="5"
                @input="onSentencePlainInput" />
              <div class="side-btn-container">
                <button type="button" class="btn side-btn copy-btn" @click="copySentence(sentencePlain)">
                  复制
                </button>
                <button type="button" class="btn side-btn paste-btn" @click="pasteSentence('plain')">
                  粘贴
                </button>
              </div>

            </div>
          </div>

          <!-- 错误提示 -->
          <div v-if="sentenceError" class="error">{{ sentenceError }}</div>

          <!-- 密文区 -->
          <div class="section">
            <label class="label">密文</label>
            <div class="input-row">
              <textarea v-model="sentenceCipher" class="textarea" placeholder="输入密文..." rows="5"
                @input="onSentenceCipherInput" />
              <div class="side-btn-container">
                <button type="button" class="btn side-btn copy-btn" @click="copySentence(sentenceCipher)">
                  复制<br />
                </button>
                <button type="button" class="btn side-btn paste-btn" @click="pasteSentence('cipher')">
                  粘贴<br />
                </button>
              </div>

            </div>
          </div>
        </div>

        <div class="button-section">
          <!-- 悬浮清空按钮：位于右侧中间 -->
          <button type="button" class="btn fixed-clear-btn" @click="clearAll" title="清空全部内容">
            <span class="clear-icon">🧹</span>
            <span class="clear-text">清空</span>
          </button>
        </div>
      </div>
    </main>

    <!-- 底部导航 -->
    <nav class="bottom-nav">
      <button type="button" class="nav-btn" :class="{ active: currentPage === 'single' }"
        @click="currentPage = 'single'">
        <span class="nav-icon">🔤</span>
        <span class="nav-label">单字</span>
      </button>
      <button type="button" class="nav-btn" :class="{ active: currentPage === 'sentence' }"
        @click="currentPage = 'sentence'">
        <span class="nav-icon">📝</span>
        <span class="nav-label">字句</span>
      </button>
    </nav>
  </div>
</template>

<style scoped>
html,
body {
  width: 100%;
  height: 100%;
  margin: 0;
  background: #5500ff;
  -webkit-tap-highlight-color: transparent;
}

/* 全局禁止选中 (应用于非输入控件) */
.app,
.top-bar,
.bottom-nav,
.label,
.btn,
.page-title,
.menu-text {
  user-select: none;
  -webkit-user-select: none;
  -webkit-tap-highlight-color: transparent;
}

/* 全局布局 */
.app {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: linear-gradient(160deg, #1a0a2e 0%, #16213e 35%, #0f3460 70%, #1a0a2e 100%);
  overflow: hidden;
  color: #e0d4f7;
}

/* 顶部标题栏 */
.top-bar {
  flex-shrink: 0;
  padding: 1rem;
  padding-top: max(1rem, env(safe-area-inset-top));
  display: flex;
  justify-content: center;
  align-items: center;
  position: relative;
  background: rgba(88, 28, 135, 0.3);
  border-bottom: 1px solid rgba(167, 139, 250, 0.25);
}

.page-title {
  margin: 0;
  font-family: "JetBrains Mono", "Fira Code", ui-monospace, monospace;
  font-size: 1.5rem;
  font-weight: 700;
  color: #e0d4f7;
  letter-spacing: 0.05em;
  text-shadow: 0 0 20px rgba(167, 139, 250, 0.3);
}

/* 设置菜单 */
.settings-container {
  position: absolute;
  right: 1rem;
  top: calc(50% + env(safe-area-inset-top) / 2);
  transform: translateY(-50%);
}

.settings-btn {
  background: transparent;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 50%;
  transition: background 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  -webkit-tap-highlight-color: transparent;
}

.settings-btn:hover {
  background: rgba(167, 139, 250, 0.2);
}

.settings-menu {
  position: absolute;
  top: 120%;
  right: 0;
  background: rgba(15, 23, 42, 0.95);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(167, 139, 250, 0.3);
  border-radius: 0.75rem;
  min-width: 160px;
  z-index: 100;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3), 0 4px 6px -2px rgba(0, 0, 0, 0.1);
  padding: 0.5rem;
  animation: slideDown 0.2s ease-out;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.menu-item {
  padding: 0.25rem;
}

.menu-label {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  border-radius: 0.5rem;
  cursor: pointer;
  transition: background 0.2s;
  color: #e0d4f7;
  font-size: 0.95rem;
}

.menu-label:hover {
  background: rgba(139, 92, 246, 0.2);
}

.menu-checkbox {
  width: 1.1rem;
  height: 1.1rem;
  accent-color: #8b5cf6;
  cursor: pointer;
}

.menu-text {
  font-weight: 500;
}

/* 主内容区 */
.content {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 1rem;
}

.page {
  margin: 0 auto;
  height: 100%;
  display: flex;
  flex-direction: column;
}

/* 单字加解密页面 */
.single-page {
  justify-content: center;
  align-items: center;
  gap: 2rem;
}

.bare-input {
  background: transparent;
  border: none;
  text-align: center;
  color: #e0d4f7;
  font-family: inherit;
  width: 100%;
}

.bare-input:focus {
  outline: none;
}

.cipher-text {
  font-size: 2rem;
  font-family: "JetBrains Mono", "Fira Code", monospace;
  color: #a78bfa;
  letter-spacing: 0.1em;
}

.cipher-text::placeholder {
  color: rgba(167, 139, 250, 0.3);
  font-size: 1.5rem;
}

.big-char {
  font-size: 8rem;
  font-weight: 700;
  text-shadow: 0 0 40px rgba(167, 139, 250, 0.5);
  line-height: 1.2;
}

.big-char::placeholder {
  color: rgba(224, 212, 247, 0.2);
}

/* 字句加解密页面 */
.sentence-page {
  margin: 0 1.5rem 0 3rem;
  display: flex;
  flex-direction: row;
  gap: 0rem;
  position: relative;
  /* 为悬浮按钮提供定位基点 */
}

@media (max-width: 640px) {
  .sentence-page {
    margin: 0 1rem;
    display: flex;
    flex-direction: column;
    gap: 0rem;
    position: relative;
  }
}

.input-section {
  /* max-width: 32rem; */
  display: flex;
  flex-direction: column;
  flex: 1;
  gap: 1rem;
  border: whitesmoke solid 1px;
}

.button-section {
  min-width: 10%;   /* 设置最小宽度为10%，这里仅用于桌面 */
  min-height: 20%;  /* 设置最小高度为20%，这里仅用于移动 */
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  border: #047857 solid;
}

.side-btn-container {
  display: flex; 
  justify-content: center; 
  gap: 2rem;
}

/* 悬浮清空按钮样式 */
.fixed-clear-btn {
  position: absolute;
  right: -1.2rem;
  /* top: 50%; */

  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;

  width: 3.5rem;
  height: auto;
  min-height: 5rem;
  padding: 1.2rem 0.5rem;
  border-radius: 1.2rem;

  background: rgba(167, 139, 250, 0.08);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(167, 139, 250, 0.2);
  color: #c4b5fd;

  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
  transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  z-index: 10;
}

.fixed-clear-btn:hover {
  background: rgba(239, 68, 68, 0.15);
  border-color: rgba(239, 68, 68, 0.4);
  color: #fff;
  transform: scale(1.08);
  box-shadow: 0 12px 40px rgba(239, 68, 68, 0.25);
  right: -0.8rem;
}

.fixed-clear-btn:active {
  transform: scale(0.98);
}

.fixed-clear-btn .clear-icon {
  font-size: 1.4rem;
  filter: drop-shadow(0 0 8px rgba(239, 68, 68, 0.3));
}

.fixed-clear-btn:hover .clear-icon {
  transform: rotate(-15deg) scale(1.1);
}

.fixed-clear-btn .clear-text {
  font-size: 0.7rem;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  opacity: 0.8;
}

/* 窄屏适配 */
@media (max-width: 640px) {
  .fixed-clear-btn {
    right: -0.6rem;
    width: 2.6rem;
    min-height: 4.5rem;
    padding: 0.8rem 0.3rem;
    border-radius: 0.8rem;
  }

  .fixed-clear-btn:hover {
    right: -0.4rem;
  }

  .fixed-clear-btn .clear-icon {
    font-size: 1.1rem;
  }

  .fixed-clear-btn .clear-text {
    font-size: 0.6rem;
  }
}

.section {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.label {
  font-size: 0.9rem;
  font-weight: 600;
  color: #c4b5fd;
  margin-left: 0.25rem;
}

.textarea {
  flex: 1;
  min-width: 0;
  box-sizing: border-box;
  padding: 1rem;
  font-size: 1rem;
  font-family: inherit;
  color: #e0d4f7;
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(167, 139, 250, 0.35);
  border-radius: 0.75rem;
  resize: none;
}

.textarea:focus {
  outline: none;
  border-color: #8b5cf6;
  box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.2);
}

.input-row {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  align-items: stretch;
  min-height: 120px;
}

.btn {
  padding: 0.8rem 2rem;
  font-size: 1rem;
  font-weight: 600;
  color: #fff;
  border: none;
  border-radius: 2rem;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  -webkit-tap-highlight-color: transparent;
}

.side-btn {
  width: 3.5rem;
  flex-shrink: 0;
  padding: 0.5rem;
  border-radius: 0.75rem;
  font-size: 0.85rem;
  text-align: center;
  line-height: 1.2;
}

.btn:active {
  transform: scale(0.96);
}

.copy-btn {
  background: linear-gradient(135deg, #7c3aed, #6d28d9);
}

.copy-btn:hover {
  background: linear-gradient(135deg, #8b5cf6, #7c3aed);
  box-shadow: 0 4px 15px rgba(124, 58, 237, 0.5);
}

.paste-btn {
  background: linear-gradient(135deg, #059669, #047857);
  /* 用绿色区分解密 */
}

.paste-btn:hover {
  background: linear-gradient(135deg, #10b981, #059669);
  box-shadow: 0 4px 15px rgba(16, 185, 129, 0.5);
}

/* 错误提示 */
.error {
  padding: 0.8rem;
  font-size: 0.9rem;
  color: #fca5a5;
  background: rgba(185, 28, 28, 0.2);
  border: 1px solid rgba(248, 113, 113, 0.4);
  border-radius: 0.5rem;
  text-align: center;
}

/* 底部导航 */
.bottom-nav {
  flex-shrink: 0;
  display: flex;
  background: rgba(88, 28, 135, 0.3);
  border-top: 1px solid rgba(167, 139, 250, 0.25);
  padding: 0.5rem;
  padding-bottom: max(0.5rem, env(safe-area-inset-bottom));
  gap: 0.5rem;
}

.nav-btn {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.25rem;
  padding: 0.75rem 0.5rem;
  background: transparent;
  border: none;
  border-radius: 0.5rem;
  cursor: pointer;
  transition: all 0.2s;
  color: #c4b5fd;
  -webkit-tap-highlight-color: transparent;
}

.nav-btn:hover {
  background: rgba(88, 28, 135, 0.5);
}

.nav-btn.active {
  background: rgba(124, 58, 237, 0.3);
  color: #e0d4f7;
}

.nav-icon {
  font-size: 1.5rem;
}

.nav-label {
  font-size: 0.85rem;
  font-weight: 500;
}

/* 移动端适配 */
@media (max-width: 640px) {
  .big-char {
    font-size: 6rem;
  }

  .cipher-text {
    font-size: 1.6rem;
  }
}

@media (max-height: 600px) {
  .big-char {
    font-size: 5rem;
  }
}
</style>

<style>
/* 全局重置 */
html,
body,
#app {
  margin: 0;
  padding: 0;
  height: 100vh;
  overflow: hidden;
}
</style>
