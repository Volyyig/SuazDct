"""
为v8a构建apk，复制apk到dist-apk并修改名字
"""

import json
import subprocess
import os
import shutil

# --- 配置区 ---
APP_NAME = "SuazDct"
TARGET_ARCH = "aarch64"
# 如果你配置了签名，请把这里的 -unsigned 删掉
SOURCE_FILENAME = "app-universal-release.apk"
# 回退版本号
FALLBACK_VERSION = "0.0.0"
# 输出目录（当前脚本所在目录下）
OUTPUT_FOLDER = "dist-apk"

def build():
    # 1. 获取版本号
    try:
        with open("package.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            version = data.get("version", FALLBACK_VERSION)
    except FileNotFoundError:
        print("[-] 错误: 找不到 package.json")
        version = FALLBACK_VERSION

    print(f">>> 正在构建 {APP_NAME} v{version} 为 {TARGET_ARCH} 架构...")

    # 2. 执行 Tauri 构建命令
    # shell=True 在 Windows 上是必须的，以便识别 pnpm 命令
    build_cmd = f"pnpm tauri android build --target {TARGET_ARCH}"
    
    try:
        # check=True 会在命令失败时抛出异常
        subprocess.run(build_cmd, shell=True, check=True)
    except subprocess.CalledProcessError:
        print("\n[-] 编译失败，请检查上方日志。")
        return

    # 3. 确定路径
    # 使用 os.path.join 自动处理 Windows/Linux 的斜杠差异
    apk_dir = os.path.join("src-tauri", "gen", "android", "app", "build", "outputs", "apk", "universal", "release")
    source_path = os.path.join(apk_dir, SOURCE_FILENAME)
    target_name = f"{APP_NAME}-v{version}-android-arm64.apk"

    # 4. 移动并重命名
    if os.path.exists(source_path):
        # 如果目标文件已存在，先删除
        if os.path.exists(target_name):
            os.remove(target_name)
        
        if not os.path.exists(OUTPUT_FOLDER):
            os.makedirs(OUTPUT_FOLDER)
        shutil.copy(source_path, os.path.join(OUTPUT_FOLDER, target_name))
        
        print("\n" + "="*30)
        print("[√] 构建成功！")
        print(f"[i] 最终产物: {os.path.abspath(os.path.join(OUTPUT_FOLDER, target_name))}")
        print("="*30)
        
        # 自动打开输出目录（可选）
        # os.startfile(os.getcwd()) 
    else:
        print(f"\n[-] 错误: 找不到生成的 APK 文件: {source_path}")
        print("    请确认 Tauri 是否生成了带 -unsigned 后缀的文件，或者你的签名配置是否有误。")

if __name__ == "__main__":
    build()
    