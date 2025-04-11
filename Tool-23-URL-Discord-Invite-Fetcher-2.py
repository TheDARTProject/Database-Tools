import json
import os
import datetime
import re
from pathlib import Path


def convert_date_to_epoch(date_str):
    """Convert a date string (YYYY-MM-DD) to epoch time."""
    try:
        dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        return int(dt.timestamp())
    except ValueError:
        print(f"Warning: Could not parse date '{date_str}', using current time instead")
        return int(datetime.datetime.now().timestamp())


def determine_account_type(account_type):
    """Determine the simplified account type based on the original type."""
    if account_type == "User Accounts":
        return "USER"
    elif account_type == "Burner Accounts":
        return "THREAT"
    elif account_type == "Deleted Accounts":
        return "DELETED"
    elif account_type == "Scraper Accounts":
        return "SCRAPER"
    else:
        print(f"Warning: Unknown account type '{account_type}', defaulting to USER")
        return "USER"  # Default to USER for any unknown types


def is_valid_url(url):
    """Check if the URL is valid and not a placeholder like 'No URL Detected'."""
    if not url or not isinstance(url, str):
        return False

    # Filter out common placeholder values
    invalid_values = [
        "no url detected",
        "no url sent",
        "none",
        "n/a",
        "null",
        "undefined",
    ]

    if url.lower().strip() in invalid_values:
        return False

    # Basic URL validation - check for domain structure
    # This simple check ensures the URL has at least something.domain format
    has_domain_structure = (
            re.search(r"[a-zA-Z0-9][\w.-]*\.[a-zA-Z]{2,}", url) is not None
    )

    return has_domain_structure


def is_discord_url(url):
    """Check if the URL is a Discord server URL."""
    return is_valid_url(url) and ("discord.gg" in url or "discord.com" in url)


def extract_discord_invite_id(url):
    """Extract the invite ID from a Discord URL regardless of format.

    Handles both discord.gg/INVITEID and discord.com/invite/INVITEID formats.
    """
    if not is_discord_url(url):
        return None

    # Match patterns like discord.gg/INVITEID or discord.com/invite/INVITEID
    pattern = r"(?:discord\.gg\/|discord\.com\/invite\/)([a-zA-Z0-9]+)"
    match = re.search(pattern, url, re.IGNORECASE)

    if match:
        return match.group(1).lower()  # Return the ID in lowercase for consistent comparison
    return None


