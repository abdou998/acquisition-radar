import sqlite3
import json
import re

test_cases = [
    {
        "title": "TO GO Group",
        "box_text": "Highest Bid | USD $45,000 | USD $400 | Reduced 10% | Excludes USD $1,200 of inventory | 6 bids | Reserve: USD $40,500 | 20 days left"
    },
    {
        "title": "PinkGirlPics",
        "box_text": "Starting Bid Price | USD $500 | 1 bid | Reserve: USD $25,800 | 20 days left"
    },
    {
        "title": "Speisekartemenus",
        "box_text": "Highest Bid | USD $700 | 19 bids | Reserve not met | 18 days left"
    },
    {
        "title": "Property-1",
        "box_text": "Highest Bid | USD $150 | 2 bids | Reserve: USD $250 | 4 days left"
    },
    {
        "title": "Vilmoria",
        "box_text": "Asking Price (Classified) | USD $790"
    },
    {
        "title": "Ended Deal",
        "box_text": "Asking Price (Classified) | USD $790 | Ended 2 days ago"
    }
]

def parse_box(box_text):
    is_ended = "ended" in box_text.lower() or "sold" in box_text.lower()
    
    # Check classified
    if "Asking Price (Classified)" in box_text or "Asking price" in box_text:
        price_m = re.search(r"USD\s*\$([\d,]+)", box_text)
        price = float(price_m.group(1).replace(",", "")) if price_m else None
        return {
            "sale_type": "classified",
            "asking_price": price,
            "is_ended": is_ended,
            "current_bid": None,
            "reserve_price": None,
            "reserve_not_met": False
        }
    
    # Check auction
    bid_m = re.search(r"(?:Highest|Starting|Current)\s+Bid[^\$0-9]*(?:USD|\$)?\s*\$?([\d,]+)", box_text, re.I)
    bid = float(bid_m.group(1).replace(",", "")) if bid_m else None
    
    res_m = re.search(r"Reserve\s*:\s*(?:USD|\$)?\s*\$?([\d,]+)", box_text, re.I)
    reserve_p = float(res_m.group(1).replace(",", "")) if res_m else None
    
    reserve_not_met = "reserve not met" in box_text.lower()
    
    # Determine effective price
    if reserve_p:
        effective_price = reserve_p
    elif reserve_not_met:
        effective_price = 999999.0
    else:
        effective_price = 999999.0
        
    return {
        "sale_type": "auction",
        "asking_price": effective_price,
        "is_ended": is_ended,
        "current_bid": bid,
        "reserve_price": reserve_p,
        "reserve_not_met": reserve_not_met
    }

for tc in test_cases:
    res = parse_box(tc["box_text"])
    print(f"=== {tc['title']} ===")
    print("  Parsed:", res)
    
    # Validation check
    rejection = None
    if res["is_ended"]:
        rejection = "Listing has ended."
    elif res["sale_type"] == "auction":
        if res["reserve_price"] and res["reserve_price"] > 1000:
            rejection = f"Reserve is ${res['reserve_price']:,.0f} (> $1,000 budget); bid of ${res['current_bid']} is not acquisition price."
        elif res["reserve_not_met"]:
            rejection = f"Unmet reserve; bid of ${res['current_bid']} cannot acquire asset."
        elif not res.get("buy_it_now_price") or res["buy_it_now_price"] > 1000:
            rejection = f"Auction without guaranteed sub-$1k BIN; bid of ${res['current_bid']} is not asking price."
    elif res["asking_price"] > 1000:
        rejection = f"Asking price ${res['asking_price']} > $1,000 budget."
        
    print("  Outcome:", "REJECTED -> " + rejection if rejection else f"ACCEPTED SUB-$1K (Price: ${res['asking_price']})")
