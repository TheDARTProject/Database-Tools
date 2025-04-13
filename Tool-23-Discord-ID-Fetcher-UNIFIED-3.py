import json
import os
import time
from datetime import datetime


def convert_date_to_epoch(date_str):
    """Convert a date string in YYYY-MM-DD format to epoch timestamp."""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return int(dt.timestamp())
    except ValueError:
        # Return current timestamp if date format is invalid
        return int(time.time())


def main():
    # Define file paths
    compromised_file = "../Database-Files/Main-Database/Compromised-Discord-Accounts.json"
    filter_file = "../Database-Files/Filter-Database/Discord-IDs.json"

    # Check if files exist
    if not os.path.exists(compromised_file):
        print(f"Error: Compromised accounts file not found at {compromised_file}")
        return

    # Load the compromised accounts data
    try:
        with open(compromised_file, 'r', encoding='utf-8') as f:
            compromised_data = json.load(f)
        print(f"Successfully loaded compromised accounts data ({len(compromised_data)} entries)")
    except json.JSONDecodeError as e:
        print(f"Error: Failed to parse compromised accounts file: {e}")
        return
    except Exception as e:
        print(f"Error: Failed to load compromised accounts file: {e}")
        return

    # Load the existing filter data if it exists
    filter_data = {}
    if os.path.exists(filter_file):
        try:
            with open(filter_file, 'r', encoding='utf-8') as f:
                filter_data = json.load(f)
            print(f"Successfully loaded existing filter data ({len(filter_data)} entries)")
        except json.JSONDecodeError:
            print(f"Warning: Filter file exists but is not valid JSON, will create new file")
        except Exception as e:
            print(f"Error: Failed to load filter file: {e}")
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
        filter_data[discord_id] = {
            "FOUND_ON": epoch_time,
            "TYPE": account_type
        }

        new_entries += 1

    # Save the updated filter data
    try:
        with open(filter_file, 'w', encoding='utf-8') as f:
            json.dump(filter_data, f, indent=4)
        print(f"Successfully saved filter data with {new_entries} new entries")
    except Exception as e:
        print(f"Error: Failed to save filter file: {e}")
        return

    print(f"Process completed: {new_entries} new Discord IDs added to filter database")


if __name__ == "__main__":
    main()