import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta
import os
import random
import time

# --- CONFIGURATION ---
def get_dates():
    """Returns check-in (tomorrow) and check-out (day after) dates."""
    tomorrow = datetime.now() + timedelta(days=1)
    day_after = tomorrow + timedelta(days=1)
    return tomorrow.strftime("%Y-%m-%d"), day_after.strftime("%Y-%m-%d")

checkin, checkout = get_dates()

# VERIFIED URLS (Final Check 2025)
COMPETITORS = [
    # YOUR HOTEL
    { "name": "Luxuria by Moustache Varanasi", "url": f"https://www.booking.com/hotel/in/luxuria-varanasi-by-moustache.html?checkin={checkin}&checkout={checkout}" },
    
    # COMPETITORS
    { "name": "Quality Inn Varanasi", "url": f"https://www.booking.com/hotel/in/quality-inn-city-centre-varanasi.html?checkin={checkin}&checkout={checkout}" },
    { "name": "Hotel Balaji Palace", "url": f"https://www.booking.com/hotel/in/balaji-palace-varanasi2.html?checkin={checkin}&checkout={checkout}" },
    { "name": "Pearl Courtyard", "url": f"https://www.booking.com/hotel/in/atithi-satkaar.html?checkin={checkin}&checkout={checkout}" },
    { "name": "Hotel Veda Heritage", "url": f"https://www.booking.com/hotel/in/veda-varanasi.html?checkin={checkin}&checkout={checkout}" },
    { "name": "Hotel Hardik", "url": f"https://www.booking.com/hotel/in/hardik-palacio.html?checkin={checkin}&checkout={checkout}" },
    { "name": "Hotel Dolphin International", "url": f"https://www.booking.com/hotel/in/dolphin-international-varanasi.html?checkin={checkin}&checkout={checkout}" },
    { "name": "Vedagram (Vedangam)", "url": f"https://www.booking.com/hotel/in/vedangam.html?checkin={checkin}&checkout={checkout}" }
]

DATA_FILE = "prices.json"

def get_inventory(url):
    # STEALTH HEADERS
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Referer": "https://www.google.com/",
        "Upgrade-Insecure-Requests": "1"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        soup = BeautifulSoup(response.text, 'html.parser')
        inventory = {}

        # 1. Try Table View (Desktop - Shows ALL Room Types)
        rows = soup.select("tr.js-hprt-table-row")
        
        if rows:
            print(f"   [DEBUG] Found Table with {len(rows)} rows. Scanning all categories...")
            for row in rows:
                name_elem = row.select_one(".hprt-roomtype-icon-link")
                
                # Try 3 ways to find price
                price_elem = row.select_one(".bui-price-display__value")
                if not price_elem: price_elem = row.select_one(".prco-valign-middle-helper")
                if not price_elem: price_elem = row.select_one("span[data-testid='price-and-discounted-price']")
                
                if name_elem and price_elem:
                    # Clean the name: Remove extra spaces/newlines
                    r_name = " ".join(name_elem.text.split())
                    
                    # Clean the price: Remove currency symbols and commas
                    r_price = float(''.join(c for c in price_elem.text if c.isdigit() or c == '.'))
                    
                    # LOGIC: Ensure we capture the room.
                    if r_name not in inventory:
                        inventory[r_name] = r_price
                    else:
                        if r_price < inventory[r_name]:
                            inventory[r_name] = r_price

        # 2. Try Card View (Mobile/Fallback)
        if not inventory:
            cards = soup.select('[data-testid="property-card"]')
            for card in cards:
                title = card.select_one('[data-testid="title"]')
                price_elem = card.select_one('[data-testid="price-and-discounted-price"]')
                
                if price_elem:
                    p = float(''.join(c for c in price_elem.text if c.isdigit()))
                    name = title.text.strip() if title else "Standard Offer"
                    inventory[name] = p

        return inventory

    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return {}

def main():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            try: history = json.load(f)
            except: history = []
    else:
        history = []

    today_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    new_entry = { "date": today_str, "data": {} }
    
    print(f"--- Scanning Full Inventory for {today_str} ---")
    
    for hotel in COMPETITORS:
        print(f"Scanning: {hotel['name']}...")
        time.sleep(random.uniform(2, 5))
        
        data = get_inventory(hotel['url'])
        if data:
            print(f" -> Found {len(data)} unique room categories.")
            new_entry["data"][hotel['name']] = data
        else:
            print(f" -> No data found (Sold out or Blocked).")
            new_entry["data"][hotel['name']] = {}

    history.append(new_entry)
    if len(history) > 50: history = history[-50:]

    with open(DATA_FILE, 'w') as f:
        json.dump(history, f, indent=2)
    
    print("--- Scan Complete ---")

if __name__ == "__main__":
    main()
