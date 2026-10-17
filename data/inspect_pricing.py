import httpx
from bs4 import BeautifulSoup
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

test_urls = [
    'https://flippa.com/12950008-offers-insulated-food-containers-with-adjustable-straps-focusing-on-convenient-portable-solutions-for-on-the-go-lifestyles',
    'https://flippa.com/14357933-catchy-brandable-domain-name-3k-business-blog-includes-instagram-monetized-social-group-beginner-friendly-website',
    'https://flippa.com/14280450-pinkgirlpics-com-aged-15-year-domain-automated-skincare-dropshipping-store-400-600-month',
    'https://flippa.com/14239440-speisekartemenus-de-6-month-old-website-monetized-with-google-adsense-guest-posting-german-menu-price-niche-perfect-for-earning-through-google-adsense',
    'https://flippa.com/14183130-property-1-is-a-specialized-real-estate-saas-platform-on-a-23-year-aged-domain-a-complete-business-in-a-box-model-to-earn-passive-income'
]

with httpx.Client(headers=headers, follow_redirects=True, timeout=15.0) as client:
    for u in test_urls:
        r = client.get(u)
        html = r.text
        slug = u.split('/')[-1][:30]
        
        # 1. Buy It Now extraction
        bin_matches = re.findall(r'Buy\s+It\s+Now[^\$0-9]*(?:USD|\$)?\s*\$?([\d,]+)', html, re.I)
        
        # 2. Reserve extraction
        reserve_price_m = re.findall(r'Reserve\s*:\s*(?:USD|\$)?\s*\$?([\d,]+)', html, re.I)
        reserve_not_met = bool(re.search(r'Reserve\s+not\s+met', html, re.I))
        reserve_met = bool(re.search(r'Reserve\s+met', html, re.I))
        no_reserve = bool(re.search(r'No\s+reserve', html, re.I))
        
        # 3. Asking price (Classified)
        asking_m = re.findall(r'Asking\s+Price[^\$0-9]*(?:USD|\$)?\s*\$?([\d,]+)', html, re.I)
        
        # 4. Highest/Current Bid
        bid_m = re.findall(r'(?:Highest|Current)\s+Bid[^\$0-9]*(?:USD|\$)?\s*\$?([\d,]+)', html, re.I)
        
        print(f"=== {slug} ===")
        print(f"  BIN Matches: {bin_matches}")
        print(f"  Reserve Price: {reserve_price_m}")
        print(f"  ReserveNotMet: {reserve_not_met} | ReserveMet: {reserve_met} | NoReserve: {no_reserve}")
        print(f"  Asking Price: {asking_m}")
        print(f"  Bid: {bid_m}")
