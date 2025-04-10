import json
import datetime
import os
import re


def process_json(json_file, output_file, date_str):
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
    readme_path, date_str, inspection_filename, case_count, additional_counts
):
    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()

    additional_lines = "\n".join(
        f"- **{name}**: {count} entries" for name, count in additional_counts.items()
    )

    new_section = f"""<!-- INSPECTION-START -->
## Latest Database Inspection - {date_str}

**Inspection File**: [`{inspection_filename}`](Inspection-Database/{inspection_filename})  
**Total Cases**: {case_count}

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

    # Count primary file
    case_count = process_json(json_file, inspection_path, today)

    # Count entries from additional files
    additional_counts = {
        "Discord IDs": count_entries_from_file(
            "../Database-Files/Filter-Database/Discord-IDs.json"
        ),
        "Malicious URLs": count_entries_from_file(
            "../Database-Files/Filter-Database/Malicious-URLs.json"
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
        readme_path, today, inspection_filename, case_count, additional_counts
    )
