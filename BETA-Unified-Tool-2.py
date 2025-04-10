import json
import time
from datetime import datetime

# Constants
JSON_FILE_PATH = "../Database-Files/Edit-Database/Compromised-Discord-Accounts.json"


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


# ======================
# Tool Functions
# ======================

def chronological_case_sorter():
    """Sort cases chronologically by FOUND_ON date (Tool-02)."""
    print_header("chronological case sorter")

    # Load existing data from the JSON file
    log_message("Loading JSON data...")
    try:
        with open(JSON_FILE_PATH, "r", encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError:
        log_message("JSON file not found. Exiting.")
        return
    except Exception as e:
        log_message(f"Error loading JSON file: {str(e)}")
        return

    # Convert data into a list of tuples (key, value) and sort by date
    log_message("Sorting cases by date...")
    date_count = 0
    unknown_dates = 0

    def parse_date(account):
        nonlocal date_count, unknown_dates
        date_str = account.get("FOUND_ON", "Unknown")
        if date_str == "Unknown":
            unknown_dates += 1
            return datetime.min  # Assign minimum date for unknown values
        try:
            date_count += 1
            return datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            unknown_dates += 1
            return datetime.min

    sorted_data = dict(sorted(data.items(), key=lambda item: parse_date(item[1])))

    # Print sorting statistics
    log_message(f"Total dates found: {date_count + unknown_dates}")
    log_message(f"Dates sorted: {date_count}")
    log_message(f"Unknown dates: {unknown_dates}")

    # Write the sorted data back to the JSON file
    log_message("Saving sorted JSON data...")
    try:
        with open(JSON_FILE_PATH, "w", encoding="utf-8") as file:
            json.dump(sorted_data, file, indent=4, ensure_ascii=False)
        log_message("Sorting complete.")
    except Exception as e:
        log_message(f"Error saving JSON file: {str(e)}")


def case_number_normalizer():
    """Normalize case numbers and account keys (Tool-03)."""
    print_header("case number normalizer")

    def get_current_timestamp():
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    log_message(f"Starting to fix account numbers in the file: {JSON_FILE_PATH}")

    try:
        with open(JSON_FILE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        log_message("Successfully loaded the data from the file.")
    except Exception as e:
        log_message(f"Error loading the file: {e}")
        return

    total_accounts = len(data)
    updated_count = 0
    updated_data = {}

    # Iterate through the accounts and update both the keys and the CASE_NUMBER
    for index, (old_key, account) in enumerate(data.items(), start=1):
        # Generate the new key (e.g., ACCOUNT_NUMBER_1, ACCOUNT_NUMBER_2, etc.)
        new_key = f"ACCOUNT_NUMBER_{index}"

        # Remove the 'ACCOUNT_NUMBER_' field if it exists
        if "ACCOUNT_NUMBER_" in account:
            del account["ACCOUNT_NUMBER_"]

        # Update the 'CASE_NUMBER' field
        if account["CASE_NUMBER"] != str(index):  # If the CASE_NUMBER is incorrect
            updated_count += 1
        account["CASE_NUMBER"] = str(index)

        # Add the updated account data with the new key to the updated_data dictionary
        updated_data[new_key] = account

    try:
        with open(JSON_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(updated_data, f, indent=4, ensure_ascii=False)
        log_message("Successfully saved the corrected data back to the file.")
    except Exception as e:
        log_message(f"Error saving the file: {e}")
        return

    log_message(f"Found {total_accounts} accounts in the file.")
    log_message(f"{updated_count} accounts were updated.")


# ======================
# Main Menu
# ======================

def display_menu():
    """Display the main menu and get user choice."""
    print("\n" + "=" * 50)
    print("CASE MANAGEMENT TOOL".center(50))
    print("=" * 50)
    print("\nMain Menu:")
    print("1. Run All Tools (Full Processing)")
    print("2. Chronological Case Sorter")
    print("3. Case Number Normalizer")
    print("4. Exit")

    while True:
        choice = input("\nEnter your choice (1-4): ")
        if choice.isdigit() and 1 <= int(choice) <= 4:
            return int(choice)
        print("Invalid input. Please enter a number between 1 and 4.")


def main():
    """Main function to run the combined tool."""
    while True:
        choice = display_menu()

        if choice == 1:  # Run all tools
            print_header("running all tools")
            chronological_case_sorter()
            case_number_normalizer()
            print_header("all tools completed")
        elif choice == 2:
            chronological_case_sorter()
        elif choice == 3:
            case_number_normalizer()
        elif choice == 4:
            print("\nExiting the program. Goodbye!")
            break

        input("\nPress Enter to return to the main menu...")


if __name__ == "__main__":
    main()