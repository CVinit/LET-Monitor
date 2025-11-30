#!/usr/bin/env python3
"""
IPv6 地址轮换工具
用于绕过 Cloudflare 检测
"""

import subprocess
import random
import logging
import sys

# ===== 配置你的 IPv6 地址池 =====
# IPv6 地址段: 2a0e:6a80:3:38d::/64
# 主 IP (SSH用，不轮换): 2a0e:6a80:3:38d::

# 运行 sudo bash setup_ipv6_pool.sh 后，将生成的地址列表粘贴到这里
# 或手动填写，格式如下：
IPV6_POOL = [
    '2a0e:6a80:3:38d::1',
    '2a0e:6a80:3:38d::2',
    '2a0e:6a80:3:38d::3',
    '2a0e:6a80:3:38d::4',
    '2a0e:6a80:3:38d::5',
    '2a0e:6a80:3:38d::6',
    '2a0e:6a80:3:38d::7',
    '2a0e:6a80:3:38d::8',
    '2a0e:6a80:3:38d::9',
    '2a0e:6a80:3:38d::a',
    '2a0e:6a80:3:38d::b',
    '2a0e:6a80:3:38d::c',
    '2a0e:6a80:3:38d::d',
    '2a0e:6a80:3:38d::e',
    '2a0e:6a80:3:38d::f',
    '2a0e:6a80:3:38d::10',
    '2a0e:6a80:3:38d::11',
    '2a0e:6a80:3:38d::12',
    '2a0e:6a80:3:38d::13',
    '2a0e:6a80:3:38d::14',
]

# 主 IP（SSH 连接用，不会被轮换）
MAIN_IP = '2a0e:6a80:3:38d::'

# 网卡名称（通常是 eth0, ens3 等）
INTERFACE = 'eth0'

# 网关地址（IPv6 默认网关，运行 ip -6 route 查看）
GATEWAY = 'fe80::1'  # 需要根据实际情况调整
# ===== 配置结束 =====

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def get_current_ipv6():
    """获取当前使用的 IPv6 地址"""
    try:
        result = subprocess.run(
            ['ip', '-6', 'route', 'show', 'default'],
            capture_output=True,
            text=True,
            check=True
        )
        # 解析输出获取当前源地址
        for line in result.stdout.split('\n'):
            if 'src' in line:
                parts = line.split('src')
                if len(parts) > 1:
                    current = parts[1].strip().split()[0]
                    return current
    except Exception as e:
        logging.error(f"获取当前 IPv6 失败: {e}")
    return None

def rotate_ipv6():
    """轮换到新的 IPv6 地址"""
    current = get_current_ipv6()
    logging.info(f"当前 IPv6 地址: {current}")
    
    # 从池中选择一个不同的地址（排除主 IP）
    available = [ip for ip in IPV6_POOL if ip != current and ip != MAIN_IP]
    
    if not available:
        logging.warning("没有可用的备用 IPv6 地址")
        return current
    
    selected = random.choice(available)
    logging.info(f"选择新的 IPv6 地址: {selected}")
    
    try:
        # 删除旧的默认路由
        subprocess.run(
            ['sudo', 'ip', '-6', 'route', 'del', 'default'],
            check=False  # 如果没有默认路由，不报错
        )
        
        # 添加新的默认路由，绑定到选择的 IPv6 地址
        subprocess.run([
            'sudo', 'ip', '-6', 'route', 'add', 'default',
            'via', GATEWAY,
            'dev', INTERFACE,
            'src', selected
        ], check=True)
        
        logging.info(f"✅ 成功切换到 IPv6: {selected}")
        logging.info(f"   (主 IP {MAIN_IP} 保持不变，用于 SSH)")
        return selected
        
    except subprocess.CalledProcessError as e:
        logging.error(f"❌ 切换 IPv6 失败: {e}")
        return None

def list_ipv6_addresses():
    """列出服务器上所有配置的 IPv6 地址"""
    try:
        result = subprocess.run(
            ['ip', '-6', 'addr', 'show'],
            capture_output=True,
            text=True,
            check=True
        )
        
        print("\n可用的 IPv6 地址:")
        print("=" * 60)
        
        for line in result.stdout.split('\n'):
            if 'inet6' in line and 'scope global' in line:
                # 提取 IPv6 地址
                parts = line.strip().split()
                if len(parts) >= 2:
                    addr = parts[1].split('/')[0]
                    print(f"  {addr}")
        
        print("=" * 60)
        print("\n请将这些地址添加到 ipv6_rotate.py 的 IPV6_POOL 中")
        
    except Exception as e:
        logging.error(f"列出 IPv6 地址失败: {e}")

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--list':
        # 列出所有可用的 IPv6 地址
        list_ipv6_addresses()
    else:
        # 执行轮换
        rotate_ipv6()
