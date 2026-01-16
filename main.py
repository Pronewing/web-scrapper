#--All Imports--
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile # Optional
from webdriver_manager.firefox import GeckoDriverManager
import pandas as pd
import os
from datetime import datetime # NEW

# Stealth setting to not get caught
import random
import time

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/119.0",
]

# OPTIONAL:
profile_path = r"C:\Users\Rapid Solutions\AppData\Roaming\Mozilla\Firefox\Profiles\2lkjpel2.default-release"

options = Options()
options.profile = FirefoxProfile(profile_path) # OPTIONAL
options.add_argument("--headless")  # Run in background (no GUI)
options.set_preference("dom.webdriver.enabled", False)
options.set_preference("useAutomationExtension", False)
options.set_preference("general.useragent.override", random.choice(USER_AGENTS))

service = Service(GeckoDriverManager().install())
driver = webdriver.Firefox(service=service, options=options)

# Page control start from the page as per your choice

start_page = 1 # page no from which you want to start scrapping
max_pages = 4 # page no till the page you want to scrap

if start_page == 1:
    base_url = "https://www.propertyfinder.bh/en/search" #"https://www.propertyfinder.bh/en/search"
else:
    base_url = f"https://www.propertyfinder.bh/en/search?c=2&fu=0&rp=m&ob=mr&page={start_page}"

#base_url = "https://www.propertyfinder.bh/en/search"
driver.get(base_url)
time.sleep(random.uniform(5, 8))  # Random delay

# Check if we are being blocked
print(f"Page title: {driver.title}")
if "Access" in driver.title or "blocked" in driver.page_source.lower():
    print("WARNING: PropertyFinder has blocked the request!")
    driver.quit()
    exit()

# New Date time variables
current_datetime = datetime.now()
date_str = current_datetime.strftime("%Y-%m-%d")
time_str = current_datetime.strftime("%H-%M-%S")

print(f"✓ Session timestamp: {date_str} {time_str}")
print(f"✓ Will scrape pages {start_page} to {max_pages}")

# Scrapping code
scraped_data = []
page_number = start_page
#max_pages = 5 # Change to 999 for full scrape, 1 for testing


