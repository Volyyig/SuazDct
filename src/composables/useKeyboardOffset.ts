/** 移动端键盘偏移量组合式函数 */
import { ref, onMounted, onUnmounted, type Ref } from 'vue';

/**
 * 从 ref 中解析出实际的 DOM 元素。
 * 当 ref 绑定在 Vue 组件上时，值为组件实例（含 `$el` 属性），
 * 需要通过 `$el` 获取底层 DOM 元素。
 */
function resolveElement(refValue: any): HTMLElement | null {
    if (!refValue) return null;
    // 组件实例：通过 $el 获取根 DOM 元素
    if (refValue.$el) return refValue.$el as HTMLElement;
    // 原生 DOM 元素
    if (refValue instanceof HTMLElement) return refValue;
    return null;
}

/**
 * 监听 Visual Viewport 变化，计算键盘弹起时的偏移量
 * @param navBarRef 底部导航栏引用（支持原生元素或 Vue 组件实例）
 */
export function useKeyboardOffset(navBarRef: Ref<any>) {
    const keyboardOffset = ref(0);

    const update = () => {
        if (window.visualViewport) {
            const totalOffset = window.innerHeight - window.visualViewport.height;
            const navEl = resolveElement(navBarRef.value);
            const navHeight = navEl?.offsetHeight || 0;
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
