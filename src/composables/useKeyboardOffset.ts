/** 移动端键盘偏移量组合式函数 */
import { ref, onMounted, onUnmounted, type Ref } from 'vue';

/**
 * 监听 Visual Viewport 变化，计算键盘弹起时的偏移量
 * @param navBarRef 底部导航栏元素引用（用于减去导航栏高度）
 */
export function useKeyboardOffset(navBarRef: Ref<HTMLElement | null>) {
    const keyboardOffset = ref(0);

    const update = () => {
        if (window.visualViewport) {
            const totalOffset = window.innerHeight - window.visualViewport.height;
            const navHeight = navBarRef.value?.offsetHeight || 0;
            keyboardOffset.value = Math.max(0, totalOffset - navHeight);
        }
    };

    onMounted(() => {
        if (window.visualViewport) {
            window.visualViewport.addEventListener('resize', update);
            window.visualViewport.addEventListener('scroll', update);
        }
    });

    onUnmounted(() => {
        if (window.visualViewport) {
            window.visualViewport.removeEventListener('resize', update);
            window.visualViewport.removeEventListener('scroll', update);
        }
    });

    return { keyboardOffset };
}
