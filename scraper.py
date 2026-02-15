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

# YOUR COMPETITORS (Varanasi List)
# Note: I have pre-filled the Booking.com URLs for your specific hotels.
COMPETITORS = [
    {
        "name": "Quality Inn Varanasi",
        "url": f"https://www.booking.com/hotel/in/quality-inn-city-centre-varanasi.html?checkin={checkin}&checkout={checkout}"
    },
    {
        "name": "Hotel Balaji Palace",
        "url": f"https://www.booking.com/hotel/in/balaji-palace-varanasi2.html?checkin={checkin}&checkout={checkout}"
    },
    {
        "name": "Pearl Courtyard",
        "url": f"https://www.booking.com/hotel/in/atithi-satkaar.html?checkin={checkin}&checkout={checkout}"
    },
    {
        "name": "Hotel Veda Heritage",
        "url": f"https://www.booking.com/hotel/in/veda-varanasi.html?checkin={checkin}&checkout={checkout}"
    },
    {
        "name": "Hotel Hardik",
        "url": f"https://www.booking.com/hotel/in/hardik-palacio.html?checkin={checkin}&checkout={checkout}"
    },
    {
        "name": "Hotel Dolphin International",
        "url": f"https://www.booking.com/hotel/in/dolphin-international.html?checkin={checkin}&checkout={checkout}"
    },
    {
        "name": "Vedagram (Vedangam)",
        "url": f"https://www.booking.com/hotel/in/vedangam.html?checkin={checkin}&checkout={checkout}"
    }
]

DATA_FILE = "prices.json"

def get_inventory(url):
    """
    Scrapes the hotel page and returns a DICTIONARY of room types and prices.
    Example: {"Deluxe Room": 4500.0, "Suite": 8000.0}
    """
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15"
    ]
    
    headers = {
        "User-Agent": random.choice(user_agents),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Upgrade-Insecure-Requests": "1"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=25)
        if response.status_code in [403, 429]:
            print(f"Blocked by {url}")
            return {}

        soup = BeautifulSoup(response.text, 'html.parser')
        inventory = {}

        # METHOD 1: Scrape the 'hprt-table' (The main availability table on Desktop)
        room_rows = soup.select("tr.js-hprt-table-row")
        
        if room_rows:
            for row in room_rows:
                # 1. Find Room Name
                name_elem = row.select_one(".hprt-roomtype-icon-link")
                if not name_elem: continue
                room_name = name_elem.text.strip()

                # 2. Find Price
                price_elem = row.select_one(".bui-price-display__value")
                if not price_elem:
                    price_elem = row.select_one(".prco-valign-middle-helper")

                if price_elem:
                    raw_price = price_elem.text.strip().replace(',', '').replace('₹', '')
                    # clean non-numeric
                    clean_price = ''.join(c for c in raw_price if c.isdigit() or c == '.')
                    if clean_price:
                        # We might find multiple prices for the same room (Refundable vs Non-refundable)
                        # We usually want the lowest valid price found for that room type
                        price_val = float(clean_price)
                        
                        if room_name in inventory:
                            if price_val < inventory[room_name]:
                                inventory[room_name] = price_val
                        else:
                            inventory[room_name] = price_val

        # METHOD 2: Fallback for different layouts (e.g. search results view if redirected)
        if not inventory:
            # Try finding generic property cards if redirected to search
            cards = soup.select('[data-testid="property-card"]')
            for card in cards:
                # This usually only happens if the URL redirects to a search list
                price_text = card.select_one('[data-testid="price-and-discounted-price"]')
                if price_text:
                    clean = ''.join(c for c in price_text.text if c.isdigit())
                    if clean:
                        inventory["Standard Offer"] = float(clean)

        return inventory

    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return {}

def main():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            try:
                history = json.load(f)
            except:
                history = []
    else:
        history = []

    today_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    new_entry = {
        "date": today_str,
        "data": {} 
    }
    
    print(f"--- Starting Detailed Inventory Scan for {today_str} ---")
    
    for hotel in COMPETITORS:
        print(f"Scanning Inventory: {hotel['name']}...")
        time.sleep(random.uniform(3, 7)) # Slightly longer wait for safety
        
        room_data = get_inventory(hotel['url'])
        
        if room_data:
            print(f" -> Found {len(room_data)} room types.")
            new_entry["data"][hotel['name']] = room_data
        else:
            print(f" -> No inventory found (Sold out or Blocked).")
            new_entry["data"][hotel['name']] = {}

    history.append(new_entry)
    
    # Keep last 30 scans
    if len(history) > 30:
        history = history[-30:]

    with open(DATA_FILE, 'w') as f:
        json.dump(history, f, indent=2)
    
    print("--- Scan Complete ---")

if __name__ == "__main__":
    main()