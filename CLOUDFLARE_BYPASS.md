# 🛡️ Cloudflare 绕过方案 - Debian 无 GUI 服务器

## 🎯 问题分析

在 Debian 11 无 GUI 服务器上，Cloudflare 检测更严格：
- 无显示环境（headless）更容易被识别
- IP 信誉可能较低
- 浏览器指纹异常

## ✅ 解决方案

### 方案 1: 使用 Xvfb（虚拟显示）⭐ 推荐

Cloudflare 可能检测到无显示环境，使用 Xvfb 模拟显示。

#### 安装 Xvfb
```bash
sudo apt update
sudo apt install xvfb -y
```

#### 修改启动脚本
创建 `run_monitor.sh`:
```bash
#!/bin/bash
# 启动虚拟显示
Xvfb :99 -screen 0 1920x1080x24 &
export DISPLAY=:99

# 等待 Xvfb 启动
sleep 2

# 运行监控
python3 monitor.py --start-page 245
```

```bash
chmod +x run_monitor.sh
./run_monitor.sh
```

### 方案 2: IPv6 地址轮换 ⭐⭐ 强烈推荐

利用多个 IPv6 地址，每次重启时切换。

#### 配置 IPv6 地址
```bash
# 查看当前 IPv6 地址
ip -6 addr show

# 添加额外的 IPv6 地址（示例）
sudo ip -6 addr add 2001:db8::2/64 dev eth0
sudo ip -6 addr add 2001:db8::3/64 dev eth0
sudo ip -6 addr add 2001:db8::4/64 dev eth0
```

#### 修改 monitor.py 支持 IPv6 轮换

在 `init_driver` 方法中添加：
```python
import random

def init_driver(self):
    """初始化 Chrome driver"""
    try:
        logger.info("🚀 初始化 Chrome driver...")
        
        options = uc.ChromeOptions()
        
        # ... 现有配置 ...
        
        # ===== IPv6 轮换配置 =====
        ipv6_addresses = [
            '2001:db8::1',  # 替换为你的实际 IPv6 地址
            '2001:db8::2',
            '2001:db8::3',
            '2001:db8::4',
        ]
        
        # 随机选择一个 IPv6 地址
        selected_ipv6 = random.choice(ipv6_addresses)
        logger.info(f"🌐 使用 IPv6 地址: {selected_ipv6}")
        
        # 绑定到特定 IPv6 地址（通过系统级配置）
        # 注意：Chrome 本身不直接支持，需要系统级路由
        # ===== IPv6 配置结束 =====
```

#### 系统级 IPv6 绑定
```bash
# 创建路由脚本 bind_ipv6.sh
#!/bin/bash
IPV6=$1
# 删除默认路由
sudo ip -6 route del default
# 添加新的默认路由，绑定到指定 IPv6
sudo ip -6 route add default via fe80::1 dev eth0 src $IPV6
```

### 方案 3: 使用 SOCKS5/HTTP 代理

通过代理隐藏真实 IP。

#### 安装代理软件（示例：Privoxy）
```bash
sudo apt install privoxy -y
sudo systemctl start privoxy
```

#### 修改 Chrome 配置
在 `init_driver` 中添加：
```python
# 代理配置
proxy_server = "socks5://127.0.0.1:1080"  # 或 http://proxy.example.com:8080

options.add_argument(f'--proxy-server={proxy_server}')
```

### 方案 4: 优化 Chrome 参数（避免检测）

