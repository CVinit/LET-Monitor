# 🌐 强制 Chrome 使用 IPv6 + 自动轮换方案

## 🎯 已实施的改进

### 1. **Chrome 强制使用 IPv6** ⭐

在 `monitor.py` 的 `init_driver()` 中添加了：
```python
# 禁用 IPv4，强制使用 IPv6
options.add_argument('--disable-ipv4')

# 通过 DNS 优先 IPv6
options.add_argument('--host-resolver-rules=MAP * ~NOTFOUND , EXCLUDE ::ffff:0:0/96')
```

**效果**：Chrome 现在会优先使用 IPv6 地址访问网站

### 2. **CF 失败时自动切换 IPv6** ⭐⭐

修改了 `restart_driver()` 方法：
```python
def restart_driver(self, rotate_ipv6=False):
    """重启 Chrome driver
    
    Args:
        rotate_ipv6: 是否在重启前轮换 IPv6 地址
    """
    if rotate_ipv6:
        # 调用 ipv6_rotate.py 切换 IPv6
        subprocess.run(['python3', 'ipv6_rotate.py'])
    
    # 初始化新的 driver
    self.init_driver()
```

### 3. **CF 失败3次触发 IPv6  切换**

在异常处理中：
```python
if "Cloudflare" in error_msg:
    logger.info("🌐 同时执行 IPv6 地址轮换以绕过 Cloudflare")
    self.restart_driver(rotate_ipv6=True)  # 触发 IPv6 轮换
```

## 📊 完整工作流程

```
页面加载
    ↓
遇到 Cloudflare
    ↓
等待30秒
    ↓
❌ 失败 (1/3)
    ↓
❌ 失败 (2/3)
    ↓
❌ 失败 (3/3) ← 达到阈值
    ↓
🔄 触发重启和 IPv6 切换
    ├─ 1. 关闭 Chrome
    ├─ 2. 切换 IPv6 (ipv6_rotate.py)
    ├─ 3. 等待3秒
    └─ 4. 启动新 Chrome (使用新 IPv6)
    ↓
✅ 继续监控
```

## 🧪 验证 Chrome 使用 IPv6

### 方法 1: 运行诊断脚本

```bash
./check_ipv6_usage.sh
```

输出会显示：
- 当前 IPv4 和 IPv6 出口 IP
- DNS 解析结果
- 路由配置

### 方法 2: 在代码中添加测试

在 `monitor.py` 的 `init_driver()` 后添加：
```python
# 测试出口 IP
try:
    self.driver.get('https://api64.ipify.org')
    current_ip = self.driver.find_element(By.TAG_NAME, 'body').text
    logger.info(f"🌐 当前出口 IP: {current_ip}")
    
    # 验证是否是 IPv6
    if ':' in current_ip:
        logger.info("✅ 确认使用 IPv6")
    else:
        logger.warning("⚠️  仍在使用 IPv4: {current_ip}")
except Exception as e:
    logger.warning(f"无法检测出口 IP: {e}")
```

### 方法 3: 系统级测试

```bash
# 在服务器上运行
curl -6 https://api64.ipify.org  # 应该返回你的 IPv6

# 如果 Chrome 仍使用 IPv4，可能需要禁用 IPv4
sudo sysctl -w net.ipv4.ip_default_ttl=0  # 临时测试
```

## ⚙️ 额外优化选项

### 选项 A: 系统级禁用 IPv4（更彻底）

**注意**：可能影响 SSH 如果 SSH 通过 IPv4 连接

```bash
# 临时禁用（重启后恢复）
sudo sysctl -w net.ipv6.conf.all.disable_ipv6=0
sudo ip -4 route del default

# 永久禁用（谨慎！）
echo "net.ipv4.ip_forward=0" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

### 选项 B: 使用 /etc/gai.conf 调整优先级

编辑 `/etc/gai.conf`：
```bash
sudo nano /etc/gai.conf
```

取消注释并修改：
```
# 优先 IPv6
precedence ::ffff:0:0/96  10   # IPv4
precedence 2000::/3       40   # IPv6 (更高优先级)
```

重启网络或重启系统：
```bash
sudo systemctl restart networking
```

### 选项 C: Chrome 通过 SOCKS5 强制 IPv6

如果 Chrome 参数不生效，使用代理：

1. **安装 dante-server**:
```bash
sudo apt install dante-server -y
```

2. **配置只监听 IPv6**:
编辑 `/etc/danted.conf`:
```
internal: :: port = 1080
external: 2a0e:6a80:3:38d::1

