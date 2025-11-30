# 🔍 LowEndTalk FAT32 评论监控器

自动监控 LowEndTalk 论坛中 FAT32 用户的评论，并通过 Telegram 发送实时通知。

## ✨ 功能特性

- 🤖 使用 `undetected-chromedriver` 避免被检测
- 🔄 自动翻页监控
- 📱 Telegram 实时通知
- 🎯 精准定位目标用户评论
- 🔧 可配置的监控参数
- 📝 详细的日志记录
- 🚫 评论去重机制

## 📋 前置要求

- Python 3.8+
- Chrome 浏览器
- Telegram Bot Token 和 Chat ID

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 到 `.env` 并填写配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=你的_bot_token
TELEGRAM_CHAT_ID=你的_chat_id

# Monitoring Configuration
START_PAGE=241
CHECK_INTERVAL=60
TARGET_USER=FAT32
```

### 3. 获取 Telegram Bot Token

1. 在 Telegram 中搜索 `@BotFather`
2. 发送 `/newbot` 创建新机器人
3. 按提示设置机器人名称
4. 获取 Bot Token

### 4. 获取 Chat ID

1. 在 Telegram 中搜索 `@userinfobot`
2. 发送任意消息获取你的 Chat ID
3. 或者将机器人添加到群组，使用群组 Chat ID

### 5. 运行监控

```bash
# 正常运行（从配置的起始页面开始）
python monitor.py

# 从指定页面开始
python monitor.py --start-page 241

# 测试模式（只检查一次）
python monitor.py --test

# 测试指定页面
python monitor.py --test --start-page 241
```

## 📖 使用说明

### 监控逻辑

1. 从指定页面（默认241）开始监控
2. 解析当前页面的所有评论（每页约30条）
3. 检查是否有 FAT32 的评论
4. 如果找到，发送 Telegram 通知
5. 继续下一页（page +1）
6. 等待配置的时间间隔后重复

### 配置参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `TELEGRAM_BOT_TOKEN` | Telegram Bot Token | 必填 |
| `TELEGRAM_CHAT_ID` | 接收通知的 Chat ID | 必填 |
| `START_PAGE` | 起始页面号 | 241 |
| `CHECK_INTERVAL` | 检查间隔（秒） | 60 |
| `TARGET_USER` | 目标用户名 | FAT32 |
| `HEADLESS` | 无头模式 | true |

### 命令行参数

```bash
python monitor.py [选项]

选项:
  --start-page PAGE    从指定页面开始监控
  --test              测试模式（检查一次后退出）
  -h, --help          显示帮助信息
```

## 📱 Telegram 通知示例

```
🔔 发现 FAT32 的新评论！

📝 评论内容：
aluy
1 vCPU
7891MB RAM
17412MB SSD
3.28 EUR/yr
And you have a deal

⏰时间： November 29, 2025 9:30PM
🔗 链接： 查看评论
📄 页面： 241
```

## 🛠️ 项目结构

```
Py-LET/
├── monitor.py          # 主监控脚本
├── config.py           # 配置管理
├── requirements.txt    # Python 依赖
├── .env.example        # 环境变量模板
├── .env               # 环境变量（需创建）
├── monitor.log        # 日志文件（自动生成）
└── README.md          # 项目文档
```

## 🔍 工作原理

### HTML 元素定位

基于提供的 HTML 样本，脚本定位以下元素：

- **评论列表**: `<ul class="MessageList DataList Comments">`
- **评论项**: `<li class="Item ItemComment" id="Comment_XXXXXX">`
- **作者名**: `<a class="Username">FAT32</a>`
- **时间戳**: `<time datetime="..." title="...">`
- **内容**: `<div class="Message userContent">`

### 防检测机制

使用 `undetected-chromedriver`：
- 绕过 Cloudflare 等反爬虫机制
- 模拟真实用户浏览器行为
- 随机 User-Agent
- 自然的页面加载等待

## 📊 日志示例

```
2025-11-29 23:30:00 - __main__ - INFO - 🚀 初始化 Chrome driver...
2025-11-29 23:30:05 - __main__ - INFO - ✅ Chrome driver 初始化成功
2025-11-29 23:30:05 - __main__ - INFO - 🎬 开始监控，起始页面: 241
2025-11-29 23:30:05 - __main__ - INFO - 🎯 目标用户: FAT32
2025-11-29 23:30:10 - __main__ - INFO - 📖 加载页面: ...p241
2025-11-29 23:30:12 - __main__ - INFO - ✅ 页面 241 加载成功
2025-11-29 23:30:12 - __main__ - INFO - 📊 找到 30 条评论
2025-11-29 23:30:12 - __main__ - INFO - 🎯 发现 FAT32 的评论: Comment_4629000
2025-11-29 23:30:13 - __main__ - INFO - ✅ Telegram 消息发送成功
```

## ⚠️ 注意事项

1. **频率限制**: 建议 `CHECK_INTERVAL` 不要设置太短（建议 ≥ 60 秒）
2. **网络稳定**: 确保网络连接稳定
3. **Chrome 版本**: 确保 Chrome 浏览器已安装
4. **资源占用**: 长时间运行会占用一定内存
5. **Telegram 限制**: 注意 Telegram Bot API 的频率限制

## 🐛 故障排除

### Chrome driver 初始化失败

```bash
# 确保 Chrome 浏览器已安装
# macOS
brew install --cask google-chrome

# 或手动从 Google 下载
```

### Telegram 发送失败

- 检查 Bot Token 是否正确
- 确认 Chat ID 格式（可能需要添加 `-` 前缀）
- 确保机器人有发送消息权限

### 页面加载超时

- 检查网络连接
- 增加等待时间
- 尝试关闭无头模式（设置 `HEADLESS=false`）

## 🔒 安全建议

- ⚠️ 不要将 `.env` 文件提交到 Git
- 🔐 妥善保管 Bot Token
- 🛡️ 定期更新依赖包

## 📝 更新日志

### v1.0.0 (2025-11-29)

- ✅ 初始版本
- ✅ 基础监控功能
- ✅ Telegram 通知
- ✅ 评论去重
- ✅ 日志记录

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可

MIT License
