import socket
import subprocess
import os
import re
import sys
import time
import signal
import atexit

# --- 全局进程追踪 ---
_tracked_processes: list[subprocess.Popen] = []
_cleanup_done = False


def _kill_process_tree(proc: subprocess.Popen):
    """在 Windows 上通过 taskkill 杀死整棵进程树"""
    if proc and proc.poll() is None:
        try:
            # /T = 杀死子进程树, /F = 强制终止
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            # Fallback: 尝试直接 terminate
            try:
                proc.terminate()
            except Exception:
                pass


def cleanup():
    """统一清理函数：杀死所有追踪的后台进程并恢复终端状态"""
    global _cleanup_done
    if _cleanup_done:
        return
    _cleanup_done = True

    print("\n>>> 正在清理后台进程...")
    for proc in reversed(_tracked_processes):
        if proc and proc.poll() is None:
            print(f"[+] 正在终止进程 PID={proc.pid}...")
            _kill_process_tree(proc)
    print("[√] 清理完成。")

    # 恢复 Windows 终端状态：
    # os.system('') 会重新初始化控制台的 VT 处理模式，
    # 修复被子进程破坏的终端输入状态（退格、Ctrl+C 等无法输入）
    try:
        os.system('')
    except Exception:
        pass


def _signal_handler(signum, frame):
    """信号处理器，确保 SIGTERM/SIGBREAK 也能执行清理"""
    cleanup()
    sys.exit(1)


# 注册清理钩子
atexit.register(cleanup)
signal.signal(signal.SIGTERM, _signal_handler)
if hasattr(signal, 'SIGBREAK'):
    # Windows 特有: 当控制台窗口关闭或 Ctrl+Break 时触发
    signal.signal(signal.SIGBREAK, _signal_handler)


def track_process(proc: subprocess.Popen) -> subprocess.Popen:
    """注册一个需要在退出时清理的子进程"""
    _tracked_processes.append(proc)
    return proc


def get_lan_ip():
    """
    获取局域网 IP，尝试排除虚拟网卡 (Docker, WSL, VPN 等)
    """
    print(">>> 正在检测局域网 IP...")

    # 尝试多种方式获取 IP，并进行过滤
    candidates = []

    # 方式 1: 通过 socket 连接外部地址获取主网卡 IP
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # 不一定要连通，只是为了让系统选择合适的本地地址
        s.connect(('8.8.8.8', 80))
        primary_ip = s.getsockname()[0]
        s.close()
        candidates.append(primary_ip)
    except Exception:
        pass

    # 方式 2: 解析 ipconfig 输出并按适配器过滤
    try:
        # 在 Windows 上解析 ipconfig
        output = subprocess.check_output('ipconfig', shell=True).decode('gbk', errors='ignore')

        # 将输出按适配器段落分割 (通常以空行+非空格字符开始)
        # 匹配模式：适配器名称行开始，直到下一个适配器名称行
        adapter_blocks = re.split(r'\r?\n(?=[^\s\r\n])', output)

        for block in adapter_blocks:
            # 检查是否是虚拟网卡
            is_virtual = any(keyword.lower() in block.lower() for keyword in [
                'VMware', 'VirtualBox', 'WSL', 'Docker', 'Hyper-V', 'Virtual'
            ])

            if is_virtual:
                continue

            # 提取该适配器段落中的 IPv4 地址
            ips = re.findall(r'IPv4 地址[ .:]+([\d\.]+)', block)
            for ip in ips:
                if ip not in candidates:
                    candidates.append(ip)
    except Exception as e:
        print(f"[!] 解析 ipconfig 时出错: {e}")

    # 过滤掉明显的 IP 前缀 (双重保险)
    virtual_prefixes = (
        '127.',
        '169.254.',
        '172.17.', '172.18.', '172.19.',
        '172.20.', '172.21.', '172.22.', '172.23.',
        '172.24.', '172.25.', '172.26.', '172.27.',
        '172.28.', '172.29.', '172.30.', '172.31.',
    )

    valid_ips = [ip for ip in candidates if not ip.startswith(virtual_prefixes)]

    # 优先级排序：192.168.x.x 通常是家用 Wi-Fi，最可能是手机能连通的
    valid_ips.sort(key=lambda x: not x.startswith('192.168.'))

    if not valid_ips:
        if candidates:
            print("[-] 未找到理想的物理网卡 IP，将使用第一个检测到的 IP。")
            return candidates[0]
        return "0.0.0.0"

    if len(valid_ips) > 1:
        print("[i] 检测到多个可能的物理网卡 IP:")
        for i, ip in enumerate(valid_ips):
            print(f"    {i+1}. {ip}")
        print(f"[+] 自动选择优先级最高的: {valid_ips[0]}")

    return valid_ips[0]


def run_command(command, check=True, capture_output=False):
    """ 运行一个命令并处理输出 """
    print(f"\n>>> 执行: {command}")
    try:
        result = subprocess.run(command, check=check, shell=True, text=True, capture_output=capture_output, encoding='utf-8')
        return result
    except subprocess.CalledProcessError as e:
        print(f"[-] 命令执行失败: {e}")
        if e.stdout:
            print(f"[stdout]:\n{e.stdout}")
        if e.stderr:
            print(f"[stderr]:\n{e.stderr}")
        return None
    except FileNotFoundError:
        # command is a string here, so we split it to get the command name
        cmd_name = command.split()[0]
        print(f"[-] 命令未找到: {cmd_name}。请确保相关工具已安装并加入 PATH。")
        return None


