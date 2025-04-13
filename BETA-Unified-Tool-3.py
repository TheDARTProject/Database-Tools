import os
import json
import requests
import time
from datetime import datetime
from urllib.parse import urlparse
from dotenv import load_dotenv

# ======================
# Constants
# ======================
URL_OUTPUT_DIR = "../Database-Files/Filter-Database/"
URL_OUTPUT_FILE = "Global-Domains.json"
URL_OUTPUT_PATH = os.path.join(URL_OUTPUT_DIR, URL_OUTPUT_FILE)
DISCORD_SERVERS_PATH = "../Database-Files/Filter-Database/Discord-Servers.json"
COMPROMISED_DB_PATH = (
    "../Database-Files/Main-Database/Compromised-Discord-Accounts.json"
)
DISCORD_IDS_PATH = "../Database-Files/Filter-Database/Discord-IDs.json"


# ======================
# Utility Functions
# ======================


def print_header(title):
    """Print a formatted header for tool sections."""
    print(f"\n{'=' * 50}")
    print(f"{title.upper():^50}")
    print(f"{'=' * 50}\n")


def log_message(message):
    """Print formatted log messages with timestamp."""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}")


def ensure_directory(directory):
    """Ensure that the directory exists."""
    if not os.path.exists(directory):
        log_message(f"Creating directory: {directory}")
        os.makedirs(directory, exist_ok=True)
    else:
        log_message(f"Directory exists: {directory}")


# ======================
# URL Data Fetcher
# ======================


def run_url_data_fetcher():
    """Run the URL Data Fetcher tool."""
    print_header("URL Data Fetcher")

    start_time = time.time()
    log_message("Starting URL collection")

    # Load environment variables
    load_dotenv()
    EXCLUDED_DOMAINS = os.getenv("EXCLUDED_DOMAINS", "").split(",")

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

    # Ensure output directory exists
    ensure_directory(URL_OUTPUT_DIR)

    # Load existing URLs if any
    existing_urls = load_existing_urls()
    existing_count = len(existing_urls)
    log_message(f"Found {existing_count} existing URLs")

    # Create a set of base domains for existing URLs
    existing_base_domains = {get_base_domain(url) for url in existing_urls}

    # Initialize counters
    total_new_urls = 0
    total_skipped_urls = 0
    source_stats = {}

    # We'll store both the full URL and its base domain to maintain uniqueness
    url_dict = {url: get_base_domain(url) for url in existing_urls}

    for source in SOURCES:
        source_data = fetch_data(source)
        if not source_data:
            log_message(f"No data retrieved from {source['name']}, skipping")
            source_stats[source["name"]] = 0
            continue

        # Count new URLs from this source
        new_from_source = 0
        for url in source_data:
            # Skip excluded URLs
            if is_url_excluded(url, EXCLUDED_DOMAINS):
                total_skipped_urls += 1
                continue

            base_domain = get_base_domain(url)

            # Check if this base domain already exists
            if base_domain not in existing_base_domains:
                # Add the simplest form of the URL (just domain)
                simple_url = base_domain
                url_dict[simple_url] = base_domain
                existing_base_domains.add(base_domain)
                new_from_source += 1

        total_new_urls += new_from_source
        source_stats[source["name"]] = new_from_source
        log_message(f"Added {new_from_source} new URLs from {source['name']}")

    # Convert to sorted list of just the domains (no paths)
    all_urls = sorted({k for k, v in url_dict.items()})

    # Save results
    save_urls(all_urls)

    # Print summary
    end_time = time.time()
    log_message(f"URL collection completed in {end_time - start_time:.2f} seconds")
    log_message(f"Summary:")
    log_message(f"    - Starting URLs: {existing_count}")
    log_message(f"    - New URLs added: {total_new_urls}")
    log_message(f"    - Total unique URLs: {len(all_urls)}")
    log_message(f"    - Total URLs skipped/excluded: {total_skipped_urls}")

    # Print breakdown by source
    log_message(f"New URLs by source:")
    for source_name, count in source_stats.items():
        log_message(f"    - {source_name}: {count} new URLs")

    if total_new_urls > 0:
        log_message(f"Updated {URL_OUTPUT_PATH} with {total_new_urls} new URLs")
    else:
        log_message(f"No new URLs found, database is up to date")