#### 修改 init_driver 方法
```python
def init_driver(self):
    options = uc.ChromeOptions()
    
    # 基础无头模式（关键！）
    if Config.HEADLESS:
        options.add_argument('--headless=new')  # 使用新的无头模式
    
    # ===== 防检测参数（重要）=====
    # 1. 禁用自动化标志
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # 2. 更真实的 User-Agent
    user_agents = [
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    ]
    options.add_argument(f'--user-agent={random.choice(user_agents)}')
    
    # 3. 窗口大小（避免检测无头）
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--start-maximized')
    
    # 4. 禁用 WebGL/Canvas 指纹
    options.add_argument('--disable-webgl')
    options.add_argument('--disable-webgl2')
    
    # 5. 语言设置
    options.add_argument('--lang=zh-CN')
    options.add_experimental_option('prefs', {
        'intl.accept_languages': 'zh-CN,zh;q=0.9,en;q=0.8'
    })
    
    # 6. 禁用沙箱（服务器环境必需）
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    # 7. 避免检测的其他参数
    options.add_argument('--disable-infobars')
    options.add_argument('--disable-notifications')
    options.add_argument('--disable-popup-blocking')
    
    # 8. 内存优化（已有）
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-plugins')
    
    self.driver = uc.Chrome(options=options, version_main=None)
    
    # ===== JavaScript 注入（隐藏自动化特征）=====
    self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': '''
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            
            Object.defineProperty(navigator, 'languages', {
                get: () => ['zh-CN', 'zh', 'en']
            });
        '''
    })
```

### 方案 5: 每次重启时切换 IPv6 ⭐⭐⭐ 最佳方案

#### 创建 IPv6 轮换脚本
创建 `ipv6_rotate.py`:
```python
#!/usr/bin/env python3
import subprocess
import random
import logging

# 你的 IPv6 地址池
IPV6_POOL = [
    '2001:db8::1',
    '2001:db8::2',
    '2001:db8::3',
    '2001:db8::4',
    '2001:db8::5',
]

def rotate_ipv6():
    """轮换 IPv6 地址"""
    selected = random.choice(IPV6_POOL)
    
    try:
        # 示例：通过路由绑定（需要 root 权限）
        subprocess.run([
            'sudo', 'ip', '-6', 'route', 'replace', 'default',
            'via', 'fe80::1',  # 网关地址
            'dev', 'eth0',     # 网卡名
            'src', selected
        ], check=True)
        
        logging.info(f"✅ 已切换到 IPv6: {selected}")
        return selected
    except Exception as e:
        logging.error(f"❌ 切换 IPv6 失败: {e}")
        return None

if __name__ == '__main__':
    rotate_ipv6()
```

#### 修改 restart_driver 方法
```python
def restart_driver(self):
    """重启 Chrome driver（防止内存泄漏）"""
    logger.info("🔄 重启 Chrome driver 以释放资源...")
    
    # 关闭旧的 driver
    if self.driver:
        try:
            self.driver.quit()
        except Exception as e:
            logger.warning(f"关闭旧 driver 时出错: {e}")
    
    # ===== 轮换 IPv6（新增）=====
    try:
        import subprocess
        result = subprocess.run(['python3', 'ipv6_rotate.py'], 
                               capture_output=True, text=True)
        logger.info(f"🌐 IPv6 轮换: {result.stdout}")
    except Exception as e:
        logger.warning(f"IPv6 轮换失败: {e}")
    # ===== IPv6 轮换结束 =====
    
    # 等待一下确保资源释放
    time.sleep(2)
    
    # 初始化新的 driver
    self.init_driver()
```

### 方案 6: 使用 Selenium Wire（查看和修改请求）

#### 安装
```bash
pip install selenium-wire
```

#### 修改代码使用 selenium-wire
```python
from seleniumwire import webdriver

# 代理配置
seleniumwire_options = {
    'proxy': {
        'http': 'http://proxy.example.com:8080',
        'https': 'https://proxy.example.com:8080',
    }
}

driver = webdriver.Chrome(
    seleniumwire_options=seleniumwire_options,
    options=chrome_options
)
```

### 方案 7: 使用 Playwright（替代方案）

Playwright 对 Cloudflare 的绕过效果可能更好。

#### 安装
```bash
pip install playwright
playwright install chromium
playwright install-deps
```

#### 示例代码
```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        args=[
            '--disable-blink-features=AutomationControlled',
        ]
    )
    context = browser.new_context(
        user_agent='Mozilla/5.0 ...',
        viewport={'width': 1920, 'height': 1080},
        locale='zh-CN',
    )
    page = context.new_page()
    page.goto('https://lowendtalk.com/...')
```

