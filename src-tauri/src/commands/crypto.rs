/// 加密与解密 Tauri 命令
use hanconv::s2t;
use uniaz::UniAz;

use crate::utils::chinese::is_chinese;
use crate::utils::cipher_format::{format_cipher, preprocess_cipher};

/// 加密文本
///
/// # 参数
/// - `plain` - 明文文本
/// - `use_traditional` - 是否启用繁体转换
/// - `format` - 密文输出格式（`"space"` | `"4-letter"` | `"first-upper"` | `"pascal"` | `"camel"`）
///
/// # 返回
/// `(格式化密文, 原始部件列表, 处理后的原文)` 三元组
#[tauri::command]
pub fn encrypt_text(
    plain: &str,
    use_traditional: bool,
    format: &str,
) -> Result<(String, Vec<String>, String), String> {
    let uni_az = UniAz::new();

    // 如果启用繁体，先将简体转换为繁体
    let text_to_encrypt = if use_traditional {
        s2t(plain)
    } else {
        plain.to_string()
    };

    let mut parts = Vec::new();
    let mut non_chinese_buffer = String::new();

    for c in text_to_encrypt.chars() {
        if is_chinese(c) {
            // 先刷新非中文缓冲区
            if !non_chinese_buffer.is_empty() {
                parts.push(non_chinese_buffer.clone());
                non_chinese_buffer.clear();
            }
            parts.push(uni_az.encrypt(c));
        } else {
            non_chinese_buffer.push(c);
        }
    }

    // 处理最后的剩余非中文字符
    if !non_chinese_buffer.is_empty() {
        parts.push(non_chinese_buffer);
    }

    // 在后端直接格式化密文
    let formatted = format_cipher(&parts, format);

    // 返回 (格式化密文, 原始部件列表, 处理后的原文)
    Ok((formatted, parts, text_to_encrypt))
}

/// 解密文本
///
/// 接受原始密文字符串，在后端完成预处理后解密。
///
/// # 参数
/// - `cipher` - 原始密文字符串（支持各种格式）
#[tauri::command]
pub fn decrypt_text(cipher: &str) -> Result<String, String> {
    let uni_az = UniAz::new();

    // 在后端预处理密文为标准化部件数组
    let parts = preprocess_cipher(cipher);

    let mut result = String::new();

    for part in &parts {
        if part.is_empty() {
            continue;
        }

        // 尝试作为密文解密（UniAz 密文通常是 4 位小写字母组合）
        if part.len() == 4 && part.chars().all(|c| c.is_ascii_lowercase()) {
            match uni_az.decrypt(part) {
                Ok(ch) => result.push(ch),
                Err(_) => {
                    // 符合格式但解密失败（库未找到对应字符），作为原文保留
                    result.push_str(part);
                }
            }
        } else {
            // 直接作为原文拼接
            result.push_str(part);
        }
    }

    Ok(result)
}