def load_existing_urls():
    """Load existing URLs from the output file if it exists."""
    if os.path.exists(URL_OUTPUT_PATH):
        log_message(f"Loading existing URLs from {URL_OUTPUT_PATH}")
        try:
            with open(URL_OUTPUT_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            log_message(f"Error decoding JSON from {URL_OUTPUT_PATH}, starting fresh")
            return []
    else:
        log_message(f"No existing URL file found, creating a new one")
        return []


def save_urls(urls):
    """Save URLs to the output file."""
    with open(URL_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(urls, f, indent=2)
    log_message(f"Saved {len(urls)} URLs to {URL_OUTPUT_PATH}")


def is_url_excluded(url, excluded_domains):
    """Check if the URL contains any excluded domain."""
    domain = urlparse(url).netloc
    for excluded_domain in excluded_domains:
        if excluded_domain and excluded_domain in domain:
            return True
    return False


def get_base_domain(url):
    """Extract the base domain from a URL (without www or subdomains)."""
    try:
        # Handle cases where URL might not have scheme
        if not url.startswith(("http://", "https://")):
            url = "http://" + url

        parsed = urlparse(url)
        domain_parts = parsed.netloc.split(".")

        # Handle cases like 'example.com' or 'www.example.com'
        if len(domain_parts) > 2:
            # For subdomains, we take the last two parts (e.g., 'example.com' from 'sub.example.com')
            base_domain = ".".join(domain_parts[-2:])
        else:
            base_domain = parsed.netloc

        # Remove www. if present
        if base_domain.startswith("www."):
            base_domain = base_domain[4:]

        return base_domain.lower()
    except:
        # Fallback for malformed URLs
        return url.lower()


def fetch_data(source):
    """Fetch data from a source."""
    log_message(f"Fetching data from {source['name']} ({source['url']})")
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
                            # Strip 'http://' or 'https://' from URLs for DART Project
                            if source["name"] == "DART Project":
                                url = url.replace("https://", "").replace("http://", "")
                            extracted_urls.append(url)
            log_message(f"Extracted {len(extracted_urls)} URLs from {source['name']}")
            return extracted_urls

        return []
    except requests.exceptions.RequestException as e:
        log_message(f"Error fetching data from {source['name']}: {e}")
        return []
    except json.JSONDecodeError as e:
        log_message(f"Error decoding JSON from {source['name']}: {e}")
        return []


# ======================
# Discord Invite Fetcher
# ======================


def run_discord_invite_fetcher():
    """Run the Discord Invite Fetcher tool."""
    print_header("Discord Invite Fetcher")

    start_time = time.time()
    log_message("Starting Discord server database update")

    api_url = "https://api.phish.gg/servers/all"

    # Define headers with User-Agent
    headers = {
        "User-Agent": "DART Project - Discord Analytics for Risks & Threats (https://github.com/TheDARTProject)"
    }

    database = load_database(DISCORD_SERVERS_PATH)

    is_old_format = any(key.startswith("http") for key in database.keys())
    if is_old_format:
        database = convert_database_format(database)

    log_message("Normalizing existing entries")
    for key, entry in database.items():
        entry["INVITE_URL"] = normalize_invite_url(entry.get("INVITE_URL", ""))
        database[key] = normalize_entry(entry)

    existing_invite_codes = {
        extract_invite_code(entry.get("INVITE_URL", "")) for entry in database.values()
    }

    # Fetch data from API with User-Agent header
    log_message(f"Fetching data from {api_url} with custom User-Agent")
    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        servers = response.json()
        log_message(f"Successfully fetched data: {len(servers)} servers found")
    except requests.RequestException as e:
        log_message(f"Error fetching data from API: {e}")
        servers = []

    # Load compromised accounts (even if unused now)
    try:
        with open(COMPROMISED_DB_PATH, "r") as file:
            compromised_accounts = json.load(file)
    except Exception as e:
        log_message(f"Error loading compromised accounts: {e}")
        compromised_accounts = {}

    # Process new servers
    new_entries_added = 0
    for server in servers:
        server_id = server.get("serverID", "UNKNOWN")
        raw_invite = server.get("invite", "")
        reason = server.get("reason", "UNKNOWN")

        if not raw_invite:
            continue

        normalized_url = normalize_invite_url(
            f"https://discord.com/invite/{raw_invite}"
        )
        invite_code = extract_invite_code(normalized_url)

        if invite_code.lower() in existing_invite_codes:
            continue

        found_on = snowflake_to_timestamp(server_id)

        new_entry = {
            "INVITE_URL": normalized_url,
            "FOUND_ON": found_on,
            "SERVER_ID": server_id,
            "REASON": reason,
            "SERVER_STATUS": "UNKNOWN",
            "SERVER_STATUS_CHANGE": "UNKNOWN",
            "INVITE_STATUS": "UNKNOWN",
            "INVITE_STATUS_CHANGE": "UNKNOWN",
        }

        database[f"DISCORD_SERVER_{len(database) + 1}"] = normalize_entry(new_entry)
        existing_invite_codes.add(invite_code.lower())
        new_entries_added += 1

    log_message(f"New entries added: {new_entries_added}")
    database = renumber_database(database)
    save_database(DISCORD_SERVERS_PATH, database)

    elapsed_time = time.time() - start_time
    log_message(f"Update completed in {elapsed_time:.2f} seconds")


def snowflake_to_timestamp(snowflake):
    """Convert Discord snowflake to timestamp."""
    try:
        discord_epoch = 1420070400000
        timestamp = ((int(snowflake) >> 22) + discord_epoch) // 1000
        return timestamp
    except (ValueError, TypeError):
        return int(datetime.now().timestamp())


def load_database(file_path):
    """Load database from file path."""
    try:
        log_message(f"Loading database from {file_path}")
        with open(file_path, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        log_message(f"Database file not found or invalid. Creating new database")
        return {}


def save_database(file_path, data):
    """Save database to file path."""
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        log_message(f"Creating directory: {directory}")
        os.makedirs(directory)

    log_message(f"Saving database to {file_path}")
    with open(file_path, "w") as file:
        json.dump(data, file, indent=4)
    log_message(f"Database saved successfully")


def normalize_entry(entry):
    """Normalize database entry."""
    required_fields = ["INVITE_URL", "FOUND_ON", "SERVER_ID", "REASON"]
    for field in required_fields:
        if field not in entry:
            entry[field] = "UNKNOWN"
    for field in [
        "SERVER_STATUS",
        "SERVER_STATUS_CHANGE",
        "INVITE_STATUS",
        "INVITE_STATUS_CHANGE",
    ]:
        entry.setdefault(field, "UNKNOWN")
    return entry


def normalize_invite_url(url):
    """Normalize Discord invite URL."""
    try:
        parts = url.split("/")
        for i, part in enumerate(parts):
            if part == "invite" and i + 1 < len(parts):
                return f"https://discord.com/invite/{parts[i + 1]}"
        return url
    except:
        return url


def extract_invite_code(url):
    """Extract invite code from URL."""
    try:
        url = normalize_invite_url(url)
        parts = url.lower().split("/")
        return parts[-1] if parts[-1] else ""
    except:
        return ""


def convert_database_format(old_database):
    """Convert old database format to new format."""
    log_message("Converting database to new format")
    new_database = {}
    count = 1
    processed_codes = set()

    for _, data in old_database.items():
        url = normalize_invite_url(data.get("INVITE_URL", ""))
        code = extract_invite_code(url)
        if code in processed_codes:
            continue

        new_entry = {
            "INVITE_URL": url,
            "FOUND_ON": data.get("FOUND_ON", "UNKNOWN"),
            "SERVER_ID": data.get("SERVER_ID", "UNKNOWN"),
            "REASON": data.get("REASON", "UNKNOWN"),
            "SERVER_STATUS": "UNKNOWN",
            "SERVER_STATUS_CHANGE": "UNKNOWN",
            "INVITE_STATUS": "UNKNOWN",
            "INVITE_STATUS_CHANGE": "UNKNOWN",
        }

        new_database[f"DISCORD_SERVER_{count}"] = normalize_entry(new_entry)
        processed_codes.add(code)
        count += 1

    log_message(f"Converted {count - 1} entries to new format")
    return new_database


def renumber_database(database):
    """Renumber database entries sequentially."""
    log_message("Renumbering database entries sequentially")
    new_database = {}
    count = 1
    for _, entry in database.items():
        new_database[f"DISCORD_SERVER_{count}"] = entry
        count += 1
    log_message(f"Renumbered {len(new_database)} entries")
    return new_database


# ======================
# Discord ID Fetcher
# ======================


def run_discord_id_fetcher():
    """Run the Discord ID Fetcher tool."""
    print_header("Discord ID Fetcher")

    log_message(f"Starting Discord ID database update")

    # Check if files exist
    if not os.path.exists(COMPROMISED_DB_PATH):
        log_message(
            f"Error: Compromised accounts file not found at {COMPROMISED_DB_PATH}"
        )
        return

    # Load the compromised accounts data
    try:
        with open(COMPROMISED_DB_PATH, "r", encoding="utf-8") as f:
            compromised_data = json.load(f)
        log_message(
            f"Successfully loaded compromised accounts data ({len(compromised_data)} entries)"
        )
    except json.JSONDecodeError as e:
        log_message(f"Error: Failed to parse compromised accounts file: {e}")
        return
    except Exception as e:
        log_message(f"Error: Failed to load compromised accounts file: {e}")
        return

    # Load the existing filter data if it exists
    filter_data = {}
    if os.path.exists(DISCORD_IDS_PATH):
        try:
            with open(DISCORD_IDS_PATH, "r", encoding="utf-8") as f:
                filter_data = json.load(f)
            log_message(
                f"Successfully loaded existing filter data ({len(filter_data)} entries)"
            )
        except json.JSONDecodeError:
            log_message(
                f"Warning: Filter file exists but is not valid JSON, will create new file"
            )
        except Exception as e:
            log_message(f"Error: Failed to load filter file: {e}")
            return

    # Counter for new entries
    new_entries = 0

    # Process each account in the compromised data
    for account_key, account_info in compromised_data.items():
        discord_id = account_info.get("DISCORD_ID", "")

        # Skip if discord ID is empty or already in filter data
        if not discord_id or discord_id in filter_data:
            continue

        # Determine the TYPE based on ACCOUNT_STATUS
        account_status = account_info.get("ACCOUNT_STATUS", "").upper()
        if account_status == "OPERATIONAL":
            account_type = "THREAT"
        elif account_status == "COMPROMISED":
            account_type = "USER"
        elif account_status == "DELETED":
            account_type = "DELETED"
        else:
            account_type = "UNKNOWN"

        # Convert found date to epoch time
        found_on_date = account_info.get("FOUND_ON", "")
        epoch_time = convert_date_to_epoch(found_on_date)

        # Add to filter data
        filter_data[discord_id] = {"FOUND_ON": epoch_time, "TYPE": account_type}

        new_entries += 1

    # Save the updated filter data
    try:
        # Ensure directory exists
        directory = os.path.dirname(DISCORD_IDS_PATH)
        if not os.path.exists(directory):
            log_message(f"Creating directory: {directory}")
            os.makedirs(directory)

        with open(DISCORD_IDS_PATH, "w", encoding="utf-8") as f:
            json.dump(filter_data, f, indent=4)
        log_message(f"Successfully saved filter data with {new_entries} new entries")
    except Exception as e:
        log_message(f"Error: Failed to save filter file: {e}")
        return

    log_message(
        f"Process completed: {new_entries} new Discord IDs added to filter database"
    )


def convert_date_to_epoch(date_str):
    """Convert a date string in YYYY-MM-DD format to epoch timestamp."""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return int(dt.timestamp())
    except ValueError:
        # Return current timestamp if date format is invalid
        return int(time.time())


# ======================
# Main Menu
# ======================


def display_menu():
    """Display the main menu and get user choice."""
    print("\n" + "=" * 50)
    print("DART PROJECT UNIFIED TOOLS".center(50))
    print("=" * 50)
    print("\nMain Menu:")
    print("1. Run All Tools (Full Processing)")
    print("2. URL Data Fetcher")
    print("3. Discord Invite Fetcher")
    print("4. Discord ID Fetcher")
    print("5. Exit")

    while True:
        choice = input("\nEnter your choice (1-5): ")
        if choice.isdigit() and 1 <= int(choice) <= 5:
            return int(choice)
        print("Invalid input. Please enter a number between 1 and 5.")


def main():
    """Main function to run the combined tool."""
    while True:
        choice = display_menu()

        if choice == 1:  # Run all tools
            print_header("running all tools")
            run_url_data_fetcher()
            run_discord_invite_fetcher()
            run_discord_id_fetcher()
            print_header("all tools completed")
        elif choice == 2:
            run_url_data_fetcher()
        elif choice == 3:
            run_discord_invite_fetcher()
        elif choice == 4:
            run_discord_id_fetcher()
        elif choice == 5:
            print("\nExiting the program. Goodbye!")
            break

        input("\nPress Enter to return to the main menu...")


if __name__ == "__main__":
    main()
