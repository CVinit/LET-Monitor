# 🚀 快速开始指南

## 第一步：安装依赖 ✅

依赖已经安装完成！

```bash
✅ undetected-chromedriver
✅ selenium 
✅ python-telegram-bot
✅ beautifulsoup4
✅ 其他依赖
```

## 第二步：配置 Telegram Bot

### 方法 1: 使用交互式设置向导（推荐）

```bash
python setup.py
```

向导会帮你：
- 📱 配置 Telegram Bot Token
- 💬 配置 Chat ID
- ⚙️ 设置监控参数
- 🧪 测试 Telegram 连接

### 方法 2: 手动创建 .env 文件

```bash
cp .env.example .env
```

然后编辑 `.env` 文件填写你的配置。

## 第三步：获取 Telegram 凭证

### 获取 Bot Token

1. 在 Telegram 搜索 `@BotFather`
2. 发送 `/newbot` 创建新机器人
3. 按提示设置机器人名称
4. 复制获得的 Bot Token

### 获取 Chat ID

1. 在 Telegram 搜索 `@userinfobot`
2. 发送任意消息
3. 复制显示的 Chat ID

## 第四步：运行监控

### 🧪 测试模式（推荐先测试）

```bash
# 测试配置和检查单个页面
python monitor.py --test

# 测试指定页面
python monitor.py --test --start-page 241
```

### 🚀 正式运行

```bash
# 从配置的起始页面开始监控
python monitor.py

# 从指定页面开始
python monitor.py --start-page 241
```

### 📋 查看演示

```bash
python demo.py
```

## 📱 你将收到的 Telegram 通知

当发现 FAT32 的评论时，你会收到类似这样的消息：

```
🔔 发现 FAT32 的新评论！

📝 评论内容：
[评论文本内容...]

⏰ 时间: November 29, 2025 9:42PM
🔗 链接: [点击查看]
📄 页面: 241
```

## 🛠️ 常用命令

```bash
# 查看日志
tail -f monitor.log

# 停止监控
按 Ctrl+C

# 后台运行（Linux/Mac）
nohup python monitor.py &

# 查看进程
ps aux | grep monitor.py
```

## ⚠️ 重要提示

1. **首次运行建议使用测试模式** (`python monitor.py --test`)
2. **确保 Chrome 浏览器已安装**
3. **建议检查间隔设置为 60 秒或更长**
4. **在 .gitignore 中的 .env 文件不会被 Git 追踪**

## 📚 更多信息

查看完整文档：`README.md`

## 🎯 监控原理

```
开始 (page 241) 
    ↓
加载页面
    ↓
解析 30 条评论
    ↓
找到 FAT32 评论？
    ├─ 是 → 发送 Telegram 通知
    └─ 否 → 继续
    ↓
page = page + 1
    ↓
等待 60 秒
    ↓
返回加载页面
```

---

🎉 **现在你可以开始监控了！**
