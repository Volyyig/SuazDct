// UniAZ: 中文字符转为 a-z 表示，通过 Tauri 暴露加解密
use hanconv::s2t;
use tauri::Manager;
use uniaz::UniAz;

/// 检查字符是否为中文字符（CJK 统一汉字）
fn is_chinese(c: char) -> bool {
    matches!(c,
        '\u{4E00}'..='\u{9FFF}' |  // CJK 统一汉字
        '\u{3400}'..='\u{4DBF}' |  // CJK 扩展 A    TODO: 扩A一部分文字加密后为3个字母，暂未作处理
        '\u{F900}'..='\u{FAFF}'    // CJK 兼容汉字
    )
}

/// Control window display on Desktop
#[tauri::command]
fn release_window(app: tauri::AppHandle) {
    #[cfg(not(mobile))]
    if let Some(window) = app.get_webview_window("main") {
        let _ = window.show();
    }
}

#[tauri::command]
fn encrypt_text(plain: &str, use_traditional: bool) -> Result<(Vec<String>, String), String> {
    let uni_az = UniAz::new();

    // 如果启用繁体，先转换简体到繁体
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

    // 处理最后的剩余字符
    if !non_chinese_buffer.is_empty() {
        parts.push(non_chinese_buffer);
    }

    // 返回 (密文列表, 处理后的原文)
    Ok((parts, text_to_encrypt))
}

#[tauri::command]
fn decrypt_text(cipher_parts: Vec<String>) -> Result<String, String> {
    let uni_az = UniAz::new();
    let mut result = String::new();

    for part in cipher_parts {
        if part.is_empty() {
            continue;
        }

        // 尝试作为密文解密（UniAz 密文通常是固定长度的字母组合，如4位）
        // 如果长度不是4或者包含非字母，则很可能是原文直接保留的部分
        if part.len() == 4 && part.chars().all(|c| c.is_ascii_lowercase()) {
            match uni_az.decrypt(&part) {
                Ok(ch) => result.push(ch),
                Err(_) => {
                    // 如果虽然符合格式但解密失败（库没找到对应字符），也作为原文保留
                    result.push_str(&part);
                }
            }
        } else {
            // 直接作为原文拼接
            result.push_str(&part);
        }
    }
    Ok(result)
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_clipboard_manager::init())
        .plugin(tauri_plugin_opener::init())
        .invoke_handler(tauri::generate_handler![
            encrypt_text,
            decrypt_text,
            release_window
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
