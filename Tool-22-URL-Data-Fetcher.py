import os
import json
import requests
import time
from datetime import datetime

# Configuration
OUTPUT_DIR = "../Database-Files/Filter-Database/"
OUTPUT_FILE = "Global-URLs.json"
OUTPUT_PATH = os.path.join(OUTPUT_DIR, OUTPUT_FILE)

# Sources
SOURCES = [
    {
        "name": "FishFish API",
        "url": "https://api.fishfish.gg/v1/domains",
        "headers": {
            "User-Agent": "DART Project - Discord Analytics for Risks & Threats (https://github.com/TheDARTProject)"
        },
        "type": "direct",
    },
    {
        "name": "DSP Project",
        "url": "https://raw.githubusercontent.com/Discord-AntiScam/scam-links/refs/heads/main/list.json",
        "headers": {},
        "type": "direct",
    },
    {
        "name": "DART Project",
        "url": "https://raw.githubusercontent.com/TheDARTProject/Database-Files/refs/heads/main/Main-Database/Compromised-Discord-Accounts.json",
        "headers": {},
        "type": "extract",
        "fields": ["SURFACE_URL", "FINAL_URL"],
        "exclude_values": ["No URL Sent", "No URL Detected"],
    },
]


def ensure_output_directory():
    """Ensure that the output directory exists."""
    if not os.path.exists(OUTPUT_DIR):
        print(f"[+] Creating output directory: {OUTPUT_DIR}")
        os.makedirs(OUTPUT_DIR, exist_ok=True)
    else:
        print(f"[+] Output directory exists: {OUTPUT_DIR}")


def fetch_data(source):
    """Fetch data from a source."""
    print(f"[+] Fetching data from {source['name']} ({source['url']})")
    try:
        response = requests.get(source["url"], headers=source["headers"], timeout=30)
        response.raise_for_status()
        data = response.json()

        # If it's a direct URL list, return it as is
        if source["type"] == "direct":
            return data

        # If we need to extract URLs from specific fields
        elif source["type"] == "extract":
            extracted_urls = []
            # For DART Compromised Accounts format
            for account_id, account_data in data.items():
                for field in source["fields"]:
                    if field in account_data:
                        url = account_data[field]
                        # Filter out excluded values
                        if url and url not in source["exclude_values"]:
                            extracted_urls.append(url)
            print(f"[+] Extracted {len(extracted_urls)} URLs from {source['name']}")
            return extracted_urls

        return []
    except requests.exceptions.RequestException as e:
        print(f"[!] Error fetching data from {source['name']}: {e}")
        return []
    except json.JSONDecodeError as e:
        print(f"[!] Error decoding JSON from {source['name']}: {e}")
        return []


def load_existing_urls():
    """Load existing URLs from the output file if it exists."""
    if os.path.exists(OUTPUT_PATH):
        print(f"[+] Loading existing URLs from {OUTPUT_PATH}")
        try:
            with open(OUTPUT_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"[!] Error decoding JSON from {OUTPUT_PATH}, starting fresh")
            return []
    else:
        print(f"[+] No existing URL file found, creating a new one")
        return []


def save_urls(urls):
    """Save URLs to the output file."""
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(urls, f, indent=2)
    print(f"[+] Saved {len(urls)} URLs to {OUTPUT_PATH}")


def main():
    """Main function to fetch and process URLs."""
    start_time = time.time()
    print(
        f"[+] Starting URL collection at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )

    # Ensure output directory exists
    ensure_output_directory()

    # Load existing URLs if any
    existing_urls = load_existing_urls()
    existing_count = len(existing_urls)
    print(f"[+] Found {existing_count} existing URLs")

    # Create a set for faster lookups and to ensure uniqueness
    url_set = set(existing_urls)

    # Fetch and process each source
    total_new_urls = 0
    source_stats = {}

    for source in SOURCES:
        source_data = fetch_data(source)
        if not source_data:
            print(f"[!] No data retrieved from {source['name']}, skipping")
            source_stats[source["name"]] = 0
            continue

        # Count new URLs from this source
        new_from_source = 0
        for url in source_data:
            if url not in url_set:
                url_set.add(url)
                new_from_source += 1

        total_new_urls += new_from_source
        source_stats[source["name"]] = new_from_source
        print(f"[+] Added {new_from_source} new URLs from {source['name']}")

    # Convert set back to sorted list for saving
    all_urls = sorted(list(url_set))

    # Save results
    save_urls(all_urls)

    # Print summary
    end_time = time.time()
    print(f"[+] URL collection completed in {end_time - start_time:.2f} seconds")
    print(f"[+] Summary:")
    print(f"    - Starting URLs: {existing_count}")
    print(f"    - New URLs added: {total_new_urls}")
    print(f"    - Total unique URLs: {len(all_urls)}")

    # Print breakdown by source
    print(f"[+] New URLs by source:")
    for source_name, count in source_stats.items():
        print(f"    - {source_name}: {count} new URLs")

    if total_new_urls > 0:
        print(f"[+] Updated {OUTPUT_PATH} with {total_new_urls} new URLs")
    else:
        print(f"[+] No new URLs found, database is up to date")


if __name__ == "__main__":
    main()
