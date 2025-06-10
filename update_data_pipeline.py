"""Utility script to download and process RBI ATM/POS/Card Statistics data."""

from update_checker import download_updates
from excel_parser import RBIExcelParser


def main() -> None:
    """Download new RBI Excel files and process them into CSVs."""
    # Always download all available Excel files to build the full dataset
    download_updates(all_files=True)
    parser = RBIExcelParser()
    parser.process_all_files()
    parser.save_processed_data()


if __name__ == "__main__":
    main()
