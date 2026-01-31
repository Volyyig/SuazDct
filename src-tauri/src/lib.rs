// UniAZ: 中文字符转为 a-z 表示，通过 Tauri 暴露加解密
use hanconv::s2t;
use uniaz::UniAz;

/// 检查字符是否为中文字符（CJK 统一汉字）
fn is_chinese(c: char) -> bool {
    matches!(c,
        '\u{4E00}'..='\u{9FFF}' |  // CJK 统一汉字
        '\u{3400}'..='\u{4DBF}' |  // CJK 扩展 A
        '\u{F900}'..='\u{FAFF}'    // CJK 兼容汉字
    )
}

#[tauri::command]
fn encrypt_text(plain: &str, use_traditional: bool) -> Result<(String, String), String> {
    let uni_az = UniAz::new();

    // 如果启用繁体，先转换简体到繁体
    let text_to_encrypt = if use_traditional {
        s2t(plain)
    } else {
        plain.to_string()
    };

    let parts: Vec<String> = text_to_encrypt
        .chars()
        .map(|c| {
            if is_chinese(c) {
                uni_az.encrypt(c)
            } else {
                c.to_string()
            }
        })
        .collect();

    // 使用空格分隔（与新版 uniaz API 保持一致）
    // 返回 (密文, 处理后的原文)
    Ok((parts.join(" "), text_to_encrypt))
}

#[tauri::command]
fn decrypt_text(cipher: &str) -> Result<String, String> {
    let uni_az = UniAz::new();
    let mut result = String::new();
    for part in cipher.split(' ') {
        if part.is_empty() {
            continue;
        }
        // 尝试解密
        match uni_az.decrypt(part) {
            Ok(ch) => result.push(ch),
            Err(_) => {
                // 如果解密失败，可能是非加密的字符，尝试直接添加
                // 假设非加密部分是单字符
                if part.len() == 1 {
                    result.push_str(part);
                } else {
                    return Err(format!("解密失败：无效的密文段 '{}'", part));
                }
            }
        }
    }
    Ok(result)
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .invoke_handler(tauri::generate_handler![encrypt_text, decrypt_text])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
