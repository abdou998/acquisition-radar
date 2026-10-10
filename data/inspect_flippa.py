import re
import httpx
from bs4 import BeautifulSoup

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

url = 'https://flippa.com/search?filter[property_type]=website&filter[status]=open&filter[price][max]=1000'
r = httpx.get(url, headers=headers, follow_redirects=True, timeout=10.0)
soup = BeautifulSoup(r.text, 'html.parser')

links = soup.find_all('a', href=lambda h: h and re.search(r'/\d{7,8}-', h))
seen = set()

for a in links[:15]:
    href = a.get('href')
    if href in seen:
        continue
    seen.add(href)
    card = a
    for _ in range(8):
        if card.parent:
            card = card.parent
            if 'border' in ' '.join(card.get('class', [])) and '@container' in ' '.join(card.get('class', [])):
                break
    text = card.get_text(separator=' | ', strip=True)
    
    # Precise extraction
    price_match = re.search(r'(?:Buy It Now|Auction|Reserve)\s*\|\s*USD\s*\$([\d,]+)', text, re.IGNORECASE) or re.search(r'USD\s*\$([\d,]+)\s*\|\s*(?:\d+\s*bids|Buy It Now)', text, re.IGNORECASE)
    price = price_match.group(1) if price_match else 'N/A'
    
    rev_match = re.search(r'Monthly Revenue\s*\|\s*USD\s*\$([\d,]+)', text, re.IGNORECASE)
    rev = rev_match.group(1) if rev_match else '0'

    profit_match = re.search(r'Monthly Profit\s*\|\s*USD\s*\$([\d,]+)', text, re.IGNORECASE)
    profit = profit_match.group(1) if profit_match else '0'

    is_verified = 'Data Verified' in text
    
    print('URL:', href)
    print('  Verified:', is_verified, '| Asking/Bid: $' + price, '| Rev: $' + rev + '/mo', '| Profit: $' + profit + '/mo')
