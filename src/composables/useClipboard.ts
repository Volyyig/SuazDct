/** 剪贴板操作组合式函数 */
import { readText, writeText } from '@tauri-apps/plugin-clipboard-manager';

export function useClipboard() {
    /**
     * 复制文本到剪贴板
     * @returns 是否成功
     */
    const copy = async (text: string): Promise<boolean> => {
        if (!text) return false;
        try {
            await writeText(text);
            return true;
        } catch {
            return false;
        }
    };

    /**
     * 从剪贴板读取文本
     * @returns 读取到的文本，失败时返回 null
     */
    const paste = async (): Promise<string | null> => {
        try {
            return await readText();
        } catch {
            return null;
        }
    };

    return { copy, paste };
}
