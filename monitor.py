#!/usr/bin/env python3
"""
LowEndTalk FAT32 评论监控器
使用 undetected-chromedriver 监控指定用户的评论并发送 Telegram 通知
"""

import time
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from typing import List, Dict, Optional, Set
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import requests

from config import Config


# 配置日志 - 使用轮转日志
# 单个文件最大 5MB，保留 3 份历史文件
file_handler = RotatingFileHandler(
    Config.LOG_FILE,
    maxBytes=5*1024*1024,  # 5MB
    backupCount=3,  # 保留3份历史文件
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
        self.api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    def send_message(self, message: str, parse_mode: str = 'HTML') -> bool:
        """发送消息到 Telegram"""
        try:
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': parse_mode,
                'disable_web_page_preview': False
            }
            
            response = requests.post(self.api_url, json=payload, timeout=10)
            
            if response.status_code == 200:
                logger.info("✅ Telegram 消息发送成功")
                return True
            else:
                logger.error(f"❌ Telegram 消息发送失败: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 发送 Telegram 消息时出错: {e}")
            return False
    
    def send_comment_notification(self, comment: Dict) -> bool:
        """发送评论通知"""
        # 基础消息内容（限制长度避免太长）
        content = comment['content'][:800] + ('...' if len(comment['content']) > 800 else '')
        
        message = f"""
🔔 <b>发现 {Config.TARGET_USER} 的新评论！</b>

📝 <b>评论内容：</b>
{content}

⏰ <b>时间：</b> {comment['timestamp']}
🔗 <b>链接：</b> <a href="{comment['link']}">查看评论</a>
📄 <b>页面：</b> {comment['page']}
"""
        
        # 如果有提取的链接，单独列出（这些链接很重要）
        if comment.get('links') and len(comment['links']) > 0:
            message += "\n<b>🔗 评论中的链接：</b>\n"
            for i, link in enumerate(comment['links'][:10], 1):  # 最多显示10个链接
                message += f"{i}. {link}\n"
        
        return self.send_message(message.strip())


