import json
import string
import re
import openpyxl
from datetime import datetime
from urllib.parse import urlparse
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(message)s")

# Constants
JSON_FILE_PATH = "../Database-Files/Edit-Database/Compromised-Discord-Accounts.json"
EXCEL_FILE_PATH = "../Database-Files/Excel-Import-Export/ExporterSheet.xlsx"


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


def validate_json(file_name):
    """Validate JSON file structure (Tool-07)."""
    print_header("json validation checker")
    try:
        with open(file_name, "r") as file:
            json_data = file.read()
        json.loads(json_data)
        log_message("JSON is valid!")
        return True
    except json.JSONDecodeError as e:
        log_message(f"Invalid JSON! Error: {e}")
        return False
    except FileNotFoundError:
        log_message(f"Error: The file '{file_name}' was not found.")
        return False


# ======================
# Tool Functions
# ======================


def excel_to_json_importer():
    """Import data from Excel to JSON (Tool-04)."""
    print_header("excel to json importer")

    # Open the Excel file
    log_message(f"Loading Excel file from {EXCEL_FILE_PATH}...")
    try:
        workbook = openpyxl.load_workbook(EXCEL_FILE_PATH)
        worksheet = workbook.active
    except Exception as e:
        log_message(f"Error loading Excel file: {str(e)}")
        return

    # Load existing data from JSON
    log_message(f"Loading JSON data from {JSON_FILE_PATH}...")
    try:
        if os.path.exists(JSON_FILE_PATH):
            with open(JSON_FILE_PATH, "r", encoding="utf-8") as file:
                data = json.load(file)
        else:
            data = {}
            log_message("JSON file not found, starting with empty dataset")
    except Exception as e:
        log_message(f"Error loading JSON file: {str(e)}")
        return

    # Create tracking dictionary {DISCORD_ID: {FOUND_ON_SERVER: account_key}}
    existing_entries = {}
    for account_key, account_data in data.items():
        discord_id = account_data.get("DISCORD_ID", "Unknown")
        found_on_server = account_data.get("FOUND_ON_SERVER", "UNKNOWN")

        if discord_id not in existing_entries:
            existing_entries[discord_id] = {}
        existing_entries[discord_id][found_on_server] = account_key

    # Counters
    json_case_count = len(data)
    excel_case_count = 0
    new_cases = 0
    skipped_cases = 0
    invalid_cases = 0

    # Process Excel rows
    for row_number, row in enumerate(
        worksheet.iter_rows(min_row=2, values_only=True), start=1
    ):
        excel_case_count += 1

        # Unpack row data
        try:
            (
                NOUMBER,
                FOUND_ON,
                FOUND_ON_SERVER,
                DISCORD_ID,
                USERNAME,
                BEHAVIOUR,
                TYPE,
                METHOD,
                TARGET,
                PLATFORM,
                SURFACE_URL,
                REGION,
                STATUS,
            ) = row
        except ValueError as e:
            log_message(f"Row {row_number} has incorrect number of columns: {str(e)}")
            invalid_cases += 1
            continue

        # Prepare values
        discord_id_str = str(DISCORD_ID) if DISCORD_ID is not None else "Unknown"
        found_on_server_str = (
            str(FOUND_ON_SERVER) if FOUND_ON_SERVER is not None else "UNKNOWN"
        )

        # Skip invalid cases
        if discord_id_str == "Unknown":
            skipped_cases += 1
            continue

        if not any(
            [
                FOUND_ON,
                DISCORD_ID,
                USERNAME,
                BEHAVIOUR,
                TYPE,
                METHOD,
                TARGET,
                PLATFORM,
                SURFACE_URL,
                REGION,
                STATUS,
            ]
        ):
            invalid_cases += 1
            continue

        # Check if case exists
        case_exists = False
        if discord_id_str in existing_entries:
            if found_on_server_str in existing_entries[discord_id_str]:
                case_exists = True

        if case_exists:
            skipped_cases += 1
            continue

        # Add new case
        new_cases += 1
        found_on_str = FOUND_ON.strftime("%Y-%m-%d") if FOUND_ON else "Unknown"
        surface_url_domain = urlparse(SURFACE_URL).netloc if SURFACE_URL else ""
        non_ascii_username = not USERNAME.isascii() if USERNAME else False

        account = {
            "CASE_NUMBER": str(len(data) + 1),
            "FOUND_ON": found_on_str,
            "FOUND_ON_SERVER": found_on_server_str,
            "DISCORD_ID": discord_id_str,
            "USERNAME": USERNAME if USERNAME is not None else "Unknown",
            "ACCOUNT_STATUS": "UNKNOWN",
            "ACCOUNT_TYPE": "UNKNOWN",
            "ACCOUNT_CREATION": "",
            "BEHAVIOUR": BEHAVIOUR if BEHAVIOUR is not None else "Unknown",
            "ATTACK_METHOD": TYPE if TYPE is not None else "Unknown",
            "ATTACK_VECTOR": METHOD if METHOD is not None else "Unknown",
            "ATTACK_GOAL": TARGET if TARGET is not None else "Unknown",
            "ATTACK_SURFACE": PLATFORM if PLATFORM is not None else "Unknown",
            "SUSPECTED_REGION_OF_ORIGIN": REGION if REGION is not None else "Unknown",
            "SURFACE_URL": SURFACE_URL if SURFACE_URL is not None else "Unknown",
            "SURFACE_URL_DOMAIN": surface_url_domain,
            "SURFACE_URL_STATUS": STATUS if STATUS is not None else "Unknown",
            "FINAL_URL": "",
            "FINAL_URL_DOMAIN": "",
            "FINAL_URL_STATUS": "",
            "NON_ASCII_USERNAME": non_ascii_username,
            "LAST_CHECK": datetime.now().isoformat(),
        }

        new_key = f"ACCOUNT_NUMBER_{len(data) + 1}"
        data[new_key] = account

        # Update tracking
        if discord_id_str not in existing_entries:
            existing_entries[discord_id_str] = {}
        existing_entries[discord_id_str][found_on_server_str] = new_key

    # Summary
    log_message(f"Total cases in JSON before update: {json_case_count}")
    log_message(f"Total rows processed in Excel: {excel_case_count}")
    log_message(f"New cases added: {new_cases}")
    log_message(f"Skipped duplicate cases: {skipped_cases}")
    log_message(f"Invalid/skipped rows: {invalid_cases}")
    log_message(f"Total cases after update: {len(data)}")

    # Save updated data
    log_message("Saving updated JSON data...")
    try:
        with open(JSON_FILE_PATH, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii=False)
        log_message("Update completed successfully")
    except Exception as e:
        log_message(f"Error saving JSON file: {str(e)}")