while page_number <= max_pages: 
    print(f"Scraping page {page_number}...")

    # 1. Find the container with all listings
    try:
        #container = driver.find_element("css selector", "ul[aria-label='Properties']")
        listings = driver.find_elements("css selector", "article")
    except:
        print("Failed to locate the property list container. Exiting...")
        break

    print(f"Found {len(listings)} listings on page {page_number}")

    for listing in listings:
        # 2. Extract data fields
        
        # Get full text content and parse it
        try:
            full_text = listing.text
            lines = [line.strip() for line in full_text.split('\n') if line.strip()]
        except:
            print("Skipping a listing due to missing text data")
            continue

        # Extract title/description
        title = "N/A"
        try:
        # Title is usually a longer descriptive text
            for line in lines:
        # Skip lines that are clearly not titles
                if 'BHD' in line or 'sqm' in line or 'Governorate' in line:
                    continue
                if line in ['Call', 'Email', 'WhatsApp', 'Inclusive']:
                    continue
        
        # Title is usually longer than 15 characters
                if len(line) > 15:
                    title = line
                    break
        except:
            title = "N/A"


        # Extract price (format: "300 BHD/month" or "1,500 BHD/month")
        try:
            price = [line for line in lines if 'BHD/month' in line][0]
        except:
            price = "N/A"

        # Extract address/location (typically after price)
        try:
            # Location contains "Governorate" keyword
            address = [line for line in lines if 'Governorate' in line][0]
        except:
            print("Skipping a listing due to missing address data")
            continue

        # Extract square footage (format: "90 sqm")
        try:
            sqft = [line for line in lines if 'sqm' in line][0]
        except:
            sqft = "N/A"

        # Extract link
        try:
            link_element = listing.find_element("css selector", "a[href*='/en/plp/rent/']")
            link = link_element.get_attribute("href")
        except:
            print("Skipping a listing due to missing link data")
            continue

        # Extract image URL
        try:
            image_element = listing.find_element("css selector", "img")
            image_url = image_element.get_attribute("src")
        except:
            image_url = "N/A"

        
        # Extract property type (Apartment, Villa, Duplex, etc.)
        property_type = "N/A"
        try:
            # Look for property type in the text
            text_lower = full_text.lower()
            if 'villa' in text_lower:
                property_type = "Villa"
            elif 'apartment' in text_lower:
                property_type = "Apartment"
            elif 'duplex' in text_lower:
                property_type = "Duplex"
            elif 'penthouse' in text_lower:
                property_type = "Penthouse"
            elif 'compound' in text_lower:
                property_type = "Compound"
            elif 'townhouse' in text_lower:
                property_type = "Townhouse"
            else:
                # Try to find from lines
                for line in lines:
                    line_lower = line.lower()
                    if any(ptype in line_lower for ptype in ['villa', 'apartment', 'duplex', 'penthouse', 'compound', 'townhouse']):
                        property_type = line
                        break
        except Exception as e:
            print(f"Warning: Could not extract property type - {e}")
            property_type = "N/A"

        # Extract beds (appears as just a number, or "studio")
        try:
            beds = None
            for i, line in enumerate(lines):
                if line.lower() == "studio":
                    beds = "Studio"
                    break
                # After property type line (line 2), look for a number that could be beds
                if i > 2 and line.isdigit():
                    beds = line
                    break
            if beds is None:
                beds = "N/A"
        except:
            beds = "N/A"

        # Extract baths (appears as a number, usually after beds)
        try:
            baths = None
            beds_index = -1
            # Find where beds is, then get the next number as baths
            for i, line in enumerate(lines):
                if line.lower() == "studio":
                    beds_index = i
                    break
                if i > 2 and line.isdigit() and beds_index == -1:
                    beds_index = i
                    break
    
            # Get the next digit after beds as baths
            for i in range(beds_index + 1, len(lines)):
                if lines[i].isdigit():
                    baths = lines[i]
                    break
    
            if baths is None:
                baths = "N/A"
        except:
            baths = "N/A"


        scraped_data.append({
            "Title": title,
            "Property Type": property_type,
            "Price": price,
            "Address": address,
            "Beds": beds,
            "Baths": baths,
            "SqFt": sqft,
            "Link": link,
            "Image URL": image_url,
            "Page": page_number,           # ← NEW FIELDS
            "Scraped Date": date_str,      # ← NEW FIELDS
            "Scraped Time": time_str,      # ← NEW FIELDS
            #"Latitude": latitude,
            #"Longitude": longitude
        })

    actual_last_page = page_number # In case of full scrap
    
    if page_number < max_pages: # for test remove for full scrap

        # 3. Pagination
        try:
            # Look for next page link
            # More specific - targets exact next page number
            next_button = driver.find_element("css selector", f"a[aria-label='Go to page {page_number + 1}']")
            #next_button = driver.find_element("css selector", "a[aria-label^='Go to page']")
            # Or use: driver.find_element("css selector", f"a[aria-label='Go to page {page_number + 1}']")
            next_button.click()
            page_number += 1
            time.sleep(random.uniform(5, 10))
        except:
            print("No more pages. Scraping complete.")
            break

    else: # for test
        print(f"Reached max pages limit ({max_pages}). Scraping complete.")
        break



# Convert scraped data to DataFrame
df = pd.DataFrame(scraped_data)

os.makedirs("data", exist_ok=True)
# Save to CSV (customize the filename)
#df.to_csv(csv_filepath, index=False) #Old
# NEW
csv_filename = f"propertyfinder_pages_{start_page}-{actual_last_page}_{date_str}_{time_str}.csv"
csv_filepath = os.path.join("data", csv_filename)
df.to_csv(csv_filepath, index=False)

# Confirmation
print(f"Scraping complete! {len(df)} listings saved to {csv_filename}")

# Close browser
driver.quit()
