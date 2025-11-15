import os
import re
import argparse
from datetime import datetime


def rename_files_in_directory(directory):
    """
    Rename files in the given directory by extracting dates in the filenames, moving the date
    to the beginning, replacing underscores with spaces, and ensuring lowercase '.pdf' extensions.

    Supported date formats in filenames:
    - YYYY-MM-DD
    - YYYY_MM_DD
    - YYYYMMDD

    Args:
        directory (str): The path to the directory containing files to rename.

    Returns:
        None
    """

    # Regular expressions to match different date formats
    date_patterns = [
        re.compile(r"(\d{4}-\d{2}-\d{2})"),  # Match YYYY-MM-DD
        re.compile(r"(\d{4}_\d{2}_\d{2})"),  # Match YYYY_MM_DD
        re.compile(r"(\d{8})"),  # Match YYYYMMDD
    ]

    try:
        files = os.listdir(directory)  # Get the list of files in the directory
    except FileNotFoundError:
        print(f"Error: Directory '{directory}' not found.")
        return
    except PermissionError:
        print(f"Error: Permission denied to access '{directory}'.")
        return

    for filename in files:
        try:
            # Search for a date in the filename
            match = None
            for date_pattern in date_patterns:
                match = date_pattern.search(filename)
                if match:
                    break

            if match:
                date_str = match.group(1)

                # Format date to YYYY-MM-DD if not already
                if re.match(r"\d{8}", date_str):  # Convert YYYYMMDD to YYYY-MM-DD
                    date_str = datetime.strptime(date_str, "%Y%m%d").strftime(
                        "%Y-%m-%d"
                    )
                elif re.match(
                    r"\d{4}_\d{2}_\d{2}", date_str
                ):  # Convert YYYY_MM_DD to YYYY-MM-DD
                    date_str = date_str.replace("_", "-")

                # Create the new filename
                new_filename = (
                    date_str
                    + " "
                    + filename.replace(match.group(1), "")  # Remove matched date
                    .replace("_", " ")  # Replace underscores with spaces
                    .replace("  ", " ")  # Remove double spaces
                    .strip()  # Remove trailing spaces
                )

                new_filename = new_filename.replace(
                    ".PDF", ".pdf"
                )  # Ensure lowercase .pdf extension
                new_filename = new_filename.replace(
                    " .pdf", ".pdf"
                )  # Remove leading spaces before .pdf

                # Construct full file paths
                old_file = os.path.join(directory, filename)
                new_file = os.path.join(directory, new_filename)

                # Perform the renaming
                # os.rename(old_file, new_file)  # Uncomment to actually rename the files
                print(f'mv "{old_file}" "{new_file}"')  # Print for verification
            else:
                print(f"# No date found in: {filename}")
        except Exception as e:
            print(f"Error renaming file {filename}: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Rename files in a directory by moving dates in their names to beginning "
        "and replacing underscores with spaces."
    )
    parser.add_argument(
        "directory",
        type=str,
        help="The path to the directory containing files to rename.",
    )
    args = parser.parse_args()

    rename_files_in_directory(args.directory)
