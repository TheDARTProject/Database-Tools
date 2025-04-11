import json
import requests
import os
import datetime
import time
from urllib.parse import urlparse


# Function to convert Discord snowflake ID to timestamp
def snowflake_to_timestamp(snowflake):
    try:
        discord_epoch = 1420070400000
        timestamp = ((int(snowflake) >> 22) + discord_epoch) // 1000
        return timestamp
    except (ValueError, TypeError):
        return int(datetime.datetime.now().timestamp())


# Function to load existing database
def load_database(file_path):
    try:
        print(f"Loading database from {file_path}...")
        with open(file_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Database file not found. Creating new database.")
        return {}
    except json.JSONDecodeError:
        print(f"Error parsing database file. Creating new database.")
        return {}


# Function to save updated database
def save_database(file_path, data):
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        print(f"Creating directory: {directory}")
        os.makedirs(directory)

    print(f"Saving database to {file_path}...")
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)
    print(f"Database saved successfully.")


# Function to ensure all entries have all required fields
def normalize_entry(entry):
    required_fields = ["INVITE_URL", "FOUND_ON", "SERVER_ID", "REASON"]
    for field in required_fields:
        if field not in entry:
            entry[field] = "UNKNOWN"
    return entry


# Function to convert old format to new format
def convert_database_format(old_database):
    print("Converting database to new format...")
    new_database = {}
    count = 1
    processed_urls = set()

    for url, data in old_database.items():
        normalized_url = url.lower()
        if normalized_url in processed_urls:
            continue

        new_entry = {
            "INVITE_URL": url,
            "FOUND_ON": data.get("FOUND_ON", "UNKNOWN"),
            "SERVER_ID": data.get("SERVER_ID", "UNKNOWN"),
            "REASON": data.get("REASON", "UNKNOWN")
        }

        new_database[f"DISCORD_SERVER_{count}"] = normalize_entry(new_entry)
        processed_urls.add(normalized_url)
        count += 1

    print(f"Converted {count - 1} entries to new format.")
    return new_database


# Function to extract invite code from URL
def extract_invite_code(url):
    try:
        parts = url.lower().split("/")
        return parts[-1] if parts[-1] else ""
    except:
        return ""


# Function to check if invite code already exists in database
def invite_code_exists_in_database(invite_code, database):
    if not invite_code:
        return False
    invite_code = invite_code.lower()
    for entry_data in database.values():
        url = entry_data.get("INVITE_URL", "").lower()
        existing_code = extract_invite_code(url)
        if existing_code == invite_code:
            return True
    return False


# Function to renumber all database entries sequentially
def renumber_database(database):
    print("Renumbering database entries sequentially...")
    new_database = {}
    count = 1
    for _, entry in database.items():
        new_database[f"DISCORD_SERVER_{count}"] = entry
        count += 1
    print(f"Renumbered {len(new_database)} entries.")
    return new_database


# Main function to fetch and process data
def update_discord_servers_database():
    start_time = time.time()
    print("Starting Discord server database update...")

    api_url = "https://api.phish.gg/servers/all"
    db_file_path = "../Database-Files/Filter-Database/Discord-Servers.json"

    database = load_database(db_file_path)

    # Check if old format
    is_old_format = any(key.startswith("http") for key in database.keys())
    if is_old_format:
        database = convert_database_format(database)

    # Normalize entries
    print("Normalizing existing entries...")
    for key, entry in database.items():
        database[key] = normalize_entry(entry)

    # Fetch from API
    print(f"Fetching data from {api_url}...")
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        servers = response.json()
        print(f"Successfully fetched data: {len(servers)} servers found.")
    except requests.RequestException as e:
        print(f"Error fetching data from API: {e}")
        return

    new_entries_data = []
    print("Processing server data...")
    for server in servers:
        server_id = server.get("serverID", "UNKNOWN")
        invite_code = server.get("invite", "")
        reason = server.get("reason", "UNKNOWN")

        if not invite_code:
            continue

        if invite_code_exists_in_database(invite_code, database):
            continue

        found_on = snowflake_to_timestamp(server_id) if server_id != "UNKNOWN" else int(datetime.datetime.now().timestamp())
        url = f"https://discord.com/invite/{invite_code}"

        new_entries_data.append({
            "INVITE_URL": url,
            "FOUND_ON": found_on,
            "SERVER_ID": server_id,
            "REASON": reason
        })

    # Track existing invite codes
    existing_invite_codes = {
        extract_invite_code(entry.get("INVITE_URL", ""))
        for entry in database.values()
    }

    for entry_data in new_entries_data:
        invite_code = extract_invite_code(entry_data["INVITE_URL"])
        if invite_code in existing_invite_codes:
            continue

        highest_num = max(
            [int(k.split("_")[-1]) for k in database if k.startswith("DISCORD_SERVER_")],
            default=0
        )
        new_key = f"DISCORD_SERVER_{highest_num + 1}"
        database[new_key] = entry_data
        existing_invite_codes.add(invite_code)

    database = renumber_database(database)
    save_database(db_file_path, database)

    end_time = time.time()
    print(f"Database update completed in {end_time - start_time:.2f} seconds.")
    print(f"Added {len(new_entries_data)} new entries.")
    print(f"Total entries in database: {len(database)}")


if __name__ == "__main__":
    update_discord_servers_database()