#!/bin/bash
# 系统级配置脚本 - 强制使用 IPv6
# 适用于 Debian 11 服务器

echo "==================================="
echo "强制 IPv6 配置脚本"
echo "==================================="
echo ""

# 检查是否 root
if [ "$EUID" -ne 0 ]; then 
    echo "错误: 需要 root 权限"
    echo "请使用: sudo bash $0"
    exit 1
fi

echo "当前配置:"
echo "  IPv4 地址:"
ip -4 addr show | grep "inet " | grep -v "127.0.0.1"
echo ""
echo "  IPv6 地址:"
ip -6 addr show | grep "inet6" | grep "scope global" | head -5
echo ""

# 方案选择
echo "请选择配置方案:"
echo ""
echo "1. /etc/gai.conf 优先级调整（推荐）⭐"
echo "   - 不禁用 IPv4，只提高 IPv6 优先级"
echo "   - SSH 和其他服务不受影响"
echo "   - 需要重启网络或系统"
echo ""
echo "2. 禁用 IPv4 默认路由（激进）"
echo "   - 完全禁用 IPv4 出站"
echo "   - 可能影响部分服务"
echo "   - 如果 SSH 通过 IPv4 会断开！"
echo ""
echo "3. 仅测试（不修改）"
echo ""
read -p "请选择 (1/2/3): " choice

case $choice in
    1)
        echo ""
        echo "=== 配置方案 1: /etc/gai.conf 优先级调整 ==="
        echo ""
        
        # 备份配置
        if [ -f /etc/gai.conf ]; then
            cp /etc/gai.conf /etc/gai.conf.backup
            echo "✓ 已备份 /etc/gai.conf"
        fi
        
        # 创建新配置
        cat > /etc/gai.conf << 'EOF'
# Configuration for getaddrinfo(3).
# 优先使用 IPv6

# IPv4 addresses - 低优先级
precedence ::ffff:0:0/96  10

# IPv6 addresses - 高优先级
precedence 2000::/3       40

# 默认标签
label ::1/128       0
label ::/0          1
label 2002::/16     2
label ::/96         3
label ::ffff:0:0/96 4
EOF

        echo "✓ 已配置 /etc/gai.conf"
        echo ""
        echo "配置已完成！需要重启网络服务或系统："
        echo ""
        echo "  选项 A: 重启网络（推荐）"
        echo "    sudo systemctl restart networking"
        echo ""
        echo "  选项 B: 重启系统"
        echo "    sudo reboot"
        echo ""
        
        read -p "是否立即重启网络服务？(y/N) " restart
        if [[ $restart =~ ^[Yy]$ ]]; then
            systemctl restart networking
            echo "✓ 网络服务已重启"
        fi
        ;;
        
    2)
        echo ""
        echo "=== 配置方案 2: 禁用 IPv4 默认路由 ==="
        echo ""
        echo "⚠️  警告: 如果你的 SSH 通过 IPv4 连接，执行后会断开！"
        echo "⚠️  建议在本地控制台或 tmux/screen 中运行"
        echo ""
        read -p "确认继续？输入 'yes' 继续: " confirm
        
        if [ "$confirm" != "yes" ]; then
            echo "已取消"
            exit 1
        fi
        
        echo "正在禁用 IPv4 默认路由..."
        
        # 删除 IPv4 默认路由
        ip -4 route del default 2>/dev/null
        
        echo "✓ IPv4 默认路由已删除"
        echo ""
        echo "测试 IPv6:"
        curl -6 -s https://api64.ipify.org
        echo ""
        
        # 询问是否永久配置
        read -p "是否创建永久配置？(y/N) " permanent
        if [[ $permanent =~ ^[Yy]$ ]]; then
            cat > /etc/network/if-up.d/disable-ipv4-route << 'EOFSCRIPT'
#!/bin/bash
# 禁用 IPv4 默认路由
ip -4 route del default 2>/dev/null
exit 0
EOFSCRIPT
            chmod +x /etc/network/if-up.d/disable-ipv4-route
            echo "✓ 已创建永久配置脚本"
        fi
        ;;
        
    3)
        echo ""
        echo "=== 测试模式 ==="
        echo ""
        
        echo "测试 IPv4 连接:"
        if curl -4 -s -m 5 https://api.ipify.org; then
            echo " - IPv4 可用"
        else
            echo " - IPv4 不可用"
        fi
        
        echo ""
        echo "测试 IPv6 连接:"
        if curl -6 -s -m 5 https://api64.ipify.org; then
            echo " - IPv6 可用"
        else
            echo " - IPv6 不可用"
        fi
        
        echo ""
        echo "DNS 解析测试 (lowendtalk.com):"
        host lowendtalk.com
        echo ""
        echo "未做任何修改"
        ;;
        
    *)
        echo "无效选择"
        exit 1
        ;;
esac

echo ""
echo "==================================="
echo "配置完成"
echo "==================================="
