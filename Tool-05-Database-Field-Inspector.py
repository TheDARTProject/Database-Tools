import json
import datetime
import os
import re
import requests
import sys
import importlib.util


def load_servers_js(file_path):
    """Load the servers.js file and extract server invites"""
    try:
        # Read the file content
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Extract invite URLs using regex
        pattern = r"https://discord\.com/invite/[a-zA-Z0-9]+"
        invites = re.findall(pattern, content)
        return invites
    except Exception as e:
        print(f"Error loading servers.js: {e}")
        return []


def get_server_member_count(invite_code):
    """Get member count for a Discord server using its invite code"""
    try:
        invite_code = invite_code.split("/")[-1]  # Extract just the code part
        url = f"https://discord.com/api/v9/invites/{invite_code}?with_counts=true"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers)
        data = response.json()

        if "approximate_member_count" in data:
            return data["approximate_member_count"]
        return 0
    except Exception as e:
        print(f"Error fetching member count for {invite_code}: {e}")
        return 0


def process_json(json_file, output_file, date_str, total_protected_members=0):
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    unique_values = {
        "FOUND_ON_SERVER": set(),
        "ACCOUNT_STATUS": set(),
        "ACCOUNT_TYPE": set(),
        "BEHAVIOUR": set(),
        "ATTACK_METHOD": set(),
        "ATTACK_VECTOR": set(),
        "ATTACK_GOAL": set(),
        "ATTACK_SURFACE": set(),
        "SUSPECTED_REGION_OF_ORIGIN": set(),
        "FINAL_URL_STATUS": set(),
        "SURFACE_URL_STATUS": set(),
    }

    for case in data.values():
        for field in unique_values:
            if field in case:
                unique_values[field].add(case[field])

    case_count = len(data)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f'<div align="center">\n\n')
        f.write(f"# Database Inspection - {date_str}\n\n")
        f.write(f"## Total Cases: {case_count}\n\n")
        if total_protected_members > 0:
            f.write(f"## Protected Members: {total_protected_members:,}\n\n")
        f.write(f"</div>\n\n")

        for field, values in unique_values.items():
            f.write(f"## {field.replace('_', ' ').title()}\n")
            for value in sorted(values):
                f.write(f"- {value}\n")
            f.write("\n")

    return case_count


def count_entries_from_file(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        if isinstance(data, dict):
            return len(data)
        elif isinstance(data, list):
            return len(data)
        return 0


def append_other_counts(output_file, counts_dict):
    with open(output_file, "a", encoding="utf-8") as f:
        f.write("## Additional Entries\n")
        for name, count in counts_dict.items():
            f.write(f"- **{name}**: {count} entries\n")


def update_readme(
        readme_path, date_str, inspection_filename, case_count, additional_counts, total_protected_members=0
):
    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()

    additional_lines = "\n".join(
        f"- **{name}**: {count} entries" for name, count in additional_counts.items()
    )

    protected_members_line = f"**Protected Members**: {total_protected_members:,}" if total_protected_members > 0 else ""

    new_section = f"""<!-- INSPECTION-START -->
## Latest Database Inspection - {date_str}

**Inspection File**: [`{inspection_filename}`](Inspection-Database/{inspection_filename})  
- **Total Cases**: {case_count}
- {protected_members_line}
{additional_lines}
<!-- INSPECTION-END -->"""

    pattern = r"<!-- INSPECTION-START -->(.*?)<!-- INSPECTION-END -->"
    if re.search(pattern, content, flags=re.DOTALL):
        content = re.sub(pattern, new_section, content, flags=re.DOTALL)
    else:
        # Insert before final closing </div> to keep formatting
        insert_point = content.rfind("</div>")
        if insert_point == -1:
            content += "\n\n" + new_section
        else:
            content = (
                    content[:insert_point] + new_section + "\n\n" + content[insert_point:]
            )

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(content)


if __name__ == "__main__":
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    inspection_dir = "../Database-Files/Inspection-Database"
    os.makedirs(inspection_dir, exist_ok=True)
    inspection_filename = "Inspection.md"
    inspection_path = os.path.join(inspection_dir, inspection_filename)

    json_file = "../Database-Files/Edit-Database/Compromised-Discord-Accounts.json"
    readme_path = "../Database-Files/README.md"
    servers_js_path = "../thedartproject.github.io/assets/js/servers.js"  # Path to servers.js

    # Get server invites and count members
    total_protected_members = 0
    invite_links = load_servers_js(servers_js_path)

    print(f"Found {len(invite_links)} server invites in servers.js")
    for invite in invite_links:
        members = get_server_member_count(invite)
        print(f"Server invite {invite}: {members} members")
        total_protected_members += members

    print(f"Total protected members: {total_protected_members}")

    # Count primary file
    case_count = process_json(json_file, inspection_path, today, total_protected_members)

    # Count entries from additional files
    additional_counts = {
        "Discord IDs": count_entries_from_file(
            "../Database-Files/Filter-Database/Discord-IDs.json"
        ),
        "Discord Servers": count_entries_from_file(
            "../Database-Files/Filter-Database/Discord-Servers.json"
        ),
        "Global Domains": count_entries_from_file(
            "../Database-Files/Filter-Database/Global-Domains.json"
        ),
    }

    append_other_counts(inspection_path, additional_counts)
    update_readme(
        readme_path,
        today,
        inspection_filename,
        case_count,
        additional_counts,
        total_protected_members
    )