#!/usr/bin/env python3
"""
LowEndTalk Deal Extractor
Extracts hosting deals and information from LowEndTalk forum HTML
"""

import re
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
import json


@dataclass
class HostingDeal:
    """Represents a hosting deal"""
    provider: str
    ram: Optional[str] = None
    cpu: Optional[str] = None
    storage: Optional[str] = None
    bandwidth: Optional[str] = None
    location: Optional[str] = None
    price: Optional[str] = None
    link: Optional[str] = None
    comment_id: Optional[str] = None
    author: Optional[str] = None
    timestamp: Optional[str] = None
    
    def to_dict(self):
        return asdict(self)


class LETParser:
    """Parser for LowEndTalk forum pages"""
    
    def __init__(self, html_content: str):
        self.soup = BeautifulSoup(html_content, 'html.parser')
        
    def extract_all_comments(self) -> List[Dict]:
        """Extract all comments from the page"""
        comments = []
        comment_items = self.soup.find_all('li', class_=re.compile(r'Item.*ItemComment'))
        
        for item in comment_items:
            comment_data = self._parse_comment(item)
            if comment_data:
                comments.append(comment_data)
                
        return comments
    
    def _parse_comment(self, item) -> Optional[Dict]:
        """Parse a single comment"""
        try:
            # Extract comment ID
            comment_id = item.get('id', '')
            
            # Extract author
            author_elem = item.find('a', class_='Username')
            author = author_elem.text.strip() if author_elem else 'Unknown'
            
            # Extract timestamp
            time_elem = item.find('time')
            timestamp = time_elem.get('datetime', '') if time_elem else ''
            
            # Extract message content
            message_elem = item.find('div', class_='Message userContent')
            message = message_elem.get_text(separator='\n', strip=True) if message_elem else ''
            
            return {
                'comment_id': comment_id,
                'author': author,
                'timestamp': timestamp,
                'message': message,
                'html': str(message_elem) if message_elem else ''
            }
        except Exception as e:
            print(f"Error parsing comment: {e}")
            return None
    
    def extract_deals(self) -> List[HostingDeal]:
        """Extract hosting deals from comments"""
        deals = []
        comments = self.extract_all_comments()
        
        for comment in comments:
            message = comment.get('message', '')
            
            # Look for deal patterns
            deal = self._parse_deal_from_text(message, comment)
            if deal:
                deals.append(deal)
        
        return deals
    
    def _parse_deal_from_text(self, text: str, comment: Dict) -> Optional[HostingDeal]:
        """Parse deal information from text content"""
        # Skip if text is too short or looks like chat
        if len(text) < 20 or not any(char.isdigit() for char in text):
            return None
        
        # Common patterns for hosting specs
        ram_pattern = r'(\d+(?:\.\d+)?)\s*(?:GB|MB)\s*(?:DDR\d+\s+)?RAM'
        cpu_pattern = r'(\d+)\s*(?:v)?(?:CPU|Core|vCPU)'
        storage_pattern = r'(\d+)\s*(?:GB|TB|MB)\s*(?:SSD|NVMe|HDD|Storage|Disk)'
        price_pattern = r'([\d.]+)\s*(?:eur|usd|€|$|EUR|USD)\s*/\s*(?:yr|year|mo|month|m)'
        location_pattern = r'(?:Location|Region|in|@)\s*:?\s*([A-Z]{2,}|[A-Za-z\s]+(?:Netherlands|Germany|USA|UK|Singapore|Japan|France))'
        bandwidth_pattern = r'(\d+(?:\.\d+)?)\s*(?:TB|GB)\s*(?:Bandwidth|Traffic|BW)'
        
        # Extract information
        ram_match = re.search(ram_pattern, text, re.IGNORECASE)
        cpu_match = re.search(cpu_pattern, text, re.IGNORECASE)
        storage_match = re.search(storage_pattern, text, re.IGNORECASE)
        price_match = re.search(price_pattern, text, re.IGNORECASE)
        location_match = re.search(location_pattern, text, re.IGNORECASE)
        bandwidth_match = re.search(bandwidth_pattern, text, re.IGNORECASE)
        
        # Only consider it a deal if it has at least RAM or CPU + price
        if (ram_match or cpu_match) and price_match:
            # Extract links
            links = re.findall(r'https?://[^\s<>"{}|\\^`\[\]]+', text)
            deal_link = links[0] if links else None
            
            return HostingDeal(
                provider=comment.get('author', 'Unknown'),
                ram=ram_match.group(0) if ram_match else None,
                cpu=cpu_match.group(0) if cpu_match else None,
                storage=storage_match.group(0) if storage_match else None,
                bandwidth=bandwidth_match.group(0) if bandwidth_match else None,
                location=location_match.group(1).strip() if location_match else None,
                price=price_match.group(0) if price_match else None,
                link=deal_link,
                comment_id=comment.get('comment_id'),
                author=comment.get('author'),
                timestamp=comment.get('timestamp')
            )
        
        return None
    
    def get_thread_info(self) -> Dict:
        """Extract thread metadata"""
        title_elem = self.soup.find('h1')
        title = title_elem.text.strip() if title_elem else 'Unknown'
        
        # Extract page number
        pager = self.soup.find('span', {'id': 'PagerBefore'})
        current_page = None
        if pager:
            current = pager.find('a', class_='Highlight')
            if current:
                current_page = current.text.strip()
        
        return {
            'title': title,
            'current_page': current_page
        }


def main():
    """Example usage"""
    # Read HTML from file or string
    with open('sample.html', 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    parser = LETParser(html_content)
    
    # Get thread info
    thread_info = parser.get_thread_info()
    print(f"Thread: {thread_info['title']}")
    print(f"Page: {thread_info['current_page']}\n")
    
    # Extract deals
    deals = parser.extract_deals()
    print(f"Found {len(deals)} potential deals:\n")
    
    for i, deal in enumerate(deals, 1):
        print(f"Deal #{i}:")
        print(f"  Provider: {deal.provider}")
        if deal.ram:
            print(f"  RAM: {deal.ram}")
        if deal.cpu:
            print(f"  CPU: {deal.cpu}")
        if deal.storage:
            print(f"  Storage: {deal.storage}")
        if deal.bandwidth:
            print(f"  Bandwidth: {deal.bandwidth}")
        if deal.location:
            print(f"  Location: {deal.location}")
        if deal.price:
            print(f"  Price: {deal.price}")
        if deal.link:
            print(f"  Link: {deal.link}")
        print()
    
    # Export to JSON
    deals_json = [deal.to_dict() for deal in deals]
    with open('deals.json', 'w', encoding='utf-8') as f:
        json.dump(deals_json, f, indent=2, ensure_ascii=False)
    
    print(f"Deals exported to deals.json")


if __name__ == '__main__':
    main()