def ascii_username_validator():
    """Validate ASCII usernames (Tool-01)."""
    print_header("ascii username validator")

    def is_ascii(s):
        return all(c in string.printable for c in s)

    # Load the JSON data
    try:
        with open(JSON_FILE_PATH, "r") as file:
            data = json.load(file)
    except Exception as e:
        log_message(f"Error loading JSON file: {str(e)}")
        return

    log_message(f"Found {len(data)} cases in the JSON.")

    # Initialize counters
    updated_true = 0
    updated_false = 0

    # Iterate through the accounts
    for account_number, account_info in data.items():
        username = account_info.get("USERNAME", "")

        # Check if the username is ASCII
        if is_ascii(username):
            account_info["NON_ASCII_USERNAME"] = False
            updated_false += 1
        else:
            account_info["NON_ASCII_USERNAME"] = True
            updated_true += 1
            log_message(
                f"Username for {username} is non-ASCII, NON_ASCII_USERNAME set to True."
            )

    # Print summary
    log_message(f"{updated_true} accounts updated with NON_ASCII_USERNAME set to True.")
    log_message(
        f"{updated_false} accounts updated with NON_ASCII_USERNAME set to False."
    )

    # Save the updated data
    try:
        with open(JSON_FILE_PATH, "w") as file:
            json.dump(data, file, indent=4)
        log_message("Updated JSON file saved successfully.")
    except Exception as e:
        log_message(f"Error saving JSON file: {str(e)}")


def timestamp_verifier():
    """Verify and update timestamps (Tool-18)."""
    print_header("timestamp verifier")

    # Load the JSON file
    try:
        with open(JSON_FILE_PATH, "r", encoding="utf-8") as file:
            data = json.load(file)
    except Exception as e:
        log_message(f"Error loading JSON file: {str(e)}")
        return

    # Initialize counters
    total_accounts = len(data)
    missing_field_count = 0
    empty_field_count = 0

    # Current timestamp
    current_timestamp = datetime.utcnow().isoformat()

    # Iterate over accounts
    for account in data.values():
        if "LAST_CHECK" not in account:
            missing_field_count += 1
            account["LAST_CHECK"] = current_timestamp
        elif not account["LAST_CHECK"]:
            empty_field_count += 1
            account["LAST_CHECK"] = current_timestamp

    # Save the updated JSON file
    try:
        with open(JSON_FILE_PATH, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii=False)
    except Exception as e:
        log_message(f"Error saving JSON file: {str(e)}")
        return

    # Print summary
    log_message(f"Total accounts processed: {total_accounts}")
    log_message(f"Accounts missing 'LAST_CHECK' field: {missing_field_count}")
    log_message(f"Accounts with empty 'LAST_CHECK' field: {empty_field_count}")
    log_message("Timestamps added successfully!")


