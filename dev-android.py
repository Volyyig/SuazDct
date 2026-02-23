"""
Tauri Android 开发脚本

问题：
    TUN开启时，Tauri android dev 默认使用 虚拟网卡IP 作为 host，导致无法在局域网中调试。

解决方案：
    1. 自动检测局域网 IP
    2. 自动设置端口转发
    3. 自动启动 Tauri Android 开发模式

"""


"""
关于在 Tauri Android 中实现 Dev包和Release包共存 的问题

目前状态：
    放弃，退回到 Tauri 原版方案即 pnpm tauri android dev
    仅保留: 
        1. 对 Dev包 app_name 的修改
        2. 对 IP 的适配

曾尝试方案：
1. 仅修改包名(即加.dev后缀)实现共存
    缺陷：
        Tauri的 adb调试 和 自动开启 依旧指向原包名的应用；若手机未安装原包名的应用，则报错

2. 手动构建安卓调试步骤
    pnpm dev → tauri android build --debug → adb install → adb reverse → adb shell am start
    
    缺陷：
        1. 流程略慢
        2. 无法热重载

"""


import socket
import subprocess
import os
import re
import sys

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
        pass

    # 过滤掉明显的 IP 前缀 (双重保险)
    virtual_prefixes = (
        '127.',
        '169.254.',
        '172.17.',
        '172.18.',
        '172.19.',
        '172.20.',
        '172.21.',
        '172.22.',
        '172.23.',
        '172.24.',
        '172.25.',
        '172.26.',
        '172.27.',
        '172.28.',
        '172.29.',
        '172.30.',
        '172.31.',
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

def run_dev():
    ip = get_lan_ip()
    
    if ip == "0.0.0.0":
        print("[-] 错误: 无法确定有效的 IP 地址，请检查网络连接。")
        sys.exit(1)

    print(f"\n[√] 最终选用 IP: {ip}")
    print(">>> 正在启动 Tauri 安卓调试服务...")
    print(">>> 强制使用 --host 参数并设置 TAURI_DEV_HOST 环境变量以避开虚拟网卡干扰\n")

    # 设置环境变量，确保 Vite 和 Tauri 都能识别
    os.environ["TAURI_DEV_HOST"] = ip

    # 执行命令
    # 注意：Tauri v2 的 android dev 支持 --host 参数
    cmd = f"pnpm tauri android dev --host {ip}"
    
    try:
        # 使用 subprocess.run 保持交互性
        subprocess.run(cmd, shell=True)
    except KeyboardInterrupt:
        print("\n[i] 调试已由用户停止")
    except Exception as e:
        print(f"[-] 运行出错: {e}")

if __name__ == "__main__":
    run_dev()