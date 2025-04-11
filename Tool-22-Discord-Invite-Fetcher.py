import json
import requests
import os
import datetime
import time
from urllib.parse import urlparse


def snowflake_to_timestamp(snowflake):
    try:
        discord_epoch = 1420070400000
        timestamp = ((int(snowflake) >> 22) + discord_epoch) // 1000
        return timestamp
    except (ValueError, TypeError):
        return int(datetime.datetime.now().timestamp())


def load_database(file_path):
    try:
        print(f"Loading database from {file_path}...")
        with open(file_path, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        print(f"Database file not found or invalid. Creating new database.")
        return {}


def save_database(file_path, data):
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        print(f"Creating directory: {directory}")
        os.makedirs(directory)

    print(f"Saving database to {file_path}...")
    with open(file_path, "w") as file:
        json.dump(data, file, indent=4)
    print(f"Database saved successfully.")


def normalize_entry(entry):
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
    try:
        parts = url.split("/")
        for i, part in enumerate(parts):
            if part == "invite" and i + 1 < len(parts):
                return f"https://discord.com/invite/{parts[i + 1]}"
        return url
    except:
        return url


def extract_invite_code(url):
    try:
        url = normalize_invite_url(url)
        parts = url.lower().split("/")
        return parts[-1] if parts[-1] else ""
    except:
        return ""


def convert_database_format(old_database):
    print("Converting database to new format...")
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

    print(f"Converted {count - 1} entries to new format.")
    return new_database


def renumber_database(database):
    print("Renumbering database entries sequentially...")
    new_database = {}
    count = 1
    for _, entry in database.items():
        new_database[f"DISCORD_SERVER_{count}"] = entry
        count += 1
    print(f"Renumbered {len(new_database)} entries.")
    return new_database


def update_discord_servers_database():
    start_time = time.time()
    print("Starting Discord server database update...")

    api_url = "https://api.phish.gg/servers/all"
    db_file_path = "../Database-Files/Filter-Database/Discord-Servers.json"
    compromised_db_path = (
        "../Database-Files/Main-Database/Compromised-Discord-Accounts.json"
    )

    database = load_database(db_file_path)

    is_old_format = any(key.startswith("http") for key in database.keys())
    if is_old_format:
        database = convert_database_format(database)

    print("Normalizing existing entries...")
    for key, entry in database.items():
        entry["INVITE_URL"] = normalize_invite_url(entry.get("INVITE_URL", ""))
        database[key] = normalize_entry(entry)

    existing_invite_codes = {
        extract_invite_code(entry.get("INVITE_URL", "")) for entry in database.values()
    }

    # Fetch data from API
    print(f"Fetching data from {api_url}...")
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        servers = response.json()
        print(f"Successfully fetched data: {len(servers)} servers found.")
    except requests.RequestException as e:
        print(f"Error fetching data from API: {e}")
        servers = []

    # Load compromised accounts (even if unused now)
    try:
        with open(compromised_db_path, "r") as file:
            compromised_accounts = json.load(file)
    except Exception as e:
        print(f"Error loading compromised accounts: {e}")
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

    print(f"New entries added: {new_entries_added}")
    database = renumber_database(database)
    save_database(db_file_path, database)

    elapsed_time = time.time() - start_time
    print(f"Update completed in {elapsed_time:.2f} seconds.")


if __name__ == "__main__":
    update_discord_servers_database()
