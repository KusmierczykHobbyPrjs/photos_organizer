import os
import argparse
from datetime import datetime


def rename_files_with_mod_date(directory):
    try:
        files = os.listdir(directory)
    except FileNotFoundError:
        print(f"Error: Directory '{directory}' not found.")
        return
    except PermissionError:
        print(f"Error: Permission denied to access '{directory}'.")
        return

    for filename in files:
        try:
            old_file_path = os.path.join(directory, filename)

            # Skip if it's a directory
            if os.path.isdir(old_file_path):
                continue

            # Get the modification time and format it
            mod_time = os.path.getmtime(old_file_path)
            mod_date = datetime.fromtimestamp(mod_time).strftime("%Y-%m-%d")

            # Create the new filename with the date prefix
            new_filename = f"{mod_date} {filename}"
            new_file_path = os.path.join(directory, new_filename)

            # Rename the file
            # os.rename(old_file_path, new_file_path)
            print(f'mv "{old_file_path}" "{new_file_path}"')
        except Exception as e:
            print(f"Error renaming file {filename}: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Add modification date as prefix to filenames in a directory."
    )
    parser.add_argument(
        "directory",
        type=str,
        help="The path to the directory containing files to rename.",
    )
    args = parser.parse_args()

    rename_files_with_mod_date(args.directory)
