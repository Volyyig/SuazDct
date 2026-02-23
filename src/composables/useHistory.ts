/** 撤销/重做历史管理组合式函数 */
import { ref } from 'vue';
import type { HistoryState } from '../types';

/** 最大历史记录条数 */
const MAX_HISTORY = 50;

export function useHistory() {
    const history = ref<HistoryState[]>([]);
    const historyIndex = ref(-1);
    let isUndoingRedoing = false;

    /** 保存当前状态到历史栈 */
    const saveHistory = (state: HistoryState) => {
        if (isUndoingRedoing) return;

        const lastState = history.value[historyIndex.value];

        // 状态未变则不保存
        if (lastState && lastState.plain === state.plain && lastState.cipher === state.cipher) {
            return;
        }

        // 在中间位置做了新改动，切断后面的 redo 链
        if (historyIndex.value < history.value.length - 1) {
            history.value = history.value.slice(0, historyIndex.value + 1);
        }

        history.value.push({ ...state });
        if (history.value.length > MAX_HISTORY) {
            history.value.shift();
        } else {
            historyIndex.value++;
        }
    };

    /** 撤销，返回恢复后的状态；无可撤销时返回 null */
    const undo = (): HistoryState | null => {
        if (historyIndex.value <= 0) return null;
        isUndoingRedoing = true;
        historyIndex.value--;
        const state = history.value[historyIndex.value];
        setTimeout(() => { isUndoingRedoing = false; }, 200);
        return { ...state };
    };

    /** 重做，返回恢复后的状态；无可重做时返回 null */
    const redo = (): HistoryState | null => {
        if (historyIndex.value >= history.value.length - 1) return null;
        isUndoingRedoing = true;
        historyIndex.value++;
        const state = history.value[historyIndex.value];
        setTimeout(() => { isUndoingRedoing = false; }, 200);
        return { ...state };
    };

    /** 是否可撤销 */
    const canUndo = () => historyIndex.value > 0;
    /** 是否可重做 */
    const canRedo = () => historyIndex.value < history.value.length - 1;

    return { history, historyIndex, saveHistory, undo, redo, canUndo, canRedo };
}
