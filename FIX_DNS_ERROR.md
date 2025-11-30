# 🔧 ERR_NAME_NOT_RESOLVED 错误修复

## ❌ 问题原因

Chrome 参数 `--disable-ipv4` 和 `--host-resolver-rules` 导致 DNS 完全无法解析域名。

**已移除的错误参数**:
```python
options.add_argument('--disable-ipv4')  # 无效参数
options.add_argument('--host-resolver-rules=MAP * ~NOTFOUND , EXCLUDE ::ffff:0:0/96')  # 错误规则
```

## ✅ 正确的解决方案

### 方案 1: 使用 /etc/gai.conf（推荐）⭐

这是最安全的方法，不会破坏 DNS 解析。

#### 自动配置
```bash
sudo bash configure_ipv6_priority.sh
# 选择 选项 1
```

#### 手动配置
```bash
# 1. 编辑配置文件
sudo nano /etc/gai.conf

# 2. 添加以下内容（或取消注释）:
precedence ::ffff:0:0/96  10  # IPv4 - 低优先级
precedence 2000::/3       40  # IPv6 - 高优先级

# 3. 重启网络
sudo systemctl restart networking
```

**效果**: 
- ✅ DNS 正常解析
- ✅ IPv6 优先使用
- ✅ IPv4 作为备用
- ✅ SSH 不受影响

### 方案 2: 手动禁用 IPv4 路由（激进）

⚠️ **警告**: 如果 SSH 通过 IPv4 连接会断开！

```bash
# 临时禁用
sudo ip -4 route del default

# 测试
curl -6 https://api64.ipify.org  # 应该返回 IPv6
curl -4 https://api.ipify.org    # 应该失败
```

## 🧪 验证配置

### 测试 1: DNS 解析
```bash
# 应该成功解析
host lowendtalk.com

# 应该看到 IPv6 地址
nslookup lowendtalk.com
```

### 测试 2: 出口 IP
```bash
# IPv4（应该超时或失败，如果使用方案2）
curl -4 https://api.ipify.org

# IPv6（应该成功）
curl -6 https://api64.ipify.org
```

### 测试 3: 运行监控
```bash
# 应该不再报错
./run_with_xvfb.sh 245
```

## 📝 预期日志

### 成功启动
```
🚀 初始化 Chrome driver...
✅ Chrome driver 初始化成功
📖 加载页面: https://lowendtalk.com/...
✅ 页面 245 加载成功
```

### 如果仍有问题
```
# 检查系统配置
ip -6 route show

# 检查 DNS
cat /etc/resolv.conf

# 检查网络
ping6 google.com
```

## 🔄 IPv6 轮换仍然有效

即使不用 Chrome 参数，IPv6 轮换仍然工作：

1. **CF 失败3次** → 触发重启
2. **调用 ipv6_rotate.py** → 切换系统级路由
3. **新 Chrome 启动** → 自动使用新 IPv6

```python
# 在 restart_driver() 中
subprocess.run(['python3', 'ipv6_rotate.py'])  # 切换系统路由
self.init_driver()  # Chrome 使用新路由
```

## 🎯 推荐配置流程

### 在 Debian 服务器上执行：

```bash
# 1. 配置 IPv6 地址池（如果还没做）
sudo bash setup_ipv6_pool.sh

# 2. 配置 IPv6 优先级
sudo bash configure_ipv6_priority.sh
# 选择选项 1，然后重启网络

# 3. 配置 sudo 免密（用于 IPv6 轮换）
echo "$USER ALL=(ALL) NOPASSWD: /sbin/ip" | sudo tee /etc/sudoers.d/ipv6_rotate
sudo chmod 0440 /etc/sudoers.d/ipv6_rotate

# 4. 测试 IPv6 轮换
python3 ipv6_rotate.py

# 5. 运行监控
./run_with_xvfb.sh 245
```

## ⚠️ 常见问题

### Q: DNS 仍然解析失败？
```bash
# 检查 DNS 服务器是否支持 IPv6
cat /etc/resolv.conf

# 如果只有 IPv4 DNS，添加 IPv6 DNS
echo "nameserver 2001:4860:4860::8888" | sudo tee -a /etc/resolv.conf
```

### Q: Chrome 仍使用 IPv4？
```bash
# 方法 A: 使用 gai.conf（已完成）
# 方法 B: 临时禁用 IPv4
sudo ip -4 route del default
```

### Q: SSH 断开了怎么办？
```bash
# 在 tmux/screen 中运行
tmux new -s monitor

# 或者通过 IPv6 连接
ssh user@2a0e:6a80:3:38d::
```

## 📊 效果对比

| 方法 | DNS解析 | IPv6优先 | SSH安全 | 难度 |
|------|---------|----------|---------|------|
| Chrome参数 | ❌ 失败 | ✅ 是 | ✅ 安全 | 简单 |
| gai.conf | ✅ 正常 | ✅ 是 | ✅ 安全 | 简单 ⭐ |
| 禁用IPv4路由 | ✅ 正常 | ✅ 是 | ⚠️ 可能断开 | 简单 |

## ✅ 完成检查

- [ ] 移除错误的 Chrome 参数
- [ ] 配置 /etc/gai.conf
- [ ] 重启网络服务
- [ ] 测试 DNS 解析成功
- [ ] 测试 IPv6 轮换
- [ ] 运行监控程序

---

**立即修复**: `sudo bash configure_ipv6_priority.sh`
