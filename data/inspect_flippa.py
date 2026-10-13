import re
import httpx
from bs4 import BeautifulSoup

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def parse_detail(url):
    r = httpx.get(url, headers=headers, follow_redirects=True, timeout=10.0)
    text = r.text
    bin_m = re.search(r'Buy It Now for USD\s*\$([\d,]+)', text, re.IGNORECASE) or re.search(r'Buy It Now\s*\|\s*USD\s*\$([\d,]+)', text, re.IGNORECASE)
    bin_price = float(bin_m.group(1).replace(',', '')) if bin_m else None
    
    reserve_not_met = 'Reserve not met' in text
    no_reserve = 'No reserve' in text
    
    bid_m = re.search(r'Highest Bid\s*(?:\|\s*)?USD\s*\$([\d,]+)', text, re.IGNORECASE) or re.search(r'Current Bid\s*(?:\|\s*)?USD\s*\$([\d,]+)', text, re.IGNORECASE)
    current_bid = float(bid_m.group(1).replace(',', '')) if bid_m else 0.0

    if bin_price is not None:
        price = bin_price
    elif reserve_not_met:
        price = 999999.0
    else:
        price = current_bid

    return price, bin_price, current_bid, reserve_not_met

test_list = [
    'https://flippa.com/14357933-catchy-brandable-domain-name-3k-business-blog-includes-instagram-monetized-social-group-beginner-friendly-website',
    'https://flippa.com/14183130-property-1-is-a-specialized-real-estate-saas-platform-on-a-23-year-aged-domain-a-complete-business-in-a-box-model-to-earn-passive-income',
    'https://flippa.com/13973578-yourcustomframe-is-a-fully-automated-print-on-demand-store-with-exclusive-artworks-global-shipping-and-no-inventory-required-ready-for-growth-and-scaling'
]

for u in test_list:
    p, b, bid, rnm = parse_detail(u)
    print(u.split('/')[-1][:35], '-> Price:', p, 'BIN:', b, 'Bid:', bid, 'ReserveNotMet:', rnm)
