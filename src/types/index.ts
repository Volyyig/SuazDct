/** 共享类型定义 */

/** 密文输出格式 */
export type CipherFormat = 'space' | '4-letter' | 'first-upper' | 'pascal' | 'camel';

/** 页面类型 */
export type PageType = 'single' | 'sentence';

/** 主题类型 */
export type ThemeType = 'light' | 'dark';

/** 应用设置 */
export interface Settings {
  /** 启用繁体转换 */
  traditionalEnabled: boolean;
  /** 密文格式 */
  cipherFormat: CipherFormat;
}

/** 历史状态快照（用于撤销/重做） */
export interface HistoryState {
  plain: string;
  cipher: string;
}
