#!/usr/bin/env python3
"""
LowEndTalk Monitor - Playwright 版本
使用 Playwright 替代 Selenium，提供更好的 Cloudflare 绕过能力
"""

import time
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from typing import List, Dict, Optional, Set
import subprocess
import random

from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext
from bs4 import BeautifulSoup

from config import Config

# 配置日志 - 使用轮转日志
file_handler = RotatingFileHandler(
    Config.LOG_FILE,
    maxBytes=5*1024*1024,  # 5MB
    backupCount=3,
    encoding='utf-8'
)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

logging.basicConfig(
    level=logging.INFO,
    handlers=[file_handler, console_handler]
)
logger = logging.getLogger(__name__)


class TelegramNotifier:
    """Telegram 通知器"""
    
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
    
    def send_comment_notification(self, comment: Dict) -> bool:
        """发送评论通知"""
        try:
            import requests
            
            message = f"""🔔 发现 {Config.TARGET_USER} 的新评论！

📝 评论内容：
{comment['content']}

⏰ 时间：{comment['timestamp']}
🔗 链接：{comment['link']}
📄 页面：{comment['page']}
"""
            
            # 如果有提取的链接，单独列出
            if comment.get('links'):
                message += "\n🔗 评论中的链接：\n"
                for i, link in enumerate(comment['links'], 1):
                    message += f"{i}. {link}\n"
            
            url = f"{self.base_url}/sendMessage"
            data = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'HTML',
                'disable_web_page_preview': True
            }
            
            response = requests.post(url, json=data, timeout=10)
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"发送 Telegram 通知失败: {e}")
            return False


