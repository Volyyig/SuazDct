import { invoke } from '@tauri-apps/api/core';

/** 显示主窗口（桌面端） */
export async function releaseWindow(): Promise<void> {
    return invoke('release_window');
}