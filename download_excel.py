import os
import time
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

def download_rbi_excel_files():
    """
    Download all Excel files from the RBI ATM/POS/Card Statistics page using Playwright
    """
    print("Starting download of RBI Excel files...")
    
    # Use Playwright instead of Selenium
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Navigate to the RBI page
        page.goto("https://www.rbi.org.in/Scripts/ATMView.aspx")
        page.wait_for_load_state("networkidle")
        
        # Get the page content
        html_content = page.content()
        browser.close()
    
    # Parse with BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find all Excel download links
    excel_links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.lower().endswith((".xls", ".xlsx")):
            full_url = href if href.startswith("http") else "https://www.rbi.org.in" + href
            filename = full_url.split("/")[-1]
            excel_links.append((full_url, filename))
    
    print(f"Found {len(excel_links)} Excel files to download")
    
    # Download all Excel files
    download_dir = os.path.join(os.getcwd(), "RBI_ATM_Excel")
    os.makedirs(download_dir, exist_ok=True)
    
    downloaded_files = []
    for url, filename in excel_links:
        print(f"📥 Downloading: {filename}")
        try:
            r = requests.get(url)
            r.raise_for_status()
            file_path = os.path.join(download_dir, filename)
            with open(file_path, "wb") as f:
                f.write(r.content)
            downloaded_files.append(file_path)
            print(f"✅ Successfully downloaded {filename}")
        except Exception as e:
            print(f"❌ Failed to download {filename}: {e}")
    
    print(f"Download complete. {len(downloaded_files)} files downloaded.")
    return downloaded_files

if __name__ == "__main__":
    download_rbi_excel_files()