## 🎯 推荐组合方案

### 组合 1: Xvfb + 优化参数（最简单）
```bash
# 1. 安装 Xvfb
sudo apt install xvfb -y

# 2. 启动脚本
#!/bin/bash
Xvfb :99 -screen 0 1920x1080x24 &
export DISPLAY=:99
python3 monitor.py
```

### 组合 2: IPv6 轮换 + 优化参数（最有效）⭐
```bash
# 1. 配置多个 IPv6
# 2. 每次重启时切换 IPv6
# 3. 使用优化的 Chrome 参数
```

### 组合 3: 代理 + Xvfb（最稳定）
```bash
# 1. 使用 SOCKS5/HTTP 代理
# 2. 使用 Xvfb
# 3. 定期切换代理
```

## 📝 实施步骤（推荐）

### 第一步：安装 Xvfb
```bash
sudo apt update
sudo apt install xvfb -y
```

### 第二步：配置 IPv6 地址池
```bash
# 查看可用的 IPv6
ip -6 addr show

# 记录到配置中
# 编辑 ipv6_rotate.py，填入实际地址
```

### 第三步：修改代码
1. 应用方案 4 的 Chrome 参数优化
2. 添加 IPv6 轮换（方案 5）
3. 使用 Xvfb 启动（方案 1）

### 第四步：测试
```bash
# 使用 Xvfb 启动
Xvfb :99 -screen 0 1920x1080x24 &
export DISPLAY=:99
python3 monitor.py --test --start-page 245
```

## ⚙️ 配置示例

### .env 配置
```bash
# Chrome 设置
HEADLESS=true  # 服务器环境保持 true

# 每次重启切换 IPv6
RESTART_INTERVAL=3  # 更频繁重启以切换 IP
```

### IPv6 地址池（ipv6_pool.txt）
```
2001:db8::1
2001:db8::2
2001:db8::3
2001:db8::4
2001:db8::5
```

## 🧪 测试方法

### 测试 1: 检查 IP
```python
# 在代码中添加
response = self.driver.execute_script("""
    return fetch('https://api64.ipify.org?format=json')
        .then(r => r.json())
""")
print(f"当前 IP: {response}")
```

### 测试 2: 检查浏览器指纹
访问 https://abrahamjuliot.github.io/creepjs/ 查看指纹

### 测试 3: 检查 Cloudflare
```bash
# 运行测试
python3 monitor.py --test --start-page 245 2>&1 | grep -i cloudflare
```

## ⚠️ 注意事项

1. **IPv6 轮换需要 root 权限**
   ```bash
   # 添加 sudo 免密（谨慎）
   echo 'username ALL=(ALL) NOPASSWD: /sbin/ip' | sudo tee /etc/sudoers.d/ipv6
   ```

2. **Xvfb 需要持续运行**
   ```bash
   # 使用 systemd 管理
   sudo systemctl enable xvfb
   ```

3. **代理可能会减慢速度**
   - 选择速度快的代理
   - 考虑使用本地代理

## 📊 效果对比

| 方案 | 难度 | 效果 | 成本 |
|------|------|------|------|
| Xvfb | ⭐ 简单 | ⭐⭐⭐ 中等 | 免费 |
| IPv6 轮换 | ⭐⭐ 中等 | ⭐⭐⭐⭐⭐ 极佳 | 免费 |
| 代理 | ⭐⭐ 中等 | ⭐⭐⭐⭐ 好 | 可能付费 |
| 优化参数 | ⭐ 简单 | ⭐⭐⭐ 中等 | 免费 |
| Playwright | ⭐⭐⭐ 复杂 | ⭐⭐⭐⭐ 好 | 免费 |

## 🎯 最终推荐

**最佳组合**: Xvfb + IPv6轮换 + 优化参数

原因：
- ✅ 完全免费
- ✅ 效果最佳
- ✅ 充分利用服务器资源（多 IPv6）
- ✅ 稳定性高

---

**实施建议**: 先尝试 Xvfb + 优化参数，如仍有问题再添加 IPv6 轮换
