/// 密文格式化与预处理工具
///
/// 从前端 TypeScript 迁移至 Rust，避免前端执行计算密集型字符串处理。

/// 将密文部件数组按指定格式拼接成最终密文字符串。
///
/// # 参数
/// - `parts` - 密文部件列表（每个部件为 4 字母密码或非中文原文）
/// - `format` - 格式类型：`"space"` | `"4-letter"` | `"first-upper"` | `"pascal"` | `"camel"`
pub fn format_cipher(parts: &[String], format: &str) -> String {
    if format == "space" {
        return parts.join(" ");
    }

    let mut result = String::new();
    let mut is_new_word = true;

    for part in parts {
        let is_code = part.len() == 4 && part.chars().all(|c| c.is_ascii_lowercase());

        if is_code {
            let formatted = match format {
                "first-upper" => {
                    if is_new_word {
                        capitalize_first(part)
                    } else {
                        part.clone()
                    }
                }
                "pascal" => capitalize_first(part),
                "camel" => {
                    if !is_new_word {
                        capitalize_first(part)
                    } else {
                        part.clone()
                    }
                }
                // "4-letter" 或其他：直接拼接
                _ => part.clone(),
            };
            result.push_str(&formatted);
            is_new_word = false;
        } else {
            result.push_str(part);
            // 碰到空白字符时重置单词标志
            if part.chars().any(|c| c.is_whitespace()) {
                is_new_word = true;
            }
        }
    }

    result
}

/// 将密文文本预处理为标准化的部件数组（用于解密）。
///
/// 支持各种密文格式的反解析：空格分隔、大驼峰、小驼峰、首字大写等。
pub fn preprocess_cipher(input: &str) -> Vec<String> {
    if input.is_empty() {
        return Vec::new();
    }

    let mut result: Vec<String> = Vec::new();

    // 按 (字母段 | 非字母段) 分割
    let mut chars = input.chars().peekable();
    let mut segments: Vec<String> = Vec::new();
    let mut current = String::new();
    let mut current_is_alpha = false;

    while let Some(&c) = chars.peek() {
        let is_alpha = c.is_ascii_alphabetic();
        if current.is_empty() {
            current_is_alpha = is_alpha;
            current.push(c);
            chars.next();
        } else if is_alpha == current_is_alpha {
            current.push(c);
            chars.next();
        } else {
            segments.push(current.clone());
            current.clear();
            current_is_alpha = is_alpha;
            current.push(c);
            chars.next();
        }
    }
    if !current.is_empty() {
        segments.push(current);
    }

    for segment in &segments {
        if segment.chars().all(|c| c.is_ascii_alphabetic()) && !segment.is_empty() {
            // 纯字母段，尝试按 4 字符密码块拆分
            if try_split_codes(segment, &mut result) {
                continue;
            }
            // 无法按密码块拆分，作为原文保留
            result.push(segment.clone());
        } else {
            result.push(segment.clone());
        }
    }

    result
}

/// 尝试将纯字母字符串按 4 字符一组拆分为密码块。
///
/// 成功则将所有块（转小写）追加到 `out` 并返回 `true`；
/// 失败（长度不是 4 的倍数，且不含大驼峰模式）则返回 `false`。
fn try_split_codes(word: &str, out: &mut Vec<String>) -> bool {
    let len = word.len();
    // 检查是否长度为 4 的倍数，或者包含大驼峰模式（大写开头 + 3 个小写）
    let has_pascal = word
        .as_bytes()
        .windows(4)
        .any(|w| w[0].is_ascii_uppercase() && w[1..].iter().all(|b| b.is_ascii_lowercase()));

    if len % 4 != 0 && !has_pascal {
        return false;
    }

    let mut i = 0;
    let mut temp: Vec<String> = Vec::new();

    while i < len {
        if i + 4 <= len {
            let chunk = &word[i..i + 4];
            if chunk.bytes().all(|b| b.is_ascii_alphabetic()) {
                temp.push(chunk.to_ascii_lowercase());
                i += 4;
            } else {
                return false;
            }
        } else {
            // 剩余不足 4 个字符
            return false;
        }
    }

    if !temp.is_empty() {
        out.extend(temp);
        true
    } else {
        false
    }
}

/// 将字符串首字母大写
fn capitalize_first(s: &str) -> String {
    let mut chars = s.chars();
    match chars.next() {
        None => String::new(),
        Some(c) => {
            let mut result = String::with_capacity(s.len());
            result.extend(c.to_uppercase());
            result.push_str(chars.as_str());
            result
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_format_space() {
        let parts = vec!["abcd".to_string(), " ".to_string(), "efgh".to_string()];
        assert_eq!(format_cipher(&parts, "space"), "abcd   efgh");
    }

    #[test]
    fn test_format_4letter() {
        let parts = vec!["abcd".to_string(), "efgh".to_string()];
        assert_eq!(format_cipher(&parts, "4-letter"), "abcdefgh");
    }

    #[test]
    fn test_format_pascal() {
        let parts = vec!["abcd".to_string(), "efgh".to_string()];
        assert_eq!(format_cipher(&parts, "pascal"), "AbcdEfgh");
    }

    #[test]
    fn test_format_camel() {
        let parts = vec!["abcd".to_string(), "efgh".to_string()];
        assert_eq!(format_cipher(&parts, "camel"), "abcdEfgh");
    }

    #[test]
    fn test_format_first_upper() {
        let parts = vec![
            "abcd".to_string(),
            "efgh".to_string(),
            " ".to_string(),
            "ijkl".to_string(),
        ];
        assert_eq!(format_cipher(&parts, "first-upper"), "Abcdefgh Ijkl");
    }

    #[test]
    fn test_preprocess_space_separated() {
        let result = preprocess_cipher("abcd efgh");
        assert_eq!(result, vec!["abcd", " ", "efgh"]);
    }

    #[test]
    fn test_preprocess_pascal() {
        let result = preprocess_cipher("AbcdEfgh");
        assert_eq!(result, vec!["abcd", "efgh"]);
    }

    #[test]
    fn test_preprocess_empty() {
        let result = preprocess_cipher("");
        assert!(result.is_empty());
    }
}
