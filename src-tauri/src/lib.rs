/// SuazDct — 中文字符 UniAZ 加解密应用
///
/// 模块结构：
/// - `commands` — Tauri 命令（加解密、格式化、窗口管理）
/// - `utils` — 工具函数（中文字符判断、密文格式化/预处理）
mod commands;
mod utils;

use commands::crypto::{decrypt_text, encrypt_text};
use commands::format::format_cipher;
use commands::window::release_window;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_clipboard_manager::init())
        .plugin(tauri_plugin_opener::init())
        .invoke_handler(tauri::generate_handler![
            encrypt_text,
            decrypt_text,
            format_cipher,
            release_window
        ])
        .run(tauri::generate_context!())
        .expect("启动 Tauri 应用时出错");
}
