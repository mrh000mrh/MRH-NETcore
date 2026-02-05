from bs4 import BeautifulSoup
import re

def parse_telegram_export(html_content: bytes) -> list[dict]:
    soup = BeautifulSoup(html_content, 'lxml')
    configs = []
    messages = soup.find_all('div', class_='message')

    for msg in messages:
        text = msg.get_text(separator='\n', strip=True)
        links = re.findall(r'(vless|vmess|trojan|ss|mtproto)://[^\s]+', text, re.IGNORECASE)
        for link in links:
            config = {
                "full_link": link,
                "type": link.split('://')[0].upper(),
                "ping": extract_ping(text),
                "location": extract_location(text, link),
                "remark": extract_remark(text) or "Unknown",
                "date": datetime.utcnow()
            }
            configs.append(config)
    return configs

def extract_ping(text: str) -> int:
    match = re.search(r'پینگ[:\s]*(\d+)', text)
    return int(match.group(1)) if match else 999

def extract_location(text: str, link: str) -> str:
    # ساده – بعداً هیبرید با ipinfo
    match = re.search(r'(آلمان|هلند|انگلیس|آمریکا|فرانسه|کانادا)', text)
    return match.group(1) if match else "نامشخص"

def extract_remark(text: str) -> str:
    match = re.search(r'#([^\n]+)', text)
    return match.group(1).strip() if match else None