def process_database():
    print("\n" + "=" * 80)
    print("DISCORD DATABASE FILTER TOOL - STARTING PROCESS")
    print("=" * 80)

    # Define file paths
    input_file = Path(
        "../Database-Files/Edit-Database/Compromised-Discord-Accounts.json"
    )
    output_dir = Path("../Database-Files/Filter-Database")
    discord_ids_file = output_dir / "Discord-IDs.json"
    urls_file = output_dir / "Malicious-URLs.json"
    discord_servers_file = output_dir / "Discord-Servers.json"

    print(f"\nInput file: {input_file}")
    print(f"Output directory: {output_dir}")

    # Create output directory if it doesn't exist
    if not output_dir.exists():
        print(f"Creating output directory: {output_dir}")
        output_dir.mkdir(parents=True, exist_ok=True)
    else:
        print(f"Output directory already exists: {output_dir}")

    # Initialize counters
    new_discord_ids = 0
    new_urls = 0
    new_discord_servers = 0
    invalid_urls_skipped = 0
    duplicate_invites_skipped = 0

    # Load existing data if files exist
    discord_ids_data = {}
    urls_data = {}
    discord_servers_data = {}

    if discord_ids_file.exists():
        try:
            with open(discord_ids_file, "r") as f:
                discord_ids_data = json.load(f)
                print(
                    f"\nLoaded {len(discord_ids_data)} existing Discord IDs from {discord_ids_file}"
                )
        except json.JSONDecodeError:
            print(f"Error reading {discord_ids_file}, starting with empty data")
    else:
        print(
            f"\nNo existing Discord IDs file found, will create new file: {discord_ids_file}"
        )

    if urls_file.exists():
        try:
            with open(urls_file, "r") as f:
                urls_data = json.load(f)
                print(f"Loaded {len(urls_data)} existing URLs from {urls_file}")
        except json.JSONDecodeError:
            print(f"Error reading {urls_file}, starting with empty data")
    else:
        print(f"No existing URLs file found, will create new file: {urls_file}")

    if discord_servers_file.exists():
        try:
            with open(discord_servers_file, "r") as f:
                discord_servers_data = json.load(f)
                print(
                    f"Loaded {len(discord_servers_data)} existing Discord servers from {discord_servers_file}"
                )
        except json.JSONDecodeError:
            print(f"Error reading {discord_servers_file}, starting with empty data")
    else:
        print(
            f"No existing Discord servers file found, will create new file: {discord_servers_file}"
        )

    # Convert old format to new format if needed
    # The old format uses URLs as keys, the new format uses DISCORD_SERVER_X as keys
    converted_discord_servers = {}

    # Check if we need to convert the format (if any URL is used as a key)
    needs_conversion = False
    for key in discord_servers_data:
        if is_discord_url(key):
            needs_conversion = True
            break

    # Create a mapping of invite IDs to server keys for deduplication
    invite_id_to_key_map = {}

    if needs_conversion:
        print("\nConverting Discord servers data to new format...")
        server_index = 1

        for key, data in discord_servers_data.items():
            if is_discord_url(key):
                # This is in the old format, extract the invite ID
                invite_id = extract_discord_invite_id(key)

                if invite_id and invite_id in invite_id_to_key_map:
                    # Skip this duplicate
                    duplicate_invites_skipped += 1
                    continue

                # Create new entry in the new format
                new_key = f"DISCORD_SERVER_{server_index}"
                converted_discord_servers[new_key] = {
                    "INVITE_URL": key,
                    "FOUND_ON": data.get("FOUND_ON", 0),
                    "SERVER_ID": "UNKNOWN",
                    "REASON": "UNKNOWN",
                    "SERVER_STATUS": "UNKNOWN",
                    "SERVER_STATUS_CHANGE": "UNKNOWN",
                    "INVITE_STATUS": "UNKNOWN",
                    "INVITE_STATUS_CHANGE": "UNKNOWN"
                }

                if invite_id:
                    invite_id_to_key_map[invite_id] = new_key
                server_index += 1
            else:
                # This is already in the new format, keep it but check for duplicates
                if isinstance(data, dict) and "INVITE_URL" in data:
                    invite_id = extract_discord_invite_id(data["INVITE_URL"])

                    if invite_id:
                        if invite_id in invite_id_to_key_map:
                            # This is a duplicate, skip it
                            duplicate_invites_skipped += 1
                            continue
                        invite_id_to_key_map[invite_id] = key

                converted_discord_servers[key] = data

        if duplicate_invites_skipped > 0:
            print(f"Skipped {duplicate_invites_skipped} duplicate Discord invites during conversion")

        print(f"Converted {len(converted_discord_servers)} Discord servers to new format")
        discord_servers_data = converted_discord_servers
    else:
        # Build the invite ID to key map for deduplication
        for key, data in discord_servers_data.items():
            if isinstance(data, dict) and "INVITE_URL" in data:
                invite_id = extract_discord_invite_id(data["INVITE_URL"])
                if invite_id:
                    invite_id_to_key_map[invite_id] = key

    # Deduplicate existing entries
    if not needs_conversion:  # Only if we didn't already deduplicate during conversion
        print("\nChecking for duplicate Discord invites in existing data...")
        keys_to_remove = set()

        # First pass: identify duplicates
        seen_invite_ids = set()
        for key, data in discord_servers_data.items():
            if isinstance(data, dict) and "INVITE_URL" in data:
                invite_id = extract_discord_invite_id(data["INVITE_URL"])
                if invite_id:
                    if invite_id in seen_invite_ids:
                        keys_to_remove.add(key)
                        duplicate_invites_skipped += 1
                    else:
                        seen_invite_ids.add(invite_id)

        # Second pass: remove duplicates
        for key in keys_to_remove:
            del discord_servers_data[key]

        if duplicate_invites_skipped > 0:
            print(f"Removed {duplicate_invites_skipped} duplicate Discord invites from existing data")
            # Rebuild the mapping after deduplication
            invite_id_to_key_map = {}
            for key, data in discord_servers_data.items():
                if isinstance(data, dict) and "INVITE_URL" in data:
                    invite_id = extract_discord_invite_id(data["INVITE_URL"])
                    if invite_id:
                        invite_id_to_key_map[invite_id] = key

    # Clean existing data - remove any invalid URLs
    urls_before_cleaning = len(urls_data)
    urls_data = {url: data for url, data in urls_data.items() if is_valid_url(url)}
    cleaned_urls = urls_before_cleaning - len(urls_data)

    if cleaned_urls > 0:
        print(f"\nCleaned up {cleaned_urls} invalid URLs from existing data")

    # Read and process the main database
    try:
        print(f"\nReading input database from {input_file}...")
        with open(input_file, "r") as f:
            accounts_data = json.load(f)
        print(f"Successfully loaded {len(accounts_data)} accounts from input database")
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"ERROR: Could not read input file: {e}")
        return

    print("\nProcessing database...")
    processed_count = 0
    duplicate_count = 0

    # Find the next available server index
    next_server_index = 1
    for key in discord_servers_data.keys():
        if key.startswith("DISCORD_SERVER_"):
            try:
                index = int(key.split("_")[2])
                next_server_index = max(next_server_index, index + 1)
            except (ValueError, IndexError):
                pass

    # Process each account
    for account_key, account_info in accounts_data.items():
        processed_count += 1

        # Process Discord IDs
        discord_id = account_info.get("DISCORD_ID")
        if discord_id:
            if discord_id not in discord_ids_data:
                found_date = convert_date_to_epoch(account_info.get("FOUND_ON", ""))
                account_type = determine_account_type(
                    account_info.get("ACCOUNT_TYPE", "")
                )

                discord_ids_data[discord_id] = {
                    "FOUND_ON": found_date,
                    "TYPE": account_type,
                }
                new_discord_ids += 1
                if new_discord_ids % 10 == 0:
                    print(f"  Added new Discord ID: {discord_id} (Type: {account_type})")

        # Process URLs
        final_url = account_info.get("FINAL_URL")
        found_date = convert_date_to_epoch(account_info.get("FOUND_ON", ""))

        if final_url:
            if not is_valid_url(final_url):
                invalid_urls_skipped += 1
                continue

            # Check if it's a Discord server URL
            if is_discord_url(final_url):
                # Extract the invite ID to check for duplicates
                invite_id = extract_discord_invite_id(final_url)

                if invite_id:
                    if invite_id in invite_id_to_key_map:
                        # This is a duplicate, skip it
                        duplicate_count += 1
                        continue

                    # Create a new entry in the new format
                    new_key = f"DISCORD_SERVER_{next_server_index}"
                    discord_servers_data[new_key] = {
                        "INVITE_URL": final_url,
                        "FOUND_ON": found_date,
                        "SERVER_ID": "UNKNOWN",
                        "REASON": "UNKNOWN",
                        "SERVER_STATUS": "UNKNOWN",
                        "SERVER_STATUS_CHANGE": "UNKNOWN",
                        "INVITE_STATUS": "UNKNOWN",
                        "INVITE_STATUS_CHANGE": "UNKNOWN"
                    }
                    invite_id_to_key_map[invite_id] = new_key
                    next_server_index += 1
                    new_discord_servers += 1
                    if new_discord_servers % 10 == 0:
                        print(f"  Added new Discord server URL: {final_url}")
            else:
                # For non-Discord URLs, add to the regular URLs file
                if final_url not in urls_data:
                    urls_data[final_url] = {"FOUND_ON": found_date}
                    new_urls += 1
                    if new_urls % 10 == 0:
                        print(f"  Added new URL: {final_url}")

        # Also check SURFACE_URL for Discord links
        surface_url = account_info.get("SURFACE_URL")
        if surface_url and is_valid_url(surface_url) and is_discord_url(surface_url):
            # Extract the invite ID to check for duplicates
            invite_id = extract_discord_invite_id(surface_url)

            if invite_id:
                if invite_id in invite_id_to_key_map:
                    # This is a duplicate, skip it
                    duplicate_count += 1
                    continue

                # Create a new entry in the new format
                new_key = f"DISCORD_SERVER_{next_server_index}"
                discord_servers_data[new_key] = {
                    "INVITE_URL": surface_url,
                    "FOUND_ON": found_date,
                    "SERVER_ID": "UNKNOWN",
                    "REASON": "UNKNOWN",
                    "SERVER_STATUS": "UNKNOWN",
                    "SERVER_STATUS_CHANGE": "UNKNOWN",
                    "INVITE_STATUS": "UNKNOWN",
                    "INVITE_STATUS_CHANGE": "UNKNOWN"
                }
                invite_id_to_key_map[invite_id] = new_key
                next_server_index += 1
                new_discord_servers += 1
                if new_discord_servers % 10 == 0:
                    print(f"  Added new Discord server URL (from surface): {surface_url}")

    print(f"\nProcessed all {processed_count} accounts")
    print(f"Found {new_discord_ids} new Discord IDs")
    print(f"Found {new_urls} new URLs")
    print(f"Found {new_discord_servers} new Discord server URLs")
    print(f"Skipped {invalid_urls_skipped} invalid URLs")
    print(f"Skipped {duplicate_count} duplicate Discord invites")

    # Write the updated data to files
    print("\nWriting updated data to output files...")

    with open(discord_ids_file, "w") as f:
        json.dump(discord_ids_data, f, indent=4)
        print(f"Written {len(discord_ids_data)} Discord IDs to {discord_ids_file}")

    with open(urls_file, "w") as f:
        json.dump(urls_data, f, indent=4)
        print(f"Written {len(urls_data)} URLs to {urls_file}")

    with open(discord_servers_file, "w") as f:
        json.dump(discord_servers_data, f, indent=4)
        print(f"Written {len(discord_servers_data)} Discord servers to {discord_servers_file}")

    print("\n" + "=" * 80)
    print(f"PROCESS COMPLETE")
    print(f"Total Discord IDs: {len(discord_ids_data)} ({new_discord_ids} new)")
    print(f"Total URLs: {len(urls_data)} ({new_urls} new)")
    print(f"Total Discord servers: {len(discord_servers_data)} ({new_discord_servers} new)")
    print(f"Total invalid URLs skipped: {invalid_urls_skipped}")
    print(f"Total duplicate Discord invites skipped: {duplicate_count + duplicate_invites_skipped}")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    process_database()