"""Extract property addresses from listing URLs (Zillow, Redfin, Realtor.com, etc.)."""
from __future__ import annotations

import re
from urllib.parse import urlparse


def extract_zillow_zpid(url: str) -> str | None:
    if not url:
        return None
    parsed = urlparse(url)
    if "zillow.com" not in parsed.netloc.lower():
        return None
    match = re.search(r"/([0-9]+)_zpid(?:/|$)", parsed.path, re.IGNORECASE)
    return match.group(1) if match else None


def extract_address_from_url(url: str) -> str | None:
    """
    Extract property address from common real estate listing URLs.
    
    Supports:
    - Zillow
    - Redfin  
    - Realtor.com
    - Trulia
    - And more
    
    Returns the extracted address or None if couldn't parse.
    """
    if not url or not url.startswith("http"):
        return None
    
    parsed = urlparse(url.lower())
    domain = parsed.netloc.replace("www.", "")
    path = parsed.path
    
    # Zillow: /homedetails/123-Main-St-City-ST-12345/123456789_zpid/
    if "zillow.com" in domain:
        match = re.search(r"/homedetails/([^/]+)/", path)
        if match:
            address_slug = match.group(1)
            # Convert "123-Main-St-City-ST-12345" to "123 Main St, City, ST 12345"
            parts = address_slug.split("-")
            if len(parts) >= 4:
                # Last part is usually ZIP, second-to-last is state
                zip_code = parts[-1]
                state = parts[-2]
                city = parts[-3]
                street = " ".join(parts[:-3])
                return f"{street}, {city}, {state} {zip_code}"
    
    # Redfin: /city/state/123-main-st/home/123456789
    elif "redfin.com" in domain:
        match = re.search(r"/([^/]+)/([^/]+)/([^/]+)/home/", path)
        if match:
            city = match.group(1).replace("-", " ").title()
            state = match.group(2).upper()
            street = match.group(3).replace("-", " ").title()
            return f"{street}, {city}, {state}"
    
    # Realtor.com: /realestateandhomes-detail/123-Main-St_City_ST_12345
    elif "realtor.com" in domain:
        match = re.search(r"/realestateandhomes-detail/([^_]+)_([^_]+)_([^_]+)_([^_?/]+)", path)
        if match:
            street = match.group(1).replace("-", " ")
            city = match.group(2).replace("-", " ")
            state = match.group(3)
            zip_code = match.group(4)
            return f"{street}, {city}, {state} {zip_code}"
    
    # Trulia: /p/state/city/123-main-st-city-st-12345
    elif "trulia.com" in domain:
        match = re.search(r"/p/[^/]+/[^/]+/([^/]+)", path)
        if match:
            address_slug = match.group(1)
            parts = address_slug.split("-")
            if len(parts) >= 4:
                zip_code = parts[-1]
                state = parts[-2]
                city = parts[-3]
                street = " ".join(parts[:-3])
                return f"{street}, {city}, {state} {zip_code}"
    
    # Homes.com: /city-state/123-main-st/
    elif "homes.com" in domain:
        match = re.search(r"/([^/]+)/([^/]+)/", path)
        if match:
            location = match.group(1).replace("-", " ")
            street = match.group(2).replace("-", " ").title()
            return f"{street}, {location}"
    
    return None


def extract_address_from_listing_url(url: str) -> str | None:
    """
    Main function to extract address from listing URL.
    
    First tries URL parsing, then could fall back to scraping if needed.
    """
    # Try URL pattern matching first
    address = extract_address_from_url(url)
    if address:
        return address
    
    # If URL parsing fails, we could add web scraping here
    # For now, just return None and let the user know
    return None
