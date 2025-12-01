#!/usr/bin/env python3
"""
LowEndTalk Monitor - curl_cffi 版本
使用 curl_cffi 模拟真实浏览器 TLS 指纹，完美绕过 Cloudflare
"""

import time
import logging
from logging.handlers import RotatingFileHandler
from typing import List, Dict, Optional, Set
import subprocess
import random

from curl_cffi import requests
from bs4 import BeautifulSoup

from config import Config

# 配置日志
file_handler = RotatingFileHandler(
    Config.LOG_FILE,
    maxBytes=5*1024*1024,
    backupCount=3,
    encoding='utf-8'
)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

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
            import requests as std_requests
            
            message = f"""🔔 发现 {Config.TARGET_USER} 的新评论！

📝 评论内容：
{comment['content']}

⏰ 时间：{comment['timestamp']}
🔗 链接：{comment['link']}
📄 页面：{comment['page']}
"""
            
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
            
            response = std_requests.post(url, json=data, timeout=10)
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"发送 Telegram 通知失败: {e}")
            return False


class LETMonitorCurlCffi:
    """LowEndTalk 监控器 - curl_cffi 版本"""
    
    def __init__(self):
        self.config = Config
        self.session = None
        self.notifier = TelegramNotifier(
            Config.TELEGRAM_BOT_TOKEN,
            Config.TELEGRAM_CHAT_ID
        )
        self.seen_comments: Set[str] = set()
        self.pages_checked = 0
        self.current_page_num = None
        self.fail_count = 0
        self.page_cf_retry_count = 0  # 当前页面的 CF 重试次数
    
    def init_session(self):
        """初始化 HTTP 会话"""
        try:
            logger.info("🚀 初始化 curl_cffi 会话...")
            
            # 创建会话，模拟 Chrome 120
            self.session = requests.Session(impersonate="chrome120")
            
            # 设置默认头
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Cache-Control': 'max-age=0',
            })
            
            logger.info("✅ curl_cffi 会话初始化成功")
            logger.info("💡 curl_cffi 模拟真实浏览器 TLS 指纹，极高 Cloudflare 绕过率")
            
        except Exception as e:
            logger.error(f"❌ 会话初始化失败: {e}")
            raise
    
    def get_page_url(self, page_num: int) -> str:
        """获取页面 URL"""
        return f"{Config.THREAD_BASE_URL}{page_num}"
    
    def load_page(self, page_num: int) -> Optional[str]:
        """加载指定页面
        
        Returns:
            str: 页面 HTML（成功）
            'not_found': HTTP 404，页面不存在
            'cf_challenge': Cloudflare 挑战失败
            None: 其他错误
        """
        try:
            url = self.get_page_url(page_num)
            logger.info(f"📖 加载页面: {url}")
            
            # 添加随机延迟（模拟人类）
            time.sleep(random.uniform(1, 3))
            
            # 使用 curl_cffi 请求
            response = self.session.get(
                url,
                timeout=30,
                allow_redirects=True,
                verify=True
            )
            
            # 检查状态码
            if response.status_code == 404:
                logger.warning(f"⚠️  HTTP 404: 页面不存在")
                return 'not_found'  # 返回特殊标记
            
            if response.status_code != 200:
                logger.error(f"❌ HTTP 状态码: {response.status_code}")
                return None
            
            # 检查是否是 Cloudflare 挑战页面
            content = response.text.lower()
            cf_keywords = ['cloudflare', 'just a moment', '请稍候', '正在验证']
            
            if any(keyword in content for keyword in cf_keywords):
                logger.warning("⚠️  检测到 Cloudflare 挑战页面")
                return 'cf_challenge'  # 返回 CF 挑战标记
            
            logger.info(f"✅ 页面 {page_num} 加载成功")
            return response.text
            
        except Exception as e:
            logger.error(f"❌ 加载页面 {page_num} 失败: {e}")
            return None
    
    def parse_comments(self, html: str, page_num: int) -> Dict:
        """解析页面中的评论"""
        try:
            soup = BeautifulSoup(html, 'lxml')
            
            # 检查是否是 "Page not found"
            page_not_found = soup.find('h1', string='Page not found.')
            not_found_msg = soup.find('div', {'id': 'Message'})
            
            if page_not_found or (not_found_msg and 'could not be found' in not_found_msg.get_text()):
                logger.warning(f"⚠️  页面 {page_num} 尚不存在")
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
                    
                    if author != Config.TARGET_USER:
                        continue
                    
                    time_elem = item.find('time')
                    timestamp = time_elem.get('datetime', '') if time_elem else ''
                    time_text = time_elem.get('title', '') if time_elem else ''
                    
                    message_elem = item.find('div', class_='Message userContent')
                    if message_elem:
                        # 筛选条件
                        required_image = message_elem.find('img', src=Config.REQUIRED_IMAGE_URL)
                        has_blockquote = message_elem.find('blockquote') is not None
                        
                        if not required_image:
                            logger.debug(f"跳过评论 {comment_id}: 不包含指定图片")
                            continue
                        
                        if Config.FILTER_BLOCKQUOTE and has_blockquote:
                            logger.debug(f"跳过评论 {comment_id}: 包含引用")
                            continue
                        
                        logger.info(f"✅ 评论 {comment_id} 通过筛选")
                        
                        content = message_elem.get_text(separator='\n', strip=True)
                        
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
        
        # 重置当前页面的 CF 重试计数
        if self.current_page_num != page_num:
            self.page_cf_retry_count = 0
        
        for retry in range(max_retries):
            try:
                result = self.load_page(page_num)
                
                # 情况 1: HTTP 404，页面不存在（应该等待，不计入 CF 次数）
                if result == 'not_found':
                    logger.info(f"ℹ️  页面 {page_num} 尚未创建（404），应等待而非跳过")
                    return {'comments': [], 'total': 0, 'not_found': True}
                
                # 情况 2: Cloudflare 挑战失败（计入 CF 次数）
                if result == 'cf_challenge':
                    self.page_cf_retry_count += 1
                    logger.warning(f"⚠️  CF 挑战失败 ({self.page_cf_retry_count}/{Config.MAX_PAGE_CF_RETRIES})")
                    
                    # 检查是否达到 CF 重试上限
                    if self.page_cf_retry_count >= Config.MAX_PAGE_CF_RETRIES:
                        logger.error(f"❌ 页面 {page_num} CF 挑战连续失败 {self.page_cf_retry_count} 次，放弃此页面")
                        return {'comments': [], 'total': 0, 'skip_page': True}
                    
                    # 未达到上限，继续重试
                    if retry < max_retries - 1:
                        logger.info(f"🔄 等待 10 秒后重试...")
                        time.sleep(10)
                        continue
                    else:
                        # 重试次数用完
                        return {'comments': [], 'total': 0, 'skip_page': True}
                
                # 情况 3: 其他错误（None）
                if result is None:
                    if retry < max_retries - 1:
                        logger.warning(f"⚠️  第 {retry + 1} 次尝试失败，重试...")
                        time.sleep(10)
                        continue
                    else:
                        return {'comments': [], 'total': 0, 'not_found': True}
                
                # 情况 4: 成功获取到 HTML
                parsed = self.parse_comments(result, page_num)
                
                if parsed is None:
                    # parse_comments 返回 None 表示页面内容显示 "Page not found"
                    return {'comments': [], 'total': 0, 'not_found': True}
                
                return parsed
                
            except Exception as e:
                logger.error(f"❌ 检查页面 {page_num} 时出错: {e}")
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
    
    def rotate_ipv6(self):
        """轮换 IPv6 地址"""
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
    
    def run(self, start_page: Optional[int] = None):
        """运行监控"""
        try:
            Config.validate()
            
            if not self.session:
                self.init_session()
            
            current_page = start_page or Config.START_PAGE
            
            logger.info(f"🎬 开始监控（curl_cffi 版本）")
            logger.info(f"🎯 起始页面: {current_page}")
            logger.info(f"🎯 目标用户: {Config.TARGET_USER}")
            logger.info(f"⏱️  检查间隔: {Config.CHECK_INTERVAL} 秒")
            
            while True:
                try:
                    logger.info(f"\n{'='*60}")
                    logger.info(f"🔍 检查页面 {current_page}")
                    logger.info(f"{'='*60}\n")
                    
                    if self.current_page_num != current_page:
                        self.current_page_num = current_page
                        self.fail_count = 0
                        self.page_cf_retry_count = 0
                    
                    result = self.check_page(current_page)
                    
                    # 检查是否因 CF 重试次数过多而跳过
                    if result.get('skip_page'):
                        logger.warning(f"⏭️  跳过页面 {current_page}，切换到下一页")
                        current_page += 1
                        continue
                    
                    if result.get('not_found'):
                        # 使用随机等待时间
                        wait_time = random.randint(Config.WAIT_MIN, Config.WAIT_MAX)
                        logger.warning(f"⏸️  页面 {current_page} 尚不存在，等待 {wait_time} 秒...")
                        time.sleep(wait_time)
                        continue
                    
                    comments = result.get('comments', [])
                    total_comments = result.get('total', 0)
                    
                    if self.fail_count > 0:
                        logger.info(f"✅ 失败计数重置（之前 {self.fail_count} 次）")
                        self.fail_count = 0
                    
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
                        
                        # 定期切换 IPv6
                        if self.pages_checked >= Config.RESTART_INTERVAL:
                            logger.info(f"📊 已检查 {self.pages_checked} 页")
                            self.rotate_ipv6()
                            self.pages_checked = 0
                        
                        # 页面已满，使用固定间隔
                        logger.info(f"⏳ 等待 {Config.CHECK_INTERVAL} 秒...")
                        time.sleep(Config.CHECK_INTERVAL)
                    else:
                        # 页面未满，使用随机等待时间
                        wait_time = random.randint(Config.WAIT_MIN, Config.WAIT_MAX)
                        logger.info(f"⏳ 仅 {total_comments} 条，随机等待 {wait_time} 秒（{Config.WAIT_MIN}-{Config.WAIT_MAX}）...")
                        time.sleep(wait_time)
                    
                except KeyboardInterrupt:
                    logger.info("\n⏹️  收到中断信号，停止监控...")
                    break
                    
                except Exception as e:
                    logger.error(f"❌ 出错: {e}")
                    self.fail_count += 1
                    
                    if self.fail_count >= 3:
                        logger.info("🌐 连续失败，尝试切换 IPv6...")
                        self.rotate_ipv6()
                        self.fail_count = 0
                    
                    time.sleep(30)
                        
        except Exception as e:
            logger.error(f"❌ 监控运行失败: {e}")
        finally:
            logger.info("✅ 监控结束")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='LowEndTalk Monitor - curl_cffi 版本')
    parser.add_argument('--start-page', type=int, help='起始页面')
    parser.add_argument('--test', action='store_true', help='测试模式')
    
    args = parser.parse_args()
    
    monitor = LETMonitorCurlCffi()
    
    try:
        if args.test:
            logger.info("🧪 测试模式")
            monitor.init_session()
            
            start_page = args.start_page or Config.START_PAGE
            result = monitor.check_page(start_page)
            
            logger.info(f"\n测试结果:")
            logger.info(f"  总评论数: {result.get('total', 0)}")
            logger.info(f"  目标评论数: {len(result.get('comments', []))}")
        else:
            monitor.run(args.start_page)
    except KeyboardInterrupt:
        logger.info("\n👋 再见!")
    except Exception as e:
        logger.error(f"❌ 程序异常: {e}")


if __name__ == '__main__':
    main()