class LETMonitorPlaywright:
    """LowEndTalk 监控器 - Playwright 版本"""
    
    def __init__(self):
        self.config = Config
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
        self.notifier = TelegramNotifier(
            Config.TELEGRAM_BOT_TOKEN,
            Config.TELEGRAM_CHAT_ID
        )
        self.seen_comments: Set[str] = set()
        self.pages_checked = 0
        
        # Cloudflare 卡住检测
        self.current_page_num = None
        self.cf_fail_count = 0
    
    def init_browser(self):
        """初始化 Playwright 浏览器"""
        try:
            logger.info("🚀 初始化 Playwright 浏览器...")
            
            self.playwright = sync_playwright().start()
            
            # 启动浏览器
            self.browser = self.playwright.chromium.launch(
                headless=Config.HEADLESS,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                ]
            )
            
            # 创建上下文（模拟真实浏览器）
            self.context = self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                locale='zh-CN',
                timezone_id='Asia/Shanghai',
                # 接受语言
                extra_http_headers={
                    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                }
            )
            
            # 创建页面
            self.page = self.context.new_page()
            
            # 隐藏自动化特征
            self.page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['zh-CN', 'zh', 'en']
                });
            """)
            
            logger.info("✅ Playwright 浏览器初始化成功")
            logger.info("💡 Playwright 提供更好的 Cloudflare 绕过能力")
            
        except Exception as e:
            logger.error(f"❌ Playwright 浏览器初始化失败: {e}")
            raise
    
    def get_page_url(self, page_num: int) -> str:
        """获取页面 URL"""
        return f"{Config.THREAD_BASE_URL}{page_num}"
    
    def wait_for_cloudflare(self, timeout: int = None) -> bool:
        """等待 Cloudflare 挑战完成"""
        timeout = timeout or Config.CLOUDFLARE_TIMEOUT
        
        try:
            logger.info(f"☁️  等待 Cloudflare 挑战（最多 {timeout} 秒）...")
            
            # Playwright 的优势：可以等待网络空闲
            self.page.wait_for_load_state('networkidle', timeout=timeout * 1000)
            
            # 检查是否仍在 Cloudflare 页面
            content = self.page.content()
            cf_keywords = ['cloudflare', 'just a moment', '请稍候', '正在验证']
            
            if any(keyword in content.lower() for keyword in cf_keywords):
                logger.warning("⚠️  Cloudflare 挑战未通过")
                return False
            
            logger.info("✅ Cloudflare 挑战已通过")
            return True
            
        except Exception as e:
            logger.warning(f"⚠️  等待 Cloudflare 超时: {e}")
            return False
    
    def load_page(self, page_num: int) -> bool:
        """加载指定页面"""
        try:
            url = self.get_page_url(page_num)
            logger.info(f"📖 加载页面: {url}")
            
            # Playwright 加载页面
            response = self.page.goto(url, wait_until='domcontentloaded', timeout=30000)
            
            if not response:
                logger.error("❌ 页面加载失败：无响应")
                return False
            
            # 添加随机延迟（模拟人类）
            time.sleep(random.uniform(1, 3))
            
            # 检查 Cloudflare
            content = self.page.content()
            cf_keywords = ['cloudflare', 'just a moment', '请稍候', '正在检查', '正在验证']
            
            cf_detected = any(keyword in content.lower() for keyword in cf_keywords)
            
            if cf_detected:
                logger.info("🔍 检测到 Cloudflare 挑战")
                if not self.wait_for_cloudflare():
                    # Cloudflare 挑战失败，计数
                    self.cf_fail_count += 1
                    logger.warning(f"⚠️  Cloudflare 挑战失败 ({self.cf_fail_count}/{Config.MAX_CF_FAILS})")
                    
                    # 判断是否需要重启
                    if self.cf_fail_count >= Config.MAX_CF_FAILS:
                        logger.error(f"❌ 同一页面 Cloudflare 失败 {self.cf_fail_count} 次，触发重启")
                        raise Exception("Cloudflare 挑战超时，需要重启")
                    else:
                        raise Exception("Cloudflare 挑战超时")
            
            # 等待评论列表加载
            logger.info("⏳ 等待页面元素加载...")
            
            try:
                # 等待评论列表出现
                self.page.wait_for_selector('.MessageList', timeout=15000)
                
                # 额外等待确保内容完全加载
                self.page.wait_for_load_state('networkidle', timeout=10000)
                
            except Exception as e:
                logger.warning(f"⚠️  等待元素超时: {e}")
                # 继续尝试，可能已经加载了部分内容
            
            logger.info(f"✅ 页面 {page_num} 加载成功")
            return True
            
        except Exception as e:
            logger.error(f"❌ 加载页面 {page_num} 失败: {e}")
            return False
    
    def parse_comments(self, page_num: int) -> Dict:
        """解析页面中的评论"""
        try:
            # 获取页面内容
            page_source = self.page.content()
            soup = BeautifulSoup(page_source, 'lxml')
            
            # 检查是否是 "Page not found" 页面
            page_not_found = soup.find('h1', string='Page not found.')
            not_found_msg = soup.find('div', {'id': 'Message'})
            
            if page_not_found or (not_found_msg and 'could not be found' in not_found_msg.get_text()):
                logger.warning(f"⚠️  页面 {page_num} 尚不存在，等待中...")
                return None
            
            comments = []
            comment_items = soup.find_all('li', class_=lambda x: x and 'ItemComment' in x)
            total_comments = len(comment_items)
            
            logger.info(f"📊 找到 {total_comments} 条评论")
            
            for item in comment_items:
                try:
                    comment_id = item.get('id', '')
                    author_elem = item.find('a', class_='Username')
                    
                    if not author_elem:
                        continue
                    
                    author = author_elem.get_text(strip=True)
                    
                    # 检查是否是目标用户
                    if author != Config.TARGET_USER:
                        continue
                    
                    # 提取时间
                    time_elem = item.find('time')
                    timestamp = time_elem.get('datetime', '') if time_elem else ''
                    time_text = time_elem.get('title', '') if time_elem else ''
                    
                    # 提取评论内容和链接
                    message_elem = item.find('div', class_='Message userContent')
                    if message_elem:
                        # ===== 筛选条件检查 =====
                        required_image = message_elem.find('img', src=Config.REQUIRED_IMAGE_URL)
                        has_blockquote = message_elem.find('blockquote') is not None
                        
                        if not required_image:
                            logger.debug(f"跳过评论 {comment_id}: 不包含指定图片")
                            continue
                        
                        if Config.FILTER_BLOCKQUOTE and has_blockquote:
                            logger.debug(f"跳过评论 {comment_id}: 包含引用(blockquote)")
                            continue
                        
                        logger.info(f"✅ 评论 {comment_id} 通过筛选")
                        
                        # 提取纯文本内容
                        content = message_elem.get_text(separator='\n', strip=True)
                        
                        # 提取所有链接
                        links = []
                        for a_tag in message_elem.find_all('a', href=True):
                            href = a_tag.get('href', '')
                            if href and not href.startswith('#') and not href.startswith('javascript:'):
                                if href.startswith('/'):
                                    href = f"https://lowendtalk.com{href}"
                                links.append(href)
                        
                        if links:
                            content += '\n\n📎 链接:\n' + '\n'.join(f'- {link}' for link in links)
                    else:
                        content = ''
                        links = []
                    
                    comment_link = f"{self.get_page_url(page_num)}#{comment_id}"
                    
                    comment = {
                        'comment_id': comment_id,
                        'author': author,
                        'timestamp': time_text or timestamp,
                        'content': content,
                        'links': links,
                        'link': comment_link,
                        'page': page_num
                    }
                    
                    comments.append(comment)
                    logger.info(f"🎯 发现 {Config.TARGET_USER} 的评论: {comment_id}")
                    
                except Exception as e:
                    logger.error(f"解析单条评论失败: {e}")
                    continue
            
            return {
                'comments': comments,
                'total': total_comments
            }
            
        except Exception as e:
            logger.error(f"❌ 解析评论失败: {e}")
            return {'comments': [], 'total': 0}
    
    def check_page(self, page_num: int) -> Dict:
        """检查指定页面"""
        max_retries = Config.MAX_PAGE_RETRIES
        
        for retry in range(max_retries):
            try:
                if not self.load_page(page_num):
                    if retry < max_retries - 1:
                        logger.warning(f"⚠️  第 {retry + 1} 次检查失败，重试...")
                        continue
                    else:
                        return {'comments': [], 'total': 0, 'not_found': True}
                
                result = self.parse_comments(page_num)
                
                if result is None:
                    return {'comments': [], 'total': 0, 'not_found': True}
                
                return result
                
            except Exception as e:
                logger.error(f"❌ 检查页面 {page_num} 时出错 (第 {retry + 1} 次): {e}")
                
                if retry < max_retries - 1:
                    time.sleep(10)
                else:
                    return {'comments': [], 'total': 0}
        
        return {'comments': [], 'total': 0}
    
    def notify_new_comments(self, comments: List[Dict]):
        """发送新评论通知"""
        for comment in comments:
            comment_id = comment['comment_id']
            
            if comment_id in self.seen_comments:
                continue
            
            if self.notifier.send_comment_notification(comment):
                self.seen_comments.add(comment_id)
                logger.info(f"📤 已发送评论 {comment_id} 的通知")
            else:
                logger.warning(f"⚠️  评论 {comment_id} 通知发送失败")
    
    def restart_browser(self, rotate_ipv6=False):
        """重启浏览器"""
        logger.info("🔄 重启 Playwright 浏览器...")
        
        # 关闭旧浏览器
        if self.page:
            try:
                self.page.close()
            except:
                pass
        
        if self.context:
            try:
                self.context.close()
            except:
                pass
        
        if self.browser:
            try:
                self.browser.close()
            except:
                pass
        
        time.sleep(2)
        
        # IPv6 轮换
        if rotate_ipv6:
            logger.info("🌐 开始轮换 IPv6 地址...")
            try:
                result = subprocess.run(
                    ['python3', 'ipv6_rotate.py'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    logger.info("✅ IPv6 轮换成功")
                    for line in result.stdout.split('\n'):
                        if line.strip():
                            logger.info(f"   {line}")
                else:
                    logger.warning(f"⚠️  IPv6 轮换失败: {result.stderr}")
                
                time.sleep(3)
                
            except Exception as e:
                logger.error(f"❌ IPv6 轮换出错: {e}")
        
        # 初始化新浏览器
        self.init_browser()
        
        self.pages_checked = 0
        logger.info("✅ Playwright 浏览器重启完成")
    
    def run(self, start_page: Optional[int] = None):
        """运行监控"""
        try:
            Config.validate()
            
            if not self.browser:
                self.init_browser()
            
            current_page = start_page or Config.START_PAGE
            
            logger.info(f"🎬 开始监控（Playwright 版本）")
            logger.info(f"🎯 起始页面: {current_page}")
            logger.info(f"🎯 目标用户: {Config.TARGET_USER}")
            logger.info(f"⏱️  检查间隔: {Config.CHECK_INTERVAL} 秒")
            
            while True:
                try:
                    logger.info(f"\n{'='*60}")
                    logger.info(f"🔍 检查页面 {current_page}")
                    logger.info(f"{'='*60}\n")
                    
                    # 更新当前页面
                    if self.current_page_num != current_page:
                        self.current_page_num = current_page
                        self.cf_fail_count = 0
                    
                    result = self.check_page(current_page)
                    
                    if result.get('not_found'):
                        logger.warning(f"⏸️  页面 {current_page} 尚不存在，等待...")
                        time.sleep(Config.CHECK_INTERVAL)
                        continue
                    
                    comments = result.get('comments', [])
                    total_comments = result.get('total', 0)
                    
                    # 成功加载，重置计数
                    if self.cf_fail_count > 0:
                        logger.info(f"✅ CF 失败计数重置（之前 {self.cf_fail_count} 次）")
                        self.cf_fail_count = 0
                    
                    self.pages_checked += 1
                    
                    if comments:
                        logger.info(f"🎉 发现 {len(comments)} 条评论")
                        self.notify_new_comments(comments)
                    else:
                        logger.info(f"📭 无符合条件的评论")
                    
                    # 判断是否切换页面
                    if total_comments >= 30:
                        logger.info(f"✅ 页面已满 ({total_comments} 条)，切换")
                        current_page += 1
                        
                        if self.pages_checked >= Config.RESTART_INTERVAL:
                            logger.info(f"📊 已检查 {self.pages_checked} 页，重启")
                            self.restart_browser()
                    else:
                        logger.info(f"⏳ 仅 {total_comments} 条，继续等待...")
                    
                    logger.info(f"⏳ 等待 {Config.CHECK_INTERVAL} 秒...")
                    time.sleep(Config.CHECK_INTERVAL)
                    
                except KeyboardInterrupt:
                    logger.info("\n⏹️  收到中断信号，停止监控...")
                    break
                    
                except Exception as e:
                    error_msg = str(e)
                    
                    if "Cloudflare" in error_msg or "需要重启" in error_msg:
                        logger.error(f"🔄 CF 卡住，重启并切换 IPv6...")
                        try:
                            self.restart_browser(rotate_ipv6=True)
                            self.cf_fail_count = 0
                            time.sleep(5)
                            continue
                        except Exception as restart_error:
                            logger.error(f"❌ 重启失败: {restart_error}")
                            time.sleep(30)
                    else:
                        logger.error(f"❌ 出错: {e}")
                        time.sleep(30)
                        
        except Exception as e:
            logger.error(f"❌ 监控运行失败: {e}")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """清理资源"""
        logger.info("🧹 清理资源...")
        
        if self.page:
            try:
                self.page.close()
            except:
                pass
        
        if self.context:
            try:
                self.context.close()
            except:
                pass
        
        if self.browser:
            try:
                self.browser.close()
            except:
                pass
        
        if self.playwright:
            try:
                self.playwright.stop()
            except:
                pass
        
        logger.info("✅ 清理完成")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='LowEndTalk Monitor - Playwright 版本')
    parser.add_argument('--start-page', type=int, help='起始页面')
    parser.add_argument('--test', action='store_true', help='测试模式')
    
    args = parser.parse_args()
    
    monitor = LETMonitorPlaywright()
    
    try:
        if args.test:
            logger.info("🧪 测试模式")
            monitor.init_browser()
            
            start_page = args.start_page or Config.START_PAGE
            result = monitor.check_page(start_page)
            
            logger.info(f"\n测试结果:")
            logger.info(f"  总评论数: {result.get('total', 0)}")
            logger.info(f"  目标评论数: {len(result.get('comments', []))}")
            
            monitor.cleanup()
        else:
            monitor.run(args.start_page)
    except KeyboardInterrupt:
        logger.info("\n👋 再见!")
    except Exception as e:
        logger.error(f"❌ 程序异常: {e}")


if __name__ == '__main__':
    main()