def url_format_validator():
    """Validate and fix URL formats (Tool-19)."""
    print_header("url format validator")

    def is_valid_url(url):
        special_cases = ["", "No URL Detected", "No URL Sent", "UNKNOWN", "Unknown"]
        if url in special_cases:
            return f"Invalid URL: '{url}' is a special case and won't be modified"

        if not url.startswith(("http://", "https://")):
            return "Invalid URL: Must start with http:// or https://"

        try:
            result = urlparse(url)
            if not all([result.scheme, result.netloc]):
                return (
                    "Invalid URL: Incomplete URL structure (missing scheme or netloc)"
                )
        except Exception as e:
            return f"Error parsing URL: {e}"

        return None

    # Load the JSON data
    try:
        with open(JSON_FILE_PATH, "r") as file:
            data = json.load(file)
    except Exception as e:
        log_message(f"Error loading JSON file: {str(e)}")
        return

    # Initialize counters
    total_cases = len(data)
    total_urls = 0
    invalid_urls = []
    fixed_urls = []
    special_case_counts = {
        "": 0,
        "No URL Detected": 0,
        "No URL Sent": 0,
        "UNKNOWN": 0,
        "Unknown": 0,
    }

    # Iterate over all accounts
    for account_id, account_data in data.items():
        surface_url = account_data.get("SURFACE_URL")
        final_url = account_data.get("FINAL_URL")
        total_urls_for_account = 0

        # Check surface URL
        if surface_url is not None:
            total_urls_for_account += 1
            if surface_url in special_case_counts:
                special_case_counts[surface_url] += 1
                continue

            validation_error = is_valid_url(surface_url)
            if validation_error:
                if "Must start with http:// or https://" in validation_error:
                    fixed_url = (
                        f"https://{surface_url}"
                        if not surface_url.startswith(("http://", "https://"))
                        else surface_url
                    )
                    fixed_urls.append(
                        f"Fixed SURFACE_URL for {account_id}: {surface_url} -> {fixed_url}"
                    )
                    account_data["SURFACE_URL"] = fixed_url
                else:
                    invalid_urls.append(
                        f"Invalid SURFACE_URL for {account_id}: {surface_url} - {validation_error}"
                    )

        # Check final URL
        if final_url is not None:
            total_urls_for_account += 1
            if final_url in special_case_counts:
                special_case_counts[final_url] += 1
                continue

            validation_error = is_valid_url(final_url)
            if validation_error:
                if "Must start with http:// or https://" in validation_error:
                    fixed_url = (
                        f"https://{final_url}"
                        if not final_url.startswith(("http://", "https://"))
                        else final_url
                    )
                    fixed_urls.append(
                        f"Fixed FINAL_URL for {account_id}: {final_url} -> {fixed_url}"
                    )
                    account_data["FINAL_URL"] = fixed_url
                else:
                    invalid_urls.append(
                        f"Invalid FINAL_URL for {account_id}: {final_url} - {validation_error}"
                    )

        total_urls += total_urls_for_account

    # Print results
    if invalid_urls:
        log_message(f"Found issues with {len(invalid_urls)} URLs:")
        for issue in invalid_urls[:5]:  # Show first 5 issues to avoid flooding
            log_message(issue)
        if len(invalid_urls) > 5:
            log_message(f"... and {len(invalid_urls) - 5} more issues")
    else:
        log_message("All URLs are valid!")

    if fixed_urls:
        log_message(f"Fixed issues with {len(fixed_urls)} URLs:")
        for fixed in fixed_urls[:5]:  # Show first 5 fixes
            log_message(fixed)
        if len(fixed_urls) > 5:
            log_message(f"... and {len(fixed_urls) - 5} more fixes")

    total_special_cases = sum(special_case_counts.values())
    if total_special_cases > 0:
        log_message(f"\nSkipped {total_special_cases} special cases:")
        for case_type, count in special_case_counts.items():
            if count > 0:
                case_description = f"'{case_type}'" if case_type else "'empty string'"
                log_message(f"  - {case_description}: {count} instances")

    log_message(
        f"\nProcessed {total_urls} total URLs in {total_cases} cases successfully!"
    )

    # Save the updated data
    try:
        with open(JSON_FILE_PATH, "w") as file:
            json.dump(data, file, indent=4)
    except Exception as e:
        log_message(f"Error saving JSON file: {str(e)}")


