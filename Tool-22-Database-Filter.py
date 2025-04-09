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


def is_discord_url(url):
    """Check if the URL is a Discord server URL."""
    return (
        url and isinstance(url, str) and ("discord.gg" in url or "discord.com" in url)
    )


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
    urls_file = output_dir / "Final-URLs.json"
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

    # Read and process the main database
    try:
        print(f"\nReading input database from {input_file}...")
        with open(input_file, "r") as f:
            accounts_data = json.load(f)
        print(f"Successfully loaded {len(accounts_data)} accounts from input database")
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"ERROR: Could not read input file: {e}")
        return

    print("\nProcessing accounts data...")
    processed_count = 0

    # Process each account
    for account_key, account_info in accounts_data.items():
        processed_count += 1
        if processed_count % 100 == 0:  # Log progress every 100 accounts
            print(f"Processing account {processed_count}/{len(accounts_data)}...")

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
                if (
                    new_discord_ids % 10 == 0
                ):  # Log less frequently to avoid excessive output
                    print(
                        f"  Added new Discord ID: {discord_id} (Type: {account_type})"
                    )

        # Process URLs
        final_url = account_info.get("FINAL_URL")

        if final_url and final_url != "":
            found_date = convert_date_to_epoch(account_info.get("FOUND_ON", ""))

            # Check if it's a Discord server URL
            if is_discord_url(final_url):
                if final_url not in discord_servers_data:
                    discord_servers_data[final_url] = {"FOUND_ON": found_date}
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
        if surface_url and surface_url != "" and is_discord_url(surface_url):
            if surface_url not in discord_servers_data:
                found_date = convert_date_to_epoch(account_info.get("FOUND_ON", ""))
                discord_servers_data[surface_url] = {"FOUND_ON": found_date}
                new_discord_servers += 1
                if new_discord_servers % 10 == 0:
                    print(
                        f"  Added new Discord server URL (from surface): {surface_url}"
                    )

    print(f"\nProcessed all {processed_count} accounts")
    print(f"Found {new_discord_ids} new Discord IDs")
    print(f"Found {new_urls} new URLs")
    print(f"Found {new_discord_servers} new Discord server URLs")

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
        print(
            f"Written {len(discord_servers_data)} Discord servers to {discord_servers_file}"
        )

    print("\n" + "=" * 80)
    print(f"PROCESS COMPLETE")
    print(f"Total Discord IDs: {len(discord_ids_data)} ({new_discord_ids} new)")
    print(f"Total URLs: {len(urls_data)} ({new_urls} new)")
    print(
        f"Total Discord servers: {len(discord_servers_data)} ({new_discord_servers} new)"
    )
    print("=" * 80 + "\n")


if __name__ == "__main__":
    process_database()
