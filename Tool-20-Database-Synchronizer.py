#!/usr/bin/env python3
import json
import os


def load_json_file(file_path):
    """Load and return JSON data from the specified file."""
    try:
        with open(file_path, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Warning: File not found - {file_path}")
        return None
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in {file_path}")
        return None


def save_json_file(file_path, data):
    """Save JSON data to the specified file."""
    # Ensure directory exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    with open(file_path, "w") as file:
        json.dump(data, file, indent=4)
    print(f"Updated: {file_path}")


def sync_files():
    """Synchronize files from Edit-Database to Main-Database and Backup-Database."""
    # Define file paths
    file_mappings = {
        "../Database-Files/Edit-Database/Active-Discord-Servers.json": [
            "../Database-Files/Main-Database/Active-Discord-Servers.json",
            "../Database-Files/Recovery-Database/Active-Discord-Servers.json",
            "../Database-Files/Backup-Database/Active-Discord-Servers.json",
        ],
        "../Database-Files/Edit-Database/Compromised-Discord-Accounts.json": [
            "../Database-Files/Main-Database/Compromised-Discord-Accounts.json",
            "../Database-Files/Recovery-Database/Compromised-Discord-Accounts.json",
            "../Database-Files/Backup-Database/Compromised-Discord-Accounts.json",
        ],
    }

    # Synchronize each source file to destination files
    for source_file, dest_files in file_mappings.items():
        # Load source data
        source_data = load_json_file(source_file)
        if source_data is None:
            print(f"Skipping synchronization for {source_file} due to loading error")
            continue

        # Update each destination file if needed
        for dest_file in dest_files:
            dest_data = load_json_file(dest_file)

            # If destination data differs from source or doesn't exist, update it
            if dest_data != source_data:
                print(f"Difference detected between {source_file} and {dest_file}")
                save_json_file(dest_file, source_data)
            else:
                print(f"No update needed for {dest_file} (identical to source)")


if __name__ == "__main__":
    print("Starting database synchronization...")
    sync_files()
    print("Synchronization complete.")
