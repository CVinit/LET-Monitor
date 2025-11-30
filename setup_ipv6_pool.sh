#!/bin/bash
# IPv6 地址批量配置脚本
# 为 eth0 接口添加多个 IPv6 地址用于轮换

# 配置参数
IPV6_PREFIX="2a0e:6a80:3:38d"  # 你的 IPv6 前缀
INTERFACE="eth0"                # 网卡名称
NUM_ADDRESSES=20                # 要添加的地址数量（建议10-50）

# 主 IP（用于 SSH，不会被轮换使用）
MAIN_IP="${IPV6_PREFIX}::"

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}IPv6 地址批量配置工具${NC}"
echo -e "${GREEN}================================${NC}\n"

echo "配置信息:"
echo "  前缀: ${IPV6_PREFIX}::/64"
echo "  接口: ${INTERFACE}"
echo "  主IP: ${MAIN_IP} (SSH 连接用，不轮换)"
echo "  添加地址数: ${NUM_ADDRESSES}"
echo ""

# 检查是否 root 权限
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}错误: 需要 root 权限${NC}"
    echo "请使用: sudo $0"
    exit 1
fi

# 检查网卡是否存在
if ! ip link show ${INTERFACE} > /dev/null 2>&1; then
    echo -e "${RED}错误: 网卡 ${INTERFACE} 不存在${NC}"
    echo "可用网卡:"
    ip link show | grep -E '^[0-9]+:' | awk '{print $2}' | sed 's/://g'
    exit 1
fi

echo -e "${YELLOW}开始添加 IPv6 地址...${NC}\n"

# 记录成功添加的地址
SUCCESS_COUNT=0
ADDED_IPS=()

# 生成随机的 IPv6 地址后缀（使用简单递增，避免冲突）
for i in $(seq 1 $NUM_ADDRESSES); do
    # 生成地址：使用简单的递增模式
    # 从 ::1 开始（::0 是主IP）
    IPV6_ADDR="${IPV6_PREFIX}::${i}"
    
    # 跳过主 IP
    if [ "${IPV6_ADDR}" == "${MAIN_IP}" ]; then
        continue
    fi
    
    # 检查地址是否已存在
    if ip -6 addr show dev ${INTERFACE} | grep -q "${IPV6_ADDR}"; then
        echo -e "${YELLOW}⊙ ${IPV6_ADDR} 已存在${NC}"
        ADDED_IPS+=("${IPV6_ADDR}")
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
        continue
    fi
    
    # 添加 IPv6 地址
    if ip -6 addr add ${IPV6_ADDR}/64 dev ${INTERFACE}; then
        echo -e "${GREEN}✓ 已添加: ${IPV6_ADDR}${NC}"
        ADDED_IPS+=("${IPV6_ADDR}")
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    else
        echo -e "${RED}✗ 添加失败: ${IPV6_ADDR}${NC}"
    fi
done

echo ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}配置完成！${NC}"
echo -e "${GREEN}================================${NC}"
echo "成功添加: ${SUCCESS_COUNT} 个地址"
echo ""

# 生成 Python 配置
echo "正在生成 ipv6_rotate.py 配置..."

cat > /tmp/ipv6_pool.txt << EOF
# 自动生成的 IPv6 地址池
# 主 IP (SSH 用): ${MAIN_IP}
# 以下地址可用于轮换:

IPV6_POOL = [
EOF

for ip in "${ADDED_IPS[@]}"; do
    echo "    '${ip}'," >> /tmp/ipv6_pool.txt
done

echo "]" >> /tmp/ipv6_pool.txt

echo ""
echo -e "${GREEN}已生成配置文件: /tmp/ipv6_pool.txt${NC}"
echo ""
echo "请将以下内容复制到 ipv6_rotate.py 的 IPV6_POOL 中:"
echo -e "${YELLOW}================================${NC}"
cat /tmp/ipv6_pool.txt
echo -e "${YELLOW}================================${NC}"
echo ""

# 验证配置
echo "验证当前接口上的 IPv6 地址:"
echo -e "${YELLOW}--------------------------------${NC}"
ip -6 addr show dev ${INTERFACE} | grep "inet6" | grep "scope global" | head -10
echo -e "${YELLOW}--------------------------------${NC}"
echo ""

# 保存配置脚本
SCRIPT_PATH="/etc/network/if-up.d/ipv6-addresses"
echo "是否创建开机自动配置脚本？(y/N)"
read -r REPLY

if [[ $REPLY =~ ^[Yy]$ ]]; then
    cat > ${SCRIPT_PATH} << 'EOFSCRIPT'
#!/bin/bash
# IPv6 地址自动配置
# 开机时自动添加 IPv6 地址

INTERFACE="eth0"
IPV6_PREFIX="2a0e:6a80:3:38d"
NUM_ADDRESSES=20

for i in $(seq 1 $NUM_ADDRESSES); do
    IPV6_ADDR="${IPV6_PREFIX}::${i}"
    ip -6 addr add ${IPV6_ADDR}/64 dev ${INTERFACE} 2>/dev/null
done

logger "IPv6 addresses configured on ${INTERFACE}"
EOFSCRIPT

    chmod +x ${SCRIPT_PATH}
    echo -e "${GREEN}✓ 已创建开机自动配置脚本: ${SCRIPT_PATH}${NC}"
fi

echo ""
echo -e "${GREEN}全部完成！${NC}"
echo ""
echo "下一步:"
echo "  1. 编辑 ipv6_rotate.py，使用生成的 IPV6_POOL"
echo "  2. 测试轮换: python3 ipv6_rotate.py"
echo "  3. 运行监控: ./run_with_xvfb.sh 245"
