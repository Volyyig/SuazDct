/** Tauri 后端调用封装 */
import { invoke } from '@tauri-apps/api/core';
import type { CipherFormat } from '../types';

/**
 * 加密文本
 * @param plain 明文
 * @param useTraditional 是否启用繁体
 * @param format 密文格式
 * @returns [格式化密文, 原始部件列表, 处理后的原文]
 */
export async function encryptText(
    plain: string,
    useTraditional: boolean,
    format: CipherFormat,
): Promise<[string, string[], string]> {
    return invoke<[string, string[], string]>('encrypt_text', {
        plain,
        useTraditional,
        format,
    });
}

/**
 * 解密文本
 * @param cipher 原始密文字符串（支持各种格式）
 */
export async function decryptText(cipher: string): Promise<string> {
    return invoke<string>('decrypt_text', { cipher });
}

/**
 * 格式化密文部件（无需重新加密）
 * @param parts 密文部件列表
 * @param format 目标格式
 */
export async function formatCipher(
    parts: string[],
    format: CipherFormat,
): Promise<string> {
    return invoke<string>('format_cipher', { parts, format });
}

/** 显示主窗口（桌面端） */
export async function releaseWindow(): Promise<void> {
    return invoke('release_window');
}
