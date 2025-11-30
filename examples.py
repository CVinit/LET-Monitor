#!/usr/bin/env python3
"""
使用示例和代码片段参考
"""

# ============================================================
# 示例 1: 基本使用
# ============================================================

def example_basic_usage():
    """基本使用示例"""
    from monitor import LETMonitor
    from config import Config
    
    # 创建监控器
    monitor = LETMonitor()
    
    # 从第 241 页开始监控
    monitor.run(start_page=241)


# ============================================================
# 示例 2: 自定义配置
# ============================================================

def example_custom_config():
    """自定义配置示例"""
    import os
    
    # 通过环境变量设置
    os.environ['TELEGRAM_BOT_TOKEN'] = 'your_token'
    os.environ['TELEGRAM_CHAT_ID'] = 'your_chat_id'
    os.environ['TARGET_USER'] = 'FAT32'
    os.environ['CHECK_INTERVAL'] = '60'
    os.environ['START_PAGE'] = '241'
    
    from monitor import LETMonitor
    
    monitor = LETMonitor()
    monitor.run()


# ============================================================
# 示例 3: 单页检查
# ============================================================

def example_single_page_check():
    """检查单个页面"""
    from monitor import LETMonitor
    
    monitor = LETMonitor()
    monitor.init_driver()
    
    # 检查第 241 页
    comments = monitor.check_page(241)
    
    if comments:
        print(f"找到 {len(comments)} 条评论")
        for comment in comments:
            print(f"- {comment['content'][:100]}...")
    else:
        print("未找到目标用户评论")
    
    monitor.cleanup()


# ============================================================
# 示例 4: 仅发送 Telegram 测试消息
# ============================================================

def example_telegram_only():
    """仅测试 Telegram 通知"""
    from monitor import TelegramNotifier
    from config import Config
    
    notifier = TelegramNotifier(
        Config.TELEGRAM_BOT_TOKEN,
        Config.TELEGRAM_CHAT_ID
    )
    
    # 发送测试消息
    notifier.send_message("🧪 这是一条测试消息")
    
    # 发送格式化的评论通知
    test_comment = {
        'content': '测试评论内容',
        'timestamp': '2025-11-29 23:00:00',
        'link': 'https://lowendtalk.com/test',
        'page': 241
    }
    
    notifier.send_comment_notification(test_comment)


# ============================================================
# 示例 5: 自定义评论过滤
# ============================================================

def example_custom_filter():
    """自定义评论过滤逻辑"""
    from monitor import LETMonitor
    from typing import List, Dict
    
    class CustomMonitor(LETMonitor):
        """自定义监控器"""
        
        def filter_comments(self, comments: List[Dict]) -> List[Dict]:
            """自定义过滤逻辑"""
            filtered = []
            
            for comment in comments:
                # 只要包含特定关键词的评论
                keywords = ['deal', 'offer', 'EUR', 'USD']
                
                if any(kw in comment['content'].lower() for kw in keywords):
                    filtered.append(comment)
            
            return filtered
    
    monitor = CustomMonitor()
    monitor.run()


# ============================================================
# 示例 6: 批量检查多个页面
# ============================================================

def example_batch_check():
    """批量检查多个页面"""
    from monitor import LETMonitor
    
    monitor = LETMonitor()
    monitor.init_driver()
    
    # 检查页面 241-245
    all_comments = []
    
    for page in range(241, 246):
        print(f"检查页面 {page}...")
        comments = monitor.check_page(page)
        all_comments.extend(comments)
    
    print(f"\n总共找到 {len(all_comments)} 条 FAT32 的评论")
    
    monitor.cleanup()


# ============================================================
# 示例 7: 使用命令行参数
# ============================================================

"""
# 测试模式
python monitor.py --test

# 从指定页面开始
python monitor.py --start-page 241

# 测试指定页面
python monitor.py --test --start-page 241
"""


# ============================================================
# 示例 8: 环境变量配置文件示例
# ============================================================

"""
.env 文件内容示例:

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=123456789

# Monitoring Configuration
START_PAGE=241
CHECK_INTERVAL=60
TARGET_USER=FAT32
HEADLESS=true

# Thread URL (通常不需要修改)
THREAD_BASE_URL=https://lowendtalk.com/discussion/212154/2025-black-friday-cyber-monday-flash-sale-megathread-the-trade-war/p
"""


# ============================================================
# 示例 9: 日志查看
# ============================================================

"""
# 实时查看日志
tail -f monitor.log

# 查看最近100行
tail -n 100 monitor.log

# 搜索特定内容
grep "FAT32" monitor.log

# 查看错误
grep "ERROR" monitor.log
"""


# ============================================================
# 示例 10: 后台运行（Linux/Mac）
# ============================================================

"""
# 后台启动
nohup python monitor.py --start-page 241 > output.log 2>&1 &

# 查看进程
ps aux | grep monitor.py

# 停止监控
kill <PID>

# 或使用 pkill
pkill -f monitor.py
"""


if __name__ == '__main__':
    print("📚 LowEndTalk 监控器 - 使用示例")
    print("\n查看源代码以了解各种使用示例")
    print("运行 python demo.py 进行交互式演示")
