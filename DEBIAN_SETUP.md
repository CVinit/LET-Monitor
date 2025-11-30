# 🚀 Debian 服务器快速部署指南

## 步骤 1: 安装 Xvfb（虚拟显示）

```bash
sudo apt update
sudo apt install xvfb -y
```

## 步骤 2: 配置 IPv6 地址池

### 查看可用的 IPv6 地址
```bash
python3 ipv6_rotate.py --list
```

### 编辑 ipv6_rotate.py
```python
# 将输出的地址填入这里
IPV6_POOL = [
    '2001:xxxx::1',  # 替换为实际地址
    ' 2001:xxxx::2',
    '2001:xxxx::3',
]

# 设置网卡名称（运行 ip addr 查看）
INTERFACE = 'eth0'  # 或 ens3, ens18 等
```

## 步骤 3: 配置 sudo 免密（用于 IPv6 轮换）

```bash
echo "$USER ALL=(ALL) NOPASSWD: /sbin/ip" | sudo tee /etc/sudoers.d/ipv6_rotate
sudo chmod 0440 /etc/sudoers.d/ipv6_rotate
```

## 步骤 4: 测试 IPv6 轮换

```bash
python3 ipv6_rotate.py
```

应该看到：
```
✅ 成功切换到 IPv6: 2001:xxxx::2
```

## 步骤 5: 运行监控（使用 Xvfb）

```bash
./run_with_xvfb.sh 245
```

或者手动运行：
```bash
Xvfb :99 -screen 0 1920x1080x24 &
export DISPLAY=:99
python3 monitor.py --start-page 245
```

## 测试 Cloudmap 绕过

### 方法 1: 简单测试
```bash
./run_with_xvfb.sh 245 2>&1 | grep -i cloudflare
```

### 方法 2: 完整测试
查看日志，应该看到：
```
✅ Cloudflare 挑战已通过
✅ 页面 245 加载成功
```

## 常见问题

### 1. Cloudflare 仍然失败

**方案 A**: 减少重启间隔，更频繁切换 IPv6
```bash
# .env
RESTART_INTERVAL=2  # 每2页重启一次
```

**方案 B**: 检查 IPv6 是否生效
```bash
curl -6 https://api64.ipify.org
```

### 2. Xvfb 启动失败

```bash
# 检查是否已运行
ps aux | grep Xvfb

# 手动停止
pkill Xvfb

# 重新启动
./run_with_xvfb.sh
```

### 3. 权限问题

```bash
# 给脚本添加执行权限
chmod +x run_with_xvfb.sh
chmod +x ipv6_rotate.py
```

## 生产环境部署

### 使用 systemd 自动启动

创建 `/etc/systemd/system/let-monitor.service`:
```ini
[Unit]
Description=LowEndTalk Monitor
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/Py-LET
Environment="DISPLAY=:99"
ExecStartPre=/usr/bin/Xvfb :99 -screen 0 1920x1080x24
ExecStart=/usr/bin/python3 monitor.py --start-page 245
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
sudo systemctl daemon-reload
sudo systemctl enable let-monitor
sudo systemctl start let-monitor
sudo systemctl status let-monitor
```

## 监控运行状态

```bash
# 查看日志
tail -f monitor.log

# 查看 Xvfb 状态
ps aux | grep Xvfb

# 查看当前 IPv6
python3 ipv6_rotate.py --list
```

---

**完成！** 现在你的服务器应该可以绕过 Cloudflare 检测了。