def get_adb_path():
    """ 从 ANDROID_HOME 环境变量中获取 adb 的完整路径 """
    android_home = os.environ.get("ANDROID_HOME")
    if not android_home:
        print("[-] 错误: 未找到 ANDROID_HOME 环境变量。请确保已正确配置安卓开发环境。")
        return None

    adb_path = os.path.join(android_home, "platform-tools", "adb.exe" if os.name == 'nt' else "adb")

    if not os.path.exists(adb_path):
        print(f"[-] 错误: 在 {adb_path} 未找到 adb。请检查 ANDROID_HOME 设置是否正确。")
        return None

    print(f"[+] 成功定位 adb: {adb_path}")
    return adb_path


def get_device_arch(adb_path):
    """ 获取连接设备的 CPU 架构并映射到 Rust 目标 """
    print("\n>>> 正在检测设备架构...")
    result = run_command(f'"{adb_path}" shell getprop ro.product.cpu.abi', capture_output=True)
    if not result or not result.stdout:
        print("[-] 无法获取设备架构，将使用默认构建目标。")
        return None

    abi = result.stdout.strip()
    print(f"[i] 设备 ABI: {abi}")

    arch_map = {
        "arm64-v8a": "aarch64",
        "armeabi-v7a": "armv7",
        "x86_64": "x86_64",
        "x86": "i686"
    }

    target = arch_map.get(abi)
    if target:
        print(f"[+] 映射到 Rust 目标: {target}")
    else:
        print(f"[-] 未知的 ABI: {abi}，将不指定特定目标。")

    return target


def run_dev():
    adb_path = get_adb_path()
    if not adb_path:
        sys.exit(1)

    ip = get_lan_ip()
    if ip == "0.0.0.0":
        print("[-] 错误: 无法确定有效的 IP 地址，请检查网络连接。")
        sys.exit(1)

    print(f"\n[√] 最终选用 IP: {ip}")

    try:
        # 1. 在后台启动 Vite 开发服务器 (使用列表参数, 避免 shell=True)
        print("\n>>> 步骤 1/8: 启动前端开发服务器...")
        dev_server_cmd = f"pnpm dev --host {ip}"
        dev_server_process = track_process(subprocess.Popen(
            dev_server_cmd, shell=True,
            # Windows 上 pnpm 是 .cmd 脚本，必须通过 shell 调用
            # 清理时通过 taskkill /F /T 杀死整棵进程树（包括 shell 子进程）
        ))
        print(f"[+] 前端服务已在后台启动 (PID: {dev_server_process.pid})。等待服务器就绪...")
        time.sleep(5)  # 等待 Vite 启动

        # 2. 获取设备架构
        target_arch = get_device_arch(adb_path)

        # 3. 构建调试版的 Android 应用
        print("\n>>> 步骤 3/8: 构建调试版 Android 应用...")
        build_cmd = "pnpm tauri android build --debug"
        if target_arch:
            build_cmd += f" --target {target_arch}"
        if not run_command(build_cmd):
            sys.exit(1)

        # 4. 安装调试包
        print("\n>>> 步骤 4/8: 安装调试版应用...")
        # 路径->实际存储路径 映射
        arch_path_map = {"aarch64": "arm64"}    # TODO: 其它架构待办
        arch_mapped = arch_path_map[target_arch]    # TODO: 未知问题：不论架构其构建包都位于universal
        apk_path = f"src-tauri/gen/android/app/build/outputs/apk/universal/debug/app-universal-debug.apk"
        if not run_command(f'"{adb_path}" install -r "{apk_path}"' ):
            print("[-] 请确保您的安卓设备已通过 USB 调试模式连接，并已授权。")
            sys.exit(1)

        # 5. 端口转发
        print("\n>>> 步骤 5/8: 设置端口转发...")
        run_command(f'"{adb_path}" reverse --remove-all', check=False)
        if not run_command(f'"{adb_path}" reverse tcp:1420 tcp:1420'):
            sys.exit(1)

        # 6. 启动开发包
        print("\n>>> 步骤 6/8: 启动开发版应用...")
        package_name = "com.entlst.suazdct.dev"
        activity_name = "com.entlst.suazdct.MainActivity"
        if not run_command(f'"{adb_path}" shell am start -n {package_name}/{activity_name}'):
            sys.exit(1)
        print(f"[+] 已启动应用: {package_name}")

        # 7. 获取应用的 PID
        print("\n>>> 步骤 7/8: 获取应用 PID...")
        time.sleep(2)  # 等待应用进程完全启动
        pid_result = run_command(f'"{adb_path}" shell pidof {package_name}', capture_output=True)

        app_pid = None
        if pid_result and pid_result.stdout:
            # pidof 在某些系统上可能返回多个 PID，取第一个
            app_pid = pid_result.stdout.strip().split()[0]

        # 8. 打印日志
        if app_pid and app_pid.isdigit():
            print(f"[+] 获取到应用 PID: {app_pid}")
            print("\n>>> 步骤 8/8: 实时显示应用日志 (按 Ctrl+C 停止)...")
            logcat_cmd = [adb_path, "logcat", f"--pid={app_pid}"]
        else:
            print("[-] 未能获取应用 PID，将回退到基于标签的日志过滤（可能不包含触摸事件）。")
            print("\n>>> 步骤 8/8: 实时显示应用日志 (按 Ctrl+C 停止)...")
            logcat_cmd = [adb_path, "logcat", "Tauri:V", "RustStdoutStderr:V", "Webview:D", "chromium:D", "*:S"]

        logcat_process = track_process(subprocess.Popen(logcat_cmd))
        logcat_process.wait()

    except KeyboardInterrupt:
        print("\n[i] 用户请求停止调试...")
    except Exception as e:
        print(f"\n[-] 发生错误: {e}")
    finally:
        # cleanup() 会通过 atexit 自动调用，但显式调用可以确保
        # 在 sys.exit() 之前就完成清理并打印信息
        cleanup()


if __name__ == "__main__":
    run_dev()
