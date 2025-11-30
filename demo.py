#!/usr/bin/env python3
"""
演示脚本 - 展示如何使用监控器
"""

from monitor import LETMonitor
from config import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def demo_page_check():
    """演示：检查单个页面"""
    print("\n" + "="*60)
    print("📋 演示 1: 检查单个页面")
    print("="*60 + "\n")
    
    try:
        monitor = LETMonitor()
        monitor.init_driver()
        
        # 检查第 241 页
        page_num = 241
        comments = monitor.check_page(page_num)
        
        if comments:
            print(f"\n🎉 在第 {page_num} 页找到 {len(comments)} 条 FAT32 的评论：\n")
            for i, comment in enumerate(comments, 1):
                print(f"评论 #{i}:")
                print(f"  ID: {comment['comment_id']}")
                print(f"  时间: {comment['timestamp']}")
                print(f"  内容: {comment['content'][:100]}...")
                print(f"  链接: {comment['link']}\n")
        else:
            print(f"📭 第 {page_num} 页没有找到 FAT32 的评论")
        
        monitor.cleanup()
        
    except Exception as e:
        logger.error(f"演示失败: {e}")


def demo_config():
    """演示：显示当前配置"""
    print("\n" + "="*60)
    print("⚙️ 演示 2: 当前配置")
    print("="*60 + "\n")
    
    print(f"目标用户: {Config.TARGET_USER}")
    print(f"起始页面: {Config.START_PAGE}")
    print(f"检查间隔: {Config.CHECK_INTERVAL} 秒")
    print(f"线程 URL: {Config.THREAD_BASE_URL}")
    print(f"无头模式: {Config.HEADLESS}")
    print(f"Bot Token: {'已设置' if Config.TELEGRAM_BOT_TOKEN else '未设置'}")
    print(f"Chat ID: {'已设置' if Config.TELEGRAM_CHAT_ID else '未设置'}")


def main():
    """主函数"""
    print("\n🎬 LowEndTalk 监控器演示\n")
    
    # 显示配置
    demo_config()
    
    # 询问是否运行页面检查演示
    print("\n" + "="*60)
    response = input("\n是否运行页面检查演示？这将启动 Chrome 浏览器 (y/N): ").strip().lower()
    
    if response == 'y':
        demo_page_check()
    else:
        print("\n跳过页面检查演示")
    
    print("\n" + "="*60)
    print("✅ 演示完成")
    print("="*60 + "\n")


if __name__ == '__main__':
    main()
