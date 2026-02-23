/// 窗口管理 Tauri 命令
use tauri::Manager;

/// 桌面端显示主窗口
///
/// 应用启动时窗口默认隐藏（`visible: false`），
/// 前端加载完成后调用此命令显示窗口，避免白屏闪烁。
#[tauri::command]
pub fn release_window(app: tauri::AppHandle) {
    #[cfg(not(mobile))]
    if let Some(window) = app.get_webview_window("main") {
        let _ = window.show();
    }
}