class LETMonitor:
    """LowEndTalk 监控器"""
    
    def __init__(self):
        self.config = Config
        self.driver: Optional[uc.Chrome] = None
        self.notifier = TelegramNotifier(
            Config.TELEGRAM_BOT_TOKEN,
            Config.TELEGRAM_CHAT_ID
        )
        self.seen_comments: Set[str] = set()  # 已发送通知的评论ID
        self.pages_checked = 0  # 已检查的页面数（用于定期重启）
        
        # Cloudflare 卡住检测
        self.current_page = None  # 当前正在检查的页面
        self.cf_fail_count = 0  # 当前页面的 CF 失败次数
        
    def init_driver(self):
        """初始化 Chrome driver"""
        try:
            logger.info("🚀 初始化 Chrome driver...")
            
            options = uc.ChromeOptions()
            
            if Config.HEADLESS:
                options.add_argument('--headless=new')
            
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            # 内存优化参数（防止崩溃）
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-plugins')
            options.add_argument('--disable-images')  # 可选：禁用图片加载以节省内存
            options.add_argument('--blink-settings=imagesEnabled=false')  # 禁用图片
            options.add_argument('--disable-javascript')  # 如果不需要JS可以禁用
            # 限制内存使用
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-software-rasterizer')
            options.add_argument('--disable-background-networking')
            options.add_argument('--disable-default-apps')
            options.add_argument('--disable-sync')
            options.add_argument('--metrics-recording-only')
            options.add_argument('--mute-audio')
            # 设置进程限制
            options.add_argument('--single-process')  # 单进程模式，减少内存消耗
            options.add_argument('--disable-renderer-backgrounding')
            
            self.driver = uc.Chrome(options=options, version_main=None)
            logger.info("✅ Chrome driver 初始化成功")
            
        except Exception as e:
            logger.error(f"❌ Chrome driver 初始化失败: {e}")
            raise
    
    def get_page_url(self, page_num: int) -> str:
        """获取页面 URL"""
        return f"{Config.THREAD_BASE_URL}{page_num}"
    
    def wait_for_cloudflare(self, timeout: Optional[int] = None) -> bool:
        """等待 Cloudflare 挑战完成"""
        timeout = timeout or Config.CLOUDFLARE_TIMEOUT
        
        try:
            logger.info("☁️  检测到可能的 Cloudflare 挑战，等待中...")
            
            # Cloudflare 检测关键字（支持中英文）
            cf_keywords_title = [
                'cloudflare',
                'just a moment',
                '请稍候',
                '稍等片刻',
                '正在检查',
            ]
            
            cf_keywords_content = [
                'checking your browser',
                'ray id',
                'cloudflare',
                '正在验证您是否是真人',
                '正在检查您的浏览器',
                '这可能需要几秒钟',
                '验证您的浏览器',
                '人机验证',
                '安全检查',
                'cloudflare-static',
                'cf-browser-verification',
            ]
            
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                try:
                    title = self.driver.title.lower()
                    page_source = self.driver.page_source
                    page_source_lower = page_source.lower()
                    
                    # 检查是否还在 Cloudflare 挑战页面
                    is_cf_page = False
                    
                    # 检查标题
                    for keyword in cf_keywords_title:
                        if keyword in title:
                            is_cf_page = True
                            break
                    
                    # 检查页面内容
                    if not is_cf_page:
                        for keyword in cf_keywords_content:
                            if keyword in page_source_lower or keyword in page_source:
                                is_cf_page = True
                                break
                    
                    if is_cf_page:
                        elapsed = int(time.time() - start_time)
                        logger.info(f"⏳ Cloudflare 挑战进行中... ({elapsed}秒)")
                        time.sleep(2)
                        continue
                    else:
                        logger.info("✅ Cloudflare 挑战已通过")
                        return True
                        
                except Exception as e:
                    logger.debug(f"Cloudflare 检测异常: {e}")
                    time.sleep(1)
                    continue
            
            logger.warning(f"⚠️  等待 Cloudflare 挑战超时 ({timeout}秒)")
            return False
            
        except Exception as e:
            logger.error(f"❌ 等待 Cloudflare 时出错: {e}")
            return False
    
    def load_page(self, page_num: int, max_retries: Optional[int] = None) -> bool:
        """加载指定页面（带重试）"""
        max_retries = max_retries or Config.MAX_PAGE_RETRIES
        for retry in range(max_retries):
            try:
                url = self.get_page_url(page_num)
                
                if retry > 0:
                    logger.info(f"🔄 第 {retry + 1}/{max_retries} 次尝试加载页面: {url}")
                else:
                    logger.info(f"📖 加载页面: {url}")
                
                self.driver.get(url)
                
                # 等待 Cloudflare 挑战（如果有）
                time.sleep(3)  # 初始等待
                
                # 检查是否遇到 Cloudflare 挑战（支持中英文）
                title = self.driver.title.lower()
                page_source = self.driver.page_source
                
                # 检测 Cloudflare 特征（中英文）
                cf_detected = False
                cf_keywords = ['cloudflare', 'just a moment', '请稍候', '正在检查', '正在验证']
                
                for keyword in cf_keywords:
                    if keyword in title or keyword in page_source:
                        cf_detected = True
                        break
                
                if cf_detected:
                    if not self.wait_for_cloudflare():
                        # Cloudflare 挑战失败，计数
                        self.cf_fail_count += 1
                        logger.warning(f"⚠️  Cloudflare 挑战失败 ({self.cf_fail_count}/{Config.MAX_CF_FAILS})")
                        
                        # 判断是否需要重启
                        if self.cf_fail_count >= Config.MAX_CF_FAILS:
                            logger.error(f"❌ 同一页面 Cloudflare 失败 {self.cf_fail_count} 次，触发重启")
                            raise Exception(f"Cloudflare 挑战超时，需要重启 Driver")
                        else:
                            raise Exception("Cloudflare 挑战超时")
                
                # 等待评论列表加载 - 使用更长的超时时间
                logger.info("⏳ 等待页面元素加载...")
                WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "MessageList"))
                )
                
                # 额外等待确保内容完全加载
                time.sleep(3)
                
                # 验证页面是否真的加载了评论
                page_source = self.driver.page_source
                if 'ItemComment' not in page_source:
                    logger.warning("⚠️  页面加载了但没有找到评论元素，可能需要更多时间")
                    time.sleep(5)  # 再等待一会
                    page_source = self.driver.page_source
                    
                    if 'ItemComment' not in page_source:
                        raise Exception("页面加载后仍未找到评论元素")
                
                logger.info(f"✅ 页面 {page_num} 加载成功")
                return True
                
            except Exception as e:
                logger.error(f"❌ 第 {retry + 1} 次加载页面 {page_num} 失败: {e}")
                
                if retry < max_retries - 1:
                    wait_time = (retry + 1) * 10  # 递增等待时间
                    logger.info(f"⏳ 等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"❌ 页面 {page_num} 加载失败，已重试 {max_retries} 次")
                    return False
        
        return False
    
    def parse_comments(self, page_num: int) -> List[Dict]:
        """解析页面中的所有评论"""
        try:
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'lxml')
            
            # 检查是否是 "Page not found" 页面
            page_not_found = soup.find('h1', string='Page not found.')
            not_found_msg = soup.find('div', {'id': 'Message'})
            
            if page_not_found or (not_found_msg and 'could not be found' in not_found_msg.get_text()):
                logger.warning(f"⚠️  页面 {page_num} 尚不存在，等待中...")
                return None  # 返回 None 表示页面不存在
            
            comments = []
            
            # 查找所有评论项
            # 根据提供的HTML，评论在 <li class="Item ItemComment ..."> 中
            comment_items = soup.find_all('li', class_=lambda x: x and 'ItemComment' in x)
            
            total_comments = len(comment_items)
            logger.info(f"📊 找到 {total_comments} 条评论")
            
            for item in comment_items:
                try:
                    # 提取评论ID
                    comment_id = item.get('id', '')
                    
                    # 提取作者
                    author_elem = item.find('a', class_='Username')
                    author = author_elem.text.strip() if author_elem else ''
                    
                    # 只处理目标用户的评论
                    if author != Config.TARGET_USER:
                        continue
                    
                    # 提取时间戳
                    time_elem = item.find('time')
                    timestamp = time_elem.get('datetime', '') if time_elem else ''
                    time_text = time_elem.get('title', '') if time_elem else ''
                    
                    # 提取评论内容和链接
                    message_elem = item.find('div', class_='Message userContent')
                    if message_elem:
                        # ===== 筛选条件检查 =====
                        # 1. 检查是否包含特定图片标签
                        required_image = message_elem.find('img', src=Config.REQUIRED_IMAGE_URL)
                        
                        # 2. 检查是否包含 blockquote 标签（引用）
                        has_blockquote = message_elem.find('blockquote') is not None
                        
                        # 3. 只处理包含特定图片且没有引用的评论
                        if not required_image:
                            logger.debug(f"跳过评论 {comment_id}: 不包含指定图片")
                            continue
                        
                        if Config.FILTER_BLOCKQUOTE and has_blockquote:
                            logger.debug(f"跳过评论 {comment_id}: 包含引用(blockquote)")
                            continue
                        
                        logger.info(f"✅ 评论 {comment_id} 通过筛选（有图片且无引用）")
                        # ===== 筛选条件检查结束 =====
                        
                        # 提取纯文本内容
                        content = message_elem.get_text(separator='\n', strip=True)
                        
                        # 提取所有链接
                        links = []
                        for a_tag in message_elem.find_all('a', href=True):
                            href = a_tag.get('href', '')
                            # 过滤掉空链接和锚点链接
                            if href and not href.startswith('#') and not href.startswith('javascript:'):
                                # 处理相对链接
                                if href.startswith('/'):
                                    href = f"https://lowendtalk.com{href}"
                                links.append(href)
                        
                        # 如果有链接，将链接信息追加到内容后
                        if links:
                            content += '\n\n📎 链接:\n' + '\n'.join(f'- {link}' for link in links)
                    else:
                        content = ''
                        links = []
                    
                    # 构建评论链接
                    comment_link = f"{self.get_page_url(page_num)}#{comment_id}"
                    
                    comment = {
                        'comment_id': comment_id,
                        'author': author,
                        'timestamp': time_text or timestamp,
                        'content': content,
                        'links': links,  # 新增：单独保存链接列表
                        'link': comment_link,
                        'page': page_num
                    }
                    
                    comments.append(comment)
                    logger.info(f"🎯 发现 {Config.TARGET_USER} 的评论: {comment_id}")
                    
                except Exception as e:
                    logger.error(f"解析单条评论失败: {e}")
                    continue
            
            # 返回评论列表，包含总数信息
            return {
                'comments': comments,
                'total': total_comments  # 总评论数
            }
            
        except Exception as e:
            logger.error(f"❌ 解析评论失败: {e}")
            return {'comments': [], 'total': 0}
    
    def check_page(self, page_num: int, max_retries: Optional[int] = None) -> Dict:
        """检查指定页面（带重试）"""
        max_retries = max_retries or Config.MAX_PAGE_RETRIES
        for retry in range(max_retries):
            try:
                # 尝试加载页面
                if not self.load_page(page_num):
                    if retry < max_retries - 1:
                        logger.warning(f"⚠️  第 {retry + 1} 次检查失败，重试...")
                        continue
                    else:
                        logger.error(f"❌ 页面 {page_num} 检查失败，已重试 {max_retries} 次")
                        return {'comments': [], 'total': 0, 'not_found': True}
                
                # 尝试解析评论
                result = self.parse_comments(page_num)
                
                # 如果页面不存在
                if result is None:
                    return {'comments': [], 'total': 0, 'not_found': True}
                
                return result
                
            except Exception as e:
                logger.error(f"❌ 检查页面 {page_num} 时出错 (第 {retry + 1} 次): {e}")
                
                if retry < max_retries - 1:
                    wait_time = 10
                    logger.info(f"⏳ 等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"❌ 页面 {page_num} 检查失败，已重试 {max_retries} 次")
                    return {'comments': [], 'total': 0}
        
        return {'comments': [], 'total': 0}
    
    def notify_new_comments(self, comments: List[Dict]):
        """发送新评论通知"""
        for comment in comments:
            comment_id = comment['comment_id']
            
            # 检查是否已经发送过通知
            if comment_id in self.seen_comments:
                logger.info(f"⏭️  跳过已通知的评论: {comment_id}")
                continue
            
            # 发送通知
            if self.notifier.send_comment_notification(comment):
                self.seen_comments.add(comment_id)
                logger.info(f"📤 已发送评论 {comment_id} 的通知")
            else:
                logger.warning(f"⚠️  评论 {comment_id} 通知发送失败")
    
    def run(self, start_page: Optional[int] = None):
        """运行监控"""
        try:
            # 验证配置
            Config.validate()
            
            # 初始化 driver
            if not self.driver:
                self.init_driver()
            
            current_page = start_page or Config.START_PAGE
            
            logger.info(f"🎬 开始监控，起始页面: {current_page}")
            logger.info(f"🎯 目标用户: {Config.TARGET_USER}")
            logger.info(f"⏱️  检查间隔: {Config.CHECK_INTERVAL} 秒")
            
            while True:
                try:
                    logger.info(f"\n{'='*60}")
                    logger.info(f"🔍 检查页面 {current_page}")
                    logger.info(f"{'='*60}\n")
                    
                    # 更新当前页面并重置 CF 失败计数（如果页面变化）
                    if self.current_page != current_page:
                        self.current_page = current_page
                        self.cf_fail_count = 0  # 新页面，重置计数
                        logger.debug(f"切换到新页面 {current_page}，重置 CF 失败计数")
                    
                    # 检查当前页面
                    result = self.check_page(current_page)
                    
                    # 检查页面是否存在
                    if result.get('not_found'):
                        logger.warning(f"⏸️  页面 {current_page} 尚不存在，等待 {Config.CHECK_INTERVAL} 秒后重新检查...")
                        time.sleep(Config.CHECK_INTERVAL)
                        continue  # 不增加页面计数，继续检查当前页
                    
                    comments = result.get('comments', [])
                    total_comments = result.get('total', 0)
                    
                    # 页面成功加载，重置 CF 失败计数
                    if self.cf_fail_count > 0:
                        logger.info(f"✅ 页面加载成功，重置 CF 失败计数（之前 {self.cf_fail_count} 次）")
                        self.cf_fail_count = 0
                    
                    # 页面计数增加（只在页面存在时计数）
                    self.pages_checked += 1
                    
                    if comments:
                        logger.info(f"🎉 在页面 {current_page} 发现 {len(comments)} 条 {Config.TARGET_USER} 的评论")
                        self.notify_new_comments(comments)
                    else:
                        logger.info(f"📭 页面 {current_page} 没有 {Config.TARGET_USER} 的符合条件的评论")
                    
                    # 判断是否切换到下一页
                    # 只有当前页评论满 30 条时才切换到下一页
                    if total_comments >= 30:
                        logger.info(f"✅ 页面 {current_page} 已满 ({total_comments} 条评论)，切换到下一页")
                        current_page += 1
                        
                        # 每隔 N 页重启一次 Chrome driver（防止内存泄漏）
                        if self.pages_checked >= Config.RESTART_INTERVAL:
                            logger.info(f"📊 已检查 {self.pages_checked} 页，执行定期重启以释放资源...")
                            self.restart_driver()
                    else:
                        logger.info(f"⏳ 页面 {current_page} 仅有 {total_comments} 条评论（未满30条），等待 {Config.CHECK_INTERVAL} 秒后继续检查...")
                        # 不切换页面，继续等待当前页
                    
                    # 等待一段时间再检查下一页
                    logger.info(f"⏳ 等待 {Config.CHECK_INTERVAL} 秒后检查下一页...")
                    time.sleep(Config.CHECK_INTERVAL)
                    
                except KeyboardInterrupt:
                    logger.info("\n⏹️  收到中断信号，停止监控...")
                    break
                    
                except Exception as e:
                    error_msg = str(e)
                    
                    # 检查是否是 Cloudflare 需要重启的情况
                    if "需要重启 Driver" in error_msg or "Cloudflare" in error_msg:
                        logger.error(f"🔄 检测到 Cloudflare 卡住，执行强制重启...")
                        try:
                            self.restart_driver()
                            logger.info("✅ 重启完成，继续监控...")
                            # 重置失败计数
                            self.cf_fail_count = 0
                            # 等待一会儿再继续
                            time.sleep(5)
                            continue
                        except Exception as restart_error:
                            logger.error(f"❌ 重启失败: {restart_error}")
                            logger.info(f"⏳ 等待 30 秒后重试...")
                            time.sleep(30)
                    else:
                        # 其他错误
                        logger.error(f"❌ 检查页面时出错: {e}")
                        logger.info(f"⏳ 等待 30 秒后重试...")
                        time.sleep(30)
                    
        except Exception as e:
            logger.error(f"❌ 监控运行失败: {e}")
            raise
            
        finally:
            self.cleanup()
    
    def restart_driver(self):
        """重启 Chrome driver（防止内存泄漏）"""
        logger.info("🔄 重启 Chrome driver 以释放资源...")
        
        # 关闭旧的 driver
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                logger.warning(f"关闭旧 driver 时出错: {e}")
        
        # 等待一下确保资源释放
        time.sleep(2)
        
        # 初始化新的 driver
        self.init_driver()
        
        # 重置页面计数
        self.pages_checked = 0
        logger.info("✅ Chrome driver 重启完成")
    
    def cleanup(self):
        """清理资源"""
        if self.driver:
            logger.info("🧹 关闭 Chrome driver...")
            try:
                self.driver.quit()
            except:
                pass
            logger.info("✅ 清理完成")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='LowEndTalk FAT32 评论监控器')
    parser.add_argument('--start-page', type=int, help='起始页面号')
    parser.add_argument('--test', action='store_true', help='测试模式（检查一次后退出）')
    
    args = parser.parse_args()
    
    monitor = LETMonitor()
    
    try:
        if args.test:
            # 测试模式
            logger.info("🧪 测试模式")
            monitor.init_driver()
            start_page = args.start_page or Config.START_PAGE
            comments = monitor.check_page(start_page)
            
            if comments:
                logger.info(f"找到 {len(comments)} 条评论")
                for comment in comments:
                    logger.info(f"  - {comment['comment_id']}: {comment['content'][:100]}...")
            else:
                logger.info("未找到目标用户的评论")
                
        else:
            # 正常运行
            monitor.run(start_page=args.start_page)
            
    except KeyboardInterrupt:
        logger.info("\n👋 再见！")
    except Exception as e:
        logger.error(f"💥 程序异常: {e}", exc_info=True)
    finally:
        monitor.cleanup()


if __name__ == '__main__':
    main()
