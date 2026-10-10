"""
Extracts live listing metadata to ensure all links are 100% active and working.
"""

import re
import httpx
from bs4 import BeautifulSoup

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36'
}

urls = [
    'https://www.sideprojectors.com/project/99207/concrete-cost-calculator',
    'https://www.sideprojectors.com/project/98202/cpm-calculator',
    'https://www.sideprojectors.com/project/98481/pdf-to-excel',
    'https://www.sideprojectors.com/project/98374/svgmotion-free-ai-svg-animation-tool-rive-alternative',
    'https://www.sideprojectors.com/project/98585/croncalc',
    'https://www.sideprojectors.com/project/98583/pixelcalc',
    'https://www.sideprojectors.com/project/98625/reduce-image-size-in-kb',
    'https://www.microns.io/startup-listings/reddit-bookmark-manager-extension',
    'https://www.microns.io/startup-listings/online-store-with-nfc-cards'
]

for url in urls:
    try:
        r = httpx.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        h1 = soup.find('h1') or soup.find('h2') or soup.find('title')
        title = h1.get_text().strip() if h1 else 'Untitled'
        
        text = soup.get_text()
        price_match = re.search(r'Asking price:\s*\$([0-9,]+)', text, re.IGNORECASE) or re.search(r'\$([0-9,]+)\s*Asking Price', text, re.IGNORECASE)
        price = price_match.group(1) if price_match else 'N/A'
        
        print('-----------------------------------------')
        print('URL:', url)
        print('Status:', r.status_code)
        print('Title:', title)
        print('Price:', price)
    except Exception as e:
        print('ERR for', url, e)
