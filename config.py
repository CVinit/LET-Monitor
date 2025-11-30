#!/usr/bin/env python3
"""
配置管理模块
"""

import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class Config:
    """配置类"""
    
    # Telegram 配置
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')
    
    # 监控配置
    START_PAGE = int(os.getenv('START_PAGE', '241'))
    CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', '60'))  # 秒
    TARGET_USER = os.getenv('TARGET_USER', 'FAT32')
    
    # 线程 URL
    THREAD_BASE_URL = os.getenv(
        'THREAD_BASE_URL',
        'https://lowendtalk.com/discussion/212154/2025-black-friday-cyber-monday-flash-sale-megathread-the-trade-war/p'
    )
    
    # Chrome 配置
    HEADLESS = os.getenv('HEADLESS', 'false').lower() == 'true'
    
    # 重试配置
    MAX_PAGE_RETRIES = int(os.getenv('MAX_PAGE_RETRIES', '3'))  # 页面加载最大重试次数
    CLOUDFLARE_TIMEOUT = int(os.getenv('CLOUDFLARE_TIMEOUT', '30'))  # Cloudflare 挑战超时（秒）
    RESTART_INTERVAL = int(os.getenv('RESTART_INTERVAL', '5'))  # Chrome driver 重启间隔（页数）
    
    # 筛选配置
    REQUIRED_IMAGE_URL = os.getenv('REQUIRED_IMAGE_URL', 'https://lowendtalk.com/uploads/editor/jm/2b3rylu483wr.png')
    FILTER_BLOCKQUOTE = os.getenv('FILTER_BLOCKQUOTE', 'true').lower() == 'true'  # 是否过滤包含引用的评论
    
    # Cloudflare 卡住检测
    MAX_CF_FAILS = int(os.getenv('MAX_CF_FAILS', '3'))  # 同一页面最大 CF 失败次数（超过后重启 Driver）
    
    # 日志配置
    LOG_FILE = 'monitor.log'
    
    @classmethod
    def validate(cls):
        """验证配置"""
        if not cls.TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN 未设置")
        if not cls.TELEGRAM_CHAT_ID:
            raise ValueError("TELEGRAM_CHAT_ID 未设置")
        return True
