/** Toast 反馈提示组合式函数 */
import { ref } from 'vue';

export function useToast() {
    const message = ref('');
    const visible = ref(false);
    let timer: ReturnType<typeof setTimeout> | null = null;

    /** 显示 Toast 提示，2 秒后自动消失 */
    const showToast = (msg: string) => {
        message.value = msg;
        visible.value = true;
        if (timer) clearTimeout(timer);
        timer = setTimeout(() => {
            visible.value = false;
        }, 2000);
    };

    return { toastMessage: message, toastVisible: visible, showToast };
}
