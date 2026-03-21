/** Toast 反馈提示组合式函数 */
import { ref } from 'vue';

export type ToastType = 'info' | 'error';

export function useToast() {
    const message = ref('');
    const visible = ref(false);
    const type = ref<ToastType>('info');
    let timer: ReturnType<typeof setTimeout> | null = null;

    /** 显示 Toast 提示，2 秒后自动消失 */
    const showToast = (msg: string, toastType: ToastType = 'info') => {
        message.value = msg;
        type.value = toastType;
        visible.value = true;
        if (timer) clearTimeout(timer);
        timer = setTimeout(() => {
            visible.value = false;
        }, 2000);
    };

    return { 
        toastMessage: message, 
        toastVisible: visible, 
        toastType: type,
        showToast 
    };
}
