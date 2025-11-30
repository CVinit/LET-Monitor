#!/bin/bash
# 强制 Chrome 使用 IPv6 的方法

echo "=== 检查当前网络配置 ==="
echo ""

# 1. 检查默认路由
echo "1. 当前路由表:"
ip -6 route show
echo ""

# 2. 检查当前出口 IP
echo "2. 测试出口 IP:"
echo -n "IPv4: "
curl -4 -s https://api.ipify.org || echo "无法访问"
echo -n "IPv6: "
curl -6 -s https://api64.ipify.org || echo "无法访问"
echo ""

# 3. 检查 DNS 解析
echo "3. DNS 解析测试 (lowendtalk.com):"
host lowendtalk.com
echo ""

# 解决方案选项
echo "=== 解决方案 ==="
echo ""
echo "方案 A: 临时禁用 IPv4（推荐用于测试）"
echo "  sudo sysctl -w net.ipv6.conf.all.disable_ipv6=0"
echo "  sudo sysctl -w net.ipv4.conf.eth0.disable_ipv4=1  # 禁用 IPv4"
echo ""
echo "方案 B: 调整地址选择优先级"
echo "  编辑 /etc/gai.conf，取消注释并修改："
echo "  precedence ::ffff:0:0/96  10  # IPv4"
echo "  precedence 2000::/3       40  # IPv6"
echo ""
echo "方案 C: 使用 SOCKS5 代理强制 IPv6（最佳）"
echo "  安装: sudo apt install dante-server"
echo "  配置并在 Chrome 中使用 IPv6-only 代理"
echo ""

# 提供快速修复脚本
cat > /tmp/force_ipv6.sh << 'EOF'
#!/bin/bash
# 临时禁用 IPv4（仅用于测试，SSH 可能断开！）

echo "警告: 这将禁用 IPv4，可能导致 SSH 断开！"
echo "建议在本地控制台或 tmux/screen 中运行"
read -p "确认继续？(yes/no) " confirm

if [ "$confirm" != "yes" ]; then
    echo "已取消"
    exit 1
fi

# 禁用 IPv4
sudo sysctl -w net.ipv4.ip_forward=0
sudo ip -4 route del default

echo "IPv4 已禁用"
echo "测试 IPv6:"
curl -6 https://api64.ipify.org
EOF

chmod +x /tmp/force_ipv6.sh

echo "已创建测试脚本: /tmp/force_ipv6.sh"
echo ""
echo "推荐: 修改 Chrome 启动参数强制使用 IPv6（见下方）"
