import json
import re
from urllib.parse import urlparse


# Function to validate URLs
def is_valid_url(url):
    # Special cases we don't want to modify
    special_cases = ["", "No URL Detected", "No URL Sent", "UNKNOWN", "Unknown"]
    if url in special_cases:
        return f"Invalid URL: '{url}' is a special case and won't be modified"

    # Check if URL starts with http:// or https://
    if not url.startswith(("http://", "https://")):
        return "Invalid URL: Must start with http:// or https://"

    # Parse the URL to ensure it's a valid structure
    try:
        result = urlparse(url)
        if not all([result.scheme, result.netloc]):
            return "Invalid URL: Incomplete URL structure (missing scheme or netloc)"
    except Exception as e:
        return f"Error parsing URL: {e}"

    return None  # None means the URL is valid


# Load the JSON data
with open("../Database-Files/Edit-Database/Compromised-Discord-Accounts.json", "r") as file:
    data = json.load(file)

# Initialize counters and lists for statistics
total_cases = len(data)
total_urls = 0
invalid_urls = []
fixed_urls = []

# Dictionary to track special cases by type
special_case_counts = {
    "": 0,
    "No URL Detected": 0,
    "No URL Sent": 0,
    "UNKNOWN": 0,
    "Unknown": 0
}

# Iterate over all accounts and check URLs
for account_id, account_data in data.items():
    surface_url = account_data.get("SURFACE_URL")
    final_url = account_data.get("FINAL_URL")

    # Count the total URLs found
    total_urls_for_account = 0

    # Check the surface URL
    if surface_url is not None:
        total_urls_for_account += 1

        # Special cases we don't want to modify
        special_cases = ["", "No URL Detected", "No URL Sent", "UNKNOWN", "Unknown"]
        if surface_url in special_cases:
            # Increment the counter for this special case
            special_case_counts[surface_url] += 1
            continue

        validation_error = is_valid_url(surface_url)

        # If the URL is invalid
        if validation_error:
            if "Must start with http:// or https://" in validation_error:
                # Fix the URL by adding https://
                fixed_url = (
                    f"https://{surface_url}"
                    if not surface_url.startswith(("http://", "https://"))
                    else surface_url
                )
                fixed_urls.append(
                    f"Fixed SURFACE_URL for {account_id}: {surface_url} -> {fixed_url}"
                )
                account_data["SURFACE_URL"] = fixed_url  # Update the SURFACE_URL field
            else:
                invalid_urls.append(
                    f"Invalid SURFACE_URL for {account_id}: {surface_url} - {validation_error}"
                )

    # Check the final URL
    if final_url is not None:
        total_urls_for_account += 1

        # Special cases we don't want to modify
        special_cases = ["", "No URL Detected", "No URL Sent", "UNKNOWN", "Unknown"]
        if final_url in special_cases:
            # Increment the counter for this special case
            special_case_counts[final_url] += 1
            continue

        validation_error = is_valid_url(final_url)

        # If the URL is invalid
        if validation_error:
            if "Must start with http:// or https://" in validation_error:
                # Fix the URL by adding https://
                fixed_url = (
                    f"https://{final_url}"
                    if not final_url.startswith(("http://", "https://"))
                    else final_url
                )
                fixed_urls.append(
                    f"Fixed FINAL_URL for {account_id}: {final_url} -> {fixed_url}"
                )
                account_data["FINAL_URL"] = fixed_url  # Update the FINAL_URL field
            else:
                invalid_urls.append(
                    f"Invalid FINAL_URL for {account_id}: {final_url} - {validation_error}"
                )

    total_urls += total_urls_for_account

# Print summary of invalid URLs
if invalid_urls:
    print(f"Found issues with {len(invalid_urls)} URLs:")
    for issue in invalid_urls:
        print(issue)
else:
    print("All URLs are valid!")

# Print summary of fixed URLs
if fixed_urls:
    print(f"Fixed issues with {len(fixed_urls)} URLs:")
    for fixed in fixed_urls:
        print(fixed)

# Print summary of special cases
total_special_cases = sum(special_case_counts.values())
if total_special_cases > 0:
    print(f"\nSkipped {total_special_cases} special cases:")
    for case_type, count in special_case_counts.items():
        if count > 0:
            case_description = f"'{case_type}'" if case_type else "'empty string'"
            print(f"  - {case_description}: {count} instances")

# Print total processed URLs and cases
print(f"\nProcessed {total_urls} total URLs in {total_cases} cases successfully!")

# Save the updated data back to the same JSON file
with open("../Database-Files/Edit-Database/Compromised-Discord-Accounts.json", "w") as file:
    json.dump(data, file, indent=4)