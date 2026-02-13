import json
import os
import shutil
import subprocess
import platform

RUST_TARGET_NAME = "suazdct"     # Rust 生成的 exe 名称

APP_NAME = "SuazDct"
OTPUT_DIR = './output'
FALLBACK_VERSION = "0.0.0"

def build_and_rename():
    # 1. 读取 Tauri 配置获取名称和版本
    config_path = './src-tauri/tauri.conf.json'
    if not os.path.exists(config_path):
        print(f"❌ 错误: 找不到 {config_path}")
        return

    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
        
    product_name = APP_NAME
    version = config.get('version', FALLBACK_VERSION)

    # 2. 执行构建命令
    print(f"🚀 开始构建 {product_name} v{version}...")
    try:
        # 使用 shell=True 确保在 Windows 环境下能找到 pnpm
        subprocess.run(["pnpm", "tauri", "build"], check=True, shell=True)
    except subprocess.CalledProcessError:
        print("❌ 构建失败，请检查输出日志。")
        return

    # 3. 确定架构和平台信息
    system = platform.system().lower() # 'windows', 'linux', 'darwin'
    arch = platform.machine().lower()  # 'amd64' (x64), 'arm64'
    
    # 规范化命名
    os_name = "Win" if system == "windows" else system.capitalize()
    arch_name = "x64" if arch in ['amd64', 'x86_64'] else arch

    # 4. 定位原始 exe 路径 (Tauri 默认将 exe 放在这个位置)
    # 注意：Tauri 会将 productName 中的空格转为下划线或保持原样，取决于版本
    # 这里我们直接去 release 目录下找最新生成的 .exe
    release_dir = './src-tauri/target/release'
    original_exe = os.path.join(release_dir, f"{RUST_TARGET_NAME}.exe")
    
    # 如果找不到，尝试查找目录下的唯一 exe (防止 productName 不匹配)
    if not os.path.exists(original_exe):
        exes = [f for f in os.listdir(release_dir) if f.endswith('.exe') and 'bundle' not in f]
        if exes:
            original_exe = os.path.join(release_dir, exes[0])

    # 5. 生成新文件名并移动到输出目录
    if not os.path.exists(OTPUT_DIR):
        os.makedirs(OTPUT_DIR)

    new_filename = f"{product_name}_v{version}_{os_name}_{arch_name}_Portable.exe"
    target_path = os.path.join(OTPUT_DIR, new_filename)

    if os.path.exists(original_exe):
        shutil.copy2(original_exe, target_path)
        print("-" * 30)
        print("✅ 构建并提取成功！")
        print(f"文件位置: {target_path}")
        print("-" * 30)
    else:
        print(f"❌ 未能找到生成的二进制文件: {original_exe}")

if __name__ == "__main__":
    build_and_rename()