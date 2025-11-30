#!/usr/bin/env python3
"""
快速设置向导
帮助用户配置 Telegram Bot
"""

import os
import sys
from pathlib import Path


def print_header():
    """打印欢迎信息"""
    print("\n" + "="*60)
    print("🔍 LowEndTalk FAT32 评论监控器 - 设置向导")
    print("="*60 + "\n")


def check_env_file():
    """检查 .env 文件是否存在"""
    env_file = Path('.env')
    
    if env_file.exists():
        print("✅ 发现现有的 .env 文件")
        overwrite = input("\n是否重新配置？(y/N): ").strip().lower()
        if overwrite != 'y':
            print("保持现有配置，退出设置向导")
            return False
    
    return True


def get_telegram_config():
    """获取 Telegram 配置"""
    print("\n📱 Telegram Bot 配置")
    print("-" * 60)
    print("\n如何获取 Bot Token：")
    print("  1. 在 Telegram 搜索 @BotFather")
    print("  2. 发送 /newbot 创建机器人")
    print("  3. 按提示完成设置并复制 Token\n")
    
    bot_token = input("请输入 Telegram Bot Token: ").strip()
    
    if not bot_token:
        print("❌ Bot Token 不能为空")
        sys.exit(1)
    
    print("\n如何获取 Chat ID：")
    print("  1. 在 Telegram 搜索 @userinfobot")
    print("  2. 发送任意消息获取你的 Chat ID")
    print("  3. 或使用群组 Chat ID（负数）\n")
    
    chat_id = input("请输入 Chat ID: ").strip()
    
    if not chat_id:
        print("❌ Chat ID 不能为空")
        sys.exit(1)
    
    return bot_token, chat_id


def get_monitor_config():
    """获取监控配置"""
    print("\n⚙️ 监控配置")
    print("-" * 60)
    
    start_page = input("\n起始页面 (默认: 241): ").strip() or "241"
    check_interval = input("检查间隔/秒 (默认: 60): ").strip() or "60"
    target_user = input("目标用户 (默认: FAT32): ").strip() or "FAT32"
    headless = input("无头模式 (y/N, 默认: y): ").strip().lower() or "y"
    
    headless_value = "true" if headless == "y" else "false"
    
    return start_page, check_interval, target_user, headless_value


def create_env_file(bot_token, chat_id, start_page, check_interval, target_user, headless):
    """创建 .env 文件"""
    env_content = f"""# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN={bot_token}
TELEGRAM_CHAT_ID={chat_id}

# Monitoring Configuration
START_PAGE={start_page}
CHECK_INTERVAL={check_interval}
TARGET_USER={target_user}
HEADLESS={headless}

# Thread URL
THREAD_BASE_URL=https://lowendtalk.com/discussion/212154/2025-black-friday-cyber-monday-flash-sale-megathread-the-trade-war/p
"""
    
    with open('.env', 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print("\n✅ .env 文件创建成功！")


def test_telegram(bot_token, chat_id):
    """测试 Telegram 配置"""
    print("\n🧪 测试 Telegram 连接...")
    
    try:
        import requests
        
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': '🎉 LowEndTalk 监控器配置成功！\n\n监控即将开始...'
        }
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            print("✅ Telegram 连接测试成功！")
            print("📱 请检查你的 Telegram 是否收到测试消息")
            return True
        else:
            print(f"❌ Telegram 连接测试失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


def print_next_steps():
    """打印后续步骤"""
    print("\n" + "="*60)
    print("🎊 设置完成！")
    print("="*60)
    print("\n📝 接下来你可以：")
    print("\n1. 🧪 测试监控（检查一次后退出）：")
    print("   python monitor.py --test")
    print("\n2. 🚀 开始监控：")
    print("   python monitor.py")
    print("\n3. 📖 指定起始页面：")
    print("   python monitor.py --start-page 241")
    print("\n4. 📚 查看详细文档：")
    print("   cat README.md")
    print("\n" + "="*60 + "\n")


def main():
    """主函数"""
    print_header()
    
    if not check_env_file():
        return
    
    # 获取配置
    bot_token, chat_id = get_telegram_config()
    start_page, check_interval, target_user, headless = get_monitor_config()
    
    # 创建 .env 文件
    create_env_file(bot_token, chat_id, start_page, check_interval, target_user, headless)
    
    # 测试 Telegram 连接
    test_result = test_telegram(bot_token, chat_id)
    
    if test_result:
        print_next_steps()
    else:
        print("\n⚠️  Telegram 测试失败，请检查配置后重试")
        print("你可以手动编辑 .env 文件或重新运行设置向导\n")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 设置已取消")
    except Exception as e:
        print(f"\n❌ 设置过程中出错: {e}")
        sys.exit(1)