def account_creation_date_extractor():
    """Extract account creation dates from Discord IDs (Tool-08)."""
    print_header("account creation date extractor")

    def get_account_creation_date(discord_id):
        try:
            creation_timestamp = ((int(discord_id) >> 22) + 1420070400000) / 1000
            return datetime.utcfromtimestamp(creation_timestamp).strftime("%Y-%m-%d")
        except ValueError:
            log_message(f"Invalid Discord ID format: {discord_id}")
            return None

    # Load the JSON file
    try:
        with open(JSON_FILE_PATH, "r") as file:
            data = json.load(file)
    except Exception as e:
        log_message(f"Error loading JSON file: {str(e)}")
        return

    log_message(f"Found {len(data)} accounts in the JSON file.")

    accounts_updated = 0
    for account_number, account_data in data.items():
        discord_id = account_data.get("DISCORD_ID")
        if not discord_id:
            log_message(f"Skipping account {account_number}: No DISCORD_ID found.")
            continue

        account_creation = account_data.get("ACCOUNT_CREATION")
        if (
            account_creation is None
            or account_creation == ""
            or str(account_creation).strip() == ""
        ):
            creation_date = get_account_creation_date(discord_id)
            if creation_date:
                updated_account_data = account_data.copy()
                keys = list(updated_account_data.keys())

                # Insert ACCOUNT_CREATION after ACCOUNT_TYPE if it exists
                account_type_index = (
                    keys.index("ACCOUNT_TYPE") if "ACCOUNT_TYPE" in keys else -1
                )
                if account_type_index != -1:
                    keys.insert(account_type_index + 1, "ACCOUNT_CREATION")
                else:
                    keys.append("ACCOUNT_CREATION")

                reordered_data = {
                    k: updated_account_data[k]
                    for k in keys
                    if k in updated_account_data
                }
                reordered_data["ACCOUNT_CREATION"] = creation_date

                data[account_number] = reordered_data
                accounts_updated += 1

    # Save updates
    if accounts_updated > 0:
        try:
            with open(JSON_FILE_PATH, "w") as file:
                json.dump(data, file, indent=4)
            log_message(f"Check complete. Updated {accounts_updated} accounts.")
        except Exception as e:
            log_message(f"Error saving JSON file: {str(e)}")
    else:
        log_message("No accounts needed updating.")


# ======================
# Main Menu
# ======================


def display_menu():
    """Display the main menu and get user choice."""
    print("\n" + "=" * 50)
    print("COMPROMISED DISCORD ACCOUNTS DATABASE TOOL".center(50))
    print("=" * 50)
    print("\nMain Menu:")
    print("1. Run All Tools (Full Processing)")
    print("2. Excel to JSON Importer")
    print("3. ASCII Username Validator")
    print("4. JSON Validation Checker")
    print("5. Timestamp Verifier")
    print("6. URL Format Validator")
    print("7. Account Creation Date Extractor")
    print("8. Exit")

    while True:
        choice = input("\nEnter your choice (1-8): ")
        if choice.isdigit() and 1 <= int(choice) <= 8:
            return int(choice)
        print("Invalid input. Please enter a number between 1 and 8.")


def main():
    """Main function to run the combined tool."""
    while True:
        choice = display_menu()

        if choice == 1:  # Run all tools
            print_header("running all tools")
            excel_to_json_importer()
            validate_json(JSON_FILE_PATH)
            ascii_username_validator()
            timestamp_verifier()
            url_format_validator()
            account_creation_date_extractor()
            print_header("all tools completed")
        elif choice == 2:
            excel_to_json_importer()
        elif choice == 3:
            ascii_username_validator()
        elif choice == 4:
            validate_json(JSON_FILE_PATH)
        elif choice == 5:
            timestamp_verifier()
        elif choice == 6:
            url_format_validator()
        elif choice == 7:
            account_creation_date_extractor()
        elif choice == 8:
            print("\nExiting the program. Goodbye!")
            break

        input("\nPress Enter to return to the main menu...")


if __name__ == "__main__":
    main()