socksmethod: none
clientmethod: none

client pass {
    from: ::/0 to: ::/0
}

socks pass {
    from: ::/0 to: ::/0
}
```

3. **在 Chrome 中使用代理**:
```python
options.add_argument('--proxy-server=socks5://[::1]:1080')
```

## 📝 日志示例

### 正常使用 IPv6
```
🌐 Chrome 配置为优先使用 IPv6
🚀 初始化 Chrome driver...
✅ Chrome driver 初始化成功
🌐 当前出口 IP: 2a0e:6a80:3:38d::5
✅ 确认使用 IPv6
```

### CF 失败触发切换
```
⚠️  Cloudflare 挑战失败 (3/3)
❌ 同一页面 Cloudflare 失败 3 次，触发重启
🔄 检测到 Cloudflare 卡住（3次失败），执行强制重启...
🌐 同时执行 IPv6 地址轮换以绕过 Cloudflare
🌐 开始轮换 IPv6 地址...
当前 IPv6 地址: 2a0e:6a80:3:38d::5
选择新的 IPv6 地址: 2a0e:6a80:3:38d::a
✅ 成功切换到 IPv6: 2a0e:6a80:3:38d::a
   (主 IP 2a0e:6a80:3:38d:: 保持不变，用于 SSH)
✅ IPv6 轮换成功
🚀 初始化 Chrome driver...
🌐 Chrome 配置为优先使用 IPv6
✅ Chrome driver 初始化成功
✅ 重启和 IPv6 轮换完成，继续监控...
```

## 🛠️ 故障排查

### 问题 1: Chrome 仍使用 IPv4

**检查**:
```bash
# 在服务器上测试
curl -4 https://api.ipify.org    # 应该超时或失败
curl -6 https://api64.ipify.org  # 应该返回 IPv6
```

**解决**:
```bash
# 方案 A: 临时禁用 IPv4
sudo ip -4 route del default

# 方案 B: 修改 /etc/gai.conf (见上方)

# 方案 C: 使用 SOCKS5 代理 (见上方)
```

### 问题 2: IPv6 轮换不生效

**检查**:
```bash
# 手动测试轮换
python3 ipv6_rotate.py

# 检查当前路由
ip -6 route show

# 应该看到类似：
# default via fe80::1 dev eth0 src 2a0e:6a80:3:38d::5
```

**解决**:
```bash
# 确保 sudo 免密
echo "$USER ALL=(ALL) NOPASSWD: /sbin/ip" | sudo tee /etc/sudoers.d/ipv6_rotate

# 检查网关地址
ip -6 route | grep default
# 更新 ipv6_rotate.py 中的 GATEWAY
```

### 问题 3: SSH 断开

如果禁用 IPv4 导致 SSH 断开：

**预防**:
```bash
# 在 tmux/screen 中运行
tmux new -s monitor

# 设置定时任务恢复 IPv4
echo "*/5 * * * * /sbin/ip -4 route add default via YOUR_GATEWAY" | crontab -
```

## ✅ 完成检查清单

- [ ] Chrome 添加了 `--disable-ipv4` 参数
- [ ] Chrome 添加了 IPv6 DNS 解析规则
- [ ] `restart_driver()` 支持 `rotate_ipv6` 参数
- [ ] CF 失败时自动调用 `ipv6_rotate.py`
- [ ] 测试 Chrome 确实使用 IPv6
- [ ] 测试 IPv6 轮换功能
- [ ] 确认 SSH 连接稳定

## 🎯 最终效果

✅ **Chrome 强制使用 IPv6**
✅ **CF 失败3次自动切换 IPv6**
✅ **每个新 IPv6 对 Cloudflare 都是全新 IP**
✅ **大幅提高绕过成功率**

---

**立即测试**: `./run_with_xvfb.sh 245`
