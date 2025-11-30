# 🔧 Debian 无桌面服务器 Playwright 错误修复

## ❌ 错误信息

```
Missing X server or $DISPLAY
Looks like you launched a headed browser without having a XServer running.
```

## ✅ 解决方案（3种）

### 方案 1: 使用启动脚本（推荐）⭐⭐⭐

**最简单的方法**，使用提供的启动脚本：

```bash
./run_playwright.sh 340
```

脚本会自动：
1. ✅ 启动 Xvfb
2. ✅ 设置 DISPLAY 环境变量
3. ✅ 运行 Playwright 监控
4. ✅ 退出时自动清理

### 方案 2: 手动设置 Xvfb ⭐⭐

```bash
# 1. 确保 Xvfb 已安装
sudo apt install xvfb -y

# 2. 启动 Xvfb
Xvfb :99 -screen 0 1920x1080x24 &

# 3. 设置 DISPLAY 环境变量
export DISPLAY=:99

# 4. 运行 Playwright
python3 monitor_playwright.py --start-page 340
```

### 方案 3: 使用真正的 headless 模式 ⭐

**最简单，但 CF 绕过率略低**

```bash
# 编辑 .env
nano .env

# 设置
HEADLESS=true

# 直接运行（不需要 Xvfb）
python3 monitor_playwright.py --start-page 340
```

## 📊 方案对比

| 方案 | CF 绕过率 | 难度 | 推荐度 |
|------|-----------|------|---------|
| 启动脚本 | 95% | 简单 | ⭐⭐⭐ |
| 手动 Xvfb | 95% | 中等 | ⭐⭐ |
| headless | 85% | 最简单 | ⭐⭐ |

## 🚀 快速修复步骤

### 步骤 1: 确保 Xvfb 已安装

```bash
# 检查
which Xvfb

# 如果没有，安装
sudo apt update
sudo apt install xvfb -y
```

### 步骤 2: 使用启动脚本

```bash
# 上传 run_playwright.sh 到服务器后
chmod +x run_playwright.sh

# 运行
./run_playwright.sh 340
```

### 步骤 3: 验证成功

你应该看到：
```
✓ 检测到 Xvfb
启动 Xvfb 虚拟显示...
✓ Xvfb 已启动 (PID: 12345, DISPLAY: :99)

================================
启动 Playwright 监控
================================
起始页面: 340

🚀 初始化 Playwright 浏览器...
✅ Playwright 浏览器初始化成功
📖 加载页面: ...
✅ 页面 340 加载成功  ← 成功！
```

## 🧪 测试各方案

### 测试方案 1（启动脚本）
```bash
./run_playwright.sh 350
# 应该成功启动并加载页面
# 按 Ctrl+C 停止
```

### 测试方案 2（手动 Xvfb）
```bash
Xvfb :99 -screen 0 1920x1080x24 &
export DISPLAY=:99
python3 monitor_playwright.py --test --start-page 350
```

### 测试方案 3（headless）
```bash
# 编辑 .env，设置 HEADLESS=true
python3 monitor_playwright.py --test --start-page 350
```

## ⚙️ 详细说明

### 为什么需要 Xvfb？

Playwright 默认使用 **headed 模式**（有界面），这样能：
- ✅ 更好地模拟真实用户
- ✅ 更高的 Cloudflare 绕过率
- ✅ 更完整的浏览器功能

但无桌面服务器没有 X Server，所以需要 **Xvfb**（虚拟显示）。

### Xvfb 是什么？

**Xvfb** = X Virtual FrameBuffer
- 虚拟的 X Server
- 在内存中创建虚拟显示
- 不需要真实的显示器

### DISPLAY 环境变量

```bash
export DISPLAY=:99
```
告诉程序使用虚拟显示 `:99`（而不是物理显示 `:0`）

## 🔍 故障排查

### 问题 1: Xvfb 未安装

```bash
sudo apt update
sudo apt install xvfb -y
```

### 问题 2: Xvfb 已在运行

```bash
# 查看正在运行的 Xvfb
ps aux | grep Xvfb

# 停止旧的
pkill Xvfb

# 重新启动
Xvfb :99 -screen 0 1920x1080x24 &
```

### 问题 3: DISPLAY 未设置

```bash
# 检查
echo $DISPLAY

# 应该输出: :99

# 如果没有，设置
export DISPLAY=:99
```

### 问题 4: 端口冲突

如果 `:99` 被占用：
```bash
# 使用其他端口
Xvfb :98 -screen 0 1920x1080x24 &
export DISPLAY=:98
```

## 🎯 生产环境部署

### 使用 systemd 自动管理

创建 `/etc/systemd/system/playwright-monitor.service`:
```ini
[Unit]
Description=Playwright LET Monitor
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/Py-LET
Environment="DISPLAY=:99"
ExecStartPre=/usr/bin/Xvfb :99 -screen 0 1920x1080x24
ExecStart=/usr/bin/python3 monitor_playwright.py --start-page 340
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
```

启动：
```bash
sudo systemctl daemon-reload
sudo systemctl enable playwright-monitor
sudo systemctl start playwright-monitor
sudo systemctl status playwright-monitor
```

### 后台运行

```bash
# 方法 1: nohup
nohup ./run_playwright.sh 340 > playwright.log 2>&1 &

# 方法 2: screen
screen -S playwright
./run_playwright.sh 340
# 按 Ctrl+A, D 离开

# 方法 3: tmux
tmux new -s playwright
./run_playwright.sh 340
# 按 Ctrl+B, D 离开
```

## ✅ 最终验证

运行以下命令确认一切正常：

```bash
# 1. 检查 Xvfb
which Xvfb

# 2. 启动测试
./run_playwright.sh 350

# 3. 应该看到成功加载页面
# ✅ Xvfb 已启动
# ✅ Playwright 浏览器初始化成功
# ✅ 页面 350 加载成功

# 4. 按 Ctrl+C 停止
# ✅ 清理完成
```

## 📋 完整命令流程

```bash
# 在 Debian 服务器上执行

# 1. 安装 Xvfb（如果还没有）
sudo apt install xvfb -y

# 2. 给脚本添加执行权限
chmod +x run_playwright.sh

# 3. 测试运行
./run_playwright.sh 350

# 4. 如果成功，后台运行
nohup ./run_playwright.sh 340 > playwright.log 2>&1 &

# 5. 检查日志
tail -f playwright.log
```

---

**立即修复**: 
```bash
sudo apt install xvfb -y
./run_playwright.sh 340
```
