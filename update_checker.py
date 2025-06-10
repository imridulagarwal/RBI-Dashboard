import os
import time
import requests
from bs4 import BeautifulSoup
import logging
from datetime import datetime
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('update_checker.log')
    ]
)
logger = logging.getLogger(__name__)

class RBIUpdateChecker:
    """
    Class to check for updates on the RBI website and download new Excel files
    """
    
    def __init__(self, excel_dir="RBI_ATM_Excel", status_file="update_status.json"):
        """Initialize the update checker"""
        self.excel_dir = excel_dir
        self.status_file = status_file
        self.base_url = "https://www.rbi.org.in/Scripts/ATMView.aspx"
        
        # Create Excel directory if it doesn't exist
        os.makedirs(self.excel_dir, exist_ok=True)
        
        # Load previous status
        self.status = self.load_status()
    
    def load_status(self):
        """Load update status from file"""
        if os.path.exists(self.status_file):
            try:
                with open(self.status_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading status file: {str(e)}")
        
        # Default status if file doesn't exist or error occurs
        return {
            'last_checked': None,
            'last_updated': None,
            'known_files': [],
            'new_data_available': False
        }
    
    def save_status(self):
        """Save update status to file"""
        try:
            with open(self.status_file, 'w') as f:
                json.dump(self.status, f, indent=2)
            logger.info("Status file updated")
        except Exception as e:
            logger.error(f"Error saving status file: {str(e)}")
    
    def _fetch_year_page(self, session, year: int) -> list:
        """Return Excel links for a given year using the ASP.NET form"""
        try:
            # Load base page to get hidden form fields
            r = session.get(self.base_url, timeout=30, verify=False)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")

            viewstate = soup.find("input", id="__VIEWSTATE")["value"]
            viewgen = soup.find("input", id="__VIEWSTATEGENERATOR")["value"]
            eventval = soup.find("input", id="__EVENTVALIDATION")["value"]

            payload = {
                "__VIEWSTATE": viewstate,
                "__VIEWSTATEGENERATOR": viewgen,
                "__EVENTVALIDATION": eventval,
                "hdnYear": str(year),
                "hdnMonth": "0",  # All months
                "UsrFontCntr$btn": "",
            }

            r2 = session.post(self.base_url, data=payload, timeout=30, verify=False)
            r2.raise_for_status()
            soup2 = BeautifulSoup(r2.text, "html.parser")

            links = []
            for a in soup2.find_all("a", href=True):
                href = a["href"]
                if href.lower().endswith((".xls", ".xlsx")):
                    full_url = href if href.startswith("http") else "https://www.rbi.org.in" + href
                    filename = full_url.split("/")[-1]
                    links.append((full_url, filename))
            return links
        except Exception as e:
            logger.error(f"Error fetching data for year {year}: {str(e)}")
            return []

    def get_available_excel_files(self):
        """Get list of all Excel files across available years"""
        logger.info("Checking for available Excel files on RBI website")

        session = requests.Session()
        current_year = datetime.now().year
        all_links = []

        for year in range(2000, current_year + 1):
            year_links = self._fetch_year_page(session, year)
            logger.info(f"Year {year}: found {len(year_links)} files")
            all_links.extend(year_links)

        # Deduplicate by filename
        unique = {}
        for url, filename in all_links:
            unique[filename] = url

        excel_links = [(url, fname) for fname, url in unique.items()]
        logger.info(f"Total unique Excel files found: {len(excel_links)}")
        return excel_links
    
    def check_for_updates(self):
        """Check if new Excel files are available"""
        logger.info("Checking for updates")
        
        # Update last checked timestamp
        self.status['last_checked'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Get available Excel files
        excel_links = self.get_available_excel_files()
        if not excel_links:
            logger.warning("No Excel files found or error occurred")
            self.status['new_data_available'] = False
            self.save_status()
            return False
        
        # Check if there are new files
        current_filenames = [filename for _, filename in excel_links]
        new_files = [filename for filename in current_filenames if filename not in self.status['known_files']]
        
        if new_files:
            logger.info(f"Found {len(new_files)} new Excel files")
            self.status['new_data_available'] = True
            self.save_status()
            return True
        else:
            logger.info("No new Excel files found")
            self.status['new_data_available'] = False
            self.save_status()
            return False
    
    def download_new_files(self, all_files: bool = False):
        """Download new or all Excel files"""
        action = "all" if all_files else "new"
        logger.info(f"Downloading {action} Excel files")
        
        # Get available Excel files
        excel_links = self.get_available_excel_files()
        if not excel_links:
            logger.warning("No Excel files found or error occurred")
            return []
        
        # Filter for new files
        current_filenames = [filename for _, filename in excel_links]
        if all_files:
            new_files = excel_links
            current_filenames = [fname for _, fname in excel_links]
        else:
            new_files = [(url, filename) for url, filename in excel_links if filename not in self.status['known_files']]
        
        # Download new files
        downloaded_files = []
        for url, filename in new_files:
            logger.info(f"Downloading {filename}")
            try:
                r = requests.get(url)
                r.raise_for_status()
                file_path = os.path.join(self.excel_dir, filename)
                with open(file_path, "wb") as f:
                    f.write(r.content)
                downloaded_files.append(file_path)
                logger.info(f"Successfully downloaded {filename}")
            except Exception as e:
                logger.error(f"Error downloading {filename}: {str(e)}")
        
        # Update status
        self.status['known_files'] = current_filenames
        self.status['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.status['new_data_available'] = False
        self.save_status()
        
        return downloaded_files
    
    def get_update_status(self):
        """Get current update status"""
        return self.status

def check_for_updates():
    """Function to check for updates on the RBI website"""
    checker = RBIUpdateChecker()
    has_updates = checker.check_for_updates()
    return checker.get_update_status()

def download_updates(all_files: bool = False):
    """Function to download updates from the RBI website"""
    checker = RBIUpdateChecker()
    downloaded_files = checker.download_new_files(all_files=all_files)
    return {
        'status': checker.get_update_status(),
        'downloaded_files': downloaded_files
    }

if __name__ == "__main__":
    # Check for updates
    status = check_for_updates()
    print(f"Update status: {status}")
    
    # Download updates if available
    if status['new_data_available']:
        result = download_updates()
        print(f"Downloaded {len(result['downloaded_files'])} new files")
