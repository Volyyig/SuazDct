/// 检查字符是否为中文字符（CJK 统一汉字）
pub fn is_chinese(c: char) -> bool {
    matches!(
        c,
        '\u{4E00}'..='\u{9FFF}'   // CJK 统一汉字
        | '\u{3400}'..='\u{4DBF}' // CJK 扩展 A（注：扩 A 部分文字加密后为 3 个字母，暂未处理）
        | '\u{F900}'..='\u{FAFF}' // CJK 兼容汉字
    )
}
