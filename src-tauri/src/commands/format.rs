/// 密文格式化 Tauri 命令
///
/// 提供独立的格式化接口，前端切换格式时可直接调用，无需重新加密。
use crate::utils::cipher_format::format_cipher as format_cipher_impl;

/// 将密文部件数组按指定格式重新格式化
///
/// # 参数
/// - `parts` - 密文部件列表
/// - `format` - 目标格式（`"space"` | `"4-letter"` | `"first-upper"` | `"pascal"` | `"camel"`）
#[tauri::command]
pub fn format_cipher(parts: Vec<String>, format: &str) -> Result<String, String> {
    Ok(format_cipher_impl(&parts, format))
}
