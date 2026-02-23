/** 设置与主题管理组合式函数 */
import { ref, watch } from 'vue';
import type { Settings, ThemeType, PageType } from '../types';

/** 默认设置 */
const DEFAULT_SETTINGS: Settings = {
    traditionalEnabled: true,
    cipherFormat: 'space',
};

export function useSettings() {
    const theme = ref<ThemeType>('dark');
    const settings = ref<Settings>({ ...DEFAULT_SETTINGS });
    const currentPage = ref<PageType>('single');

    /** 切换亮暗主题 */
    const toggleTheme = () => {
        theme.value = theme.value === 'light' ? 'dark' : 'light';
        localStorage.setItem('theme', theme.value);
        document.documentElement.setAttribute('data-theme', theme.value);
    };

    // 持久化 settings
    watch(settings, (v) => {
        localStorage.setItem('settings', JSON.stringify(v));
    }, { deep: true });

    // 持久化 currentPage
    watch(currentPage, (v) => {
        localStorage.setItem('currentPage', v);
    });

    /** 从 localStorage 恢复设置（在 onMounted 中调用） */
    const initSettings = () => {
        // 主题
        const savedTheme = localStorage.getItem('theme') as ThemeType | null;
        if (savedTheme) {
            theme.value = savedTheme;
        } else if (window.matchMedia('(prefers-color-scheme: light)').matches) {
            theme.value = 'light';
        }
        document.documentElement.setAttribute('data-theme', theme.value);

        // 设置
        const savedSettings = localStorage.getItem('settings');
        if (savedSettings) {
            try {
                const parsed = JSON.parse(savedSettings);
                settings.value = { ...DEFAULT_SETTINGS, ...parsed };
            } catch (e) {
                console.error('解析保存的设置失败', e);
            }
        }

        // 当前页面
        const savedPage = localStorage.getItem('currentPage') as PageType | null;
        if (savedPage) {
            currentPage.value = savedPage;
        }
    };

    return { theme, settings, currentPage, toggleTheme, initSettings };
}
