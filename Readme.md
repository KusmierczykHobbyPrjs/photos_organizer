
Scripts for organizing files (e.g., photos) by their date. For example, they can be used when creating a disk copy of photos from a phone.

Scripts:
 - [rename_by_date.py](rename_by_date.py) — renames files so that their names begin with the date (YYYY-MM-DD)
 - [organize_by_date.py](organize_by_date.py) — groups files into directories based on their dates
 - [detect_duplicates.py](detect_duplicates.py) — detects duplicate files


# Usage

The Python scripts do not perform the modifications directly. Instead, they print out shell commands to be executed. You can redirect the output of a script and then run the resulting commands.

# Details of the scripts 

--------------------------------------------------
## [rename_by_date.py](rename_by_date.py): File Renaming Based on Date

This Python script generates bash commands for renaming files (e.g., JPEG images) based on their date. It scans the provided files, extracts the date from their name or metadata, and constructs new filenames in the format `date+suffix`. The script resolves naming conflicts (e.g., duplicate filenames) and outputs the corresponding shell commands (such as `mv` or another user-specified command).

### Usage

To run the script, use the following command:

```python rename_by_date.py -f /path/to/files/*.jpg```

--------------------------------------------------
## [organize_by_date.py](organize_by_date.py): File Grouping by Date

This Python script groups files (such as images) into directories based on their date metadata. It outputs bash commands to move the files into their respective directories, with options for adding directory prefixes or suffixes, resolving naming conflicts, and merging small directories into a common folder.

### Features

- **File Grouping by Date**: Groups files into directories based on their extracted date metadata.
- **Directory Creation**: Automatically creates directories for the grouped files.
- **Customizable Directory Names**: Optionally add prefixes and/or suffixes to the directory names.
- **Merge Small Directories**: Merge directories with fewer than a specified number of files into a common folder.
- **Conflict Resolution**: Automatically resolves filename conflicts by appending numerical suffixes to avoid overwriting.
- **Bash Command Output**: Outputs bash commands (`mv`, `mkdir`, etc.) for review and manual execution.

### Usage

You can run the script using the following command:

```python organize_by_date.py -f "/path/to/files/*.jpg"```
or
```python organize_by_date.py -f "/path/to/files/*.jpg" -d "/path/to/target" -p "prefix_" -s "_suffix" -n 5```

--------------------------------------------------
## [detect_duplicates.py](detect_duplicates.py): Detecting Duplicates

This Python script is designed to detect duplicate files between two sets of files by comparing their contents. It outputs bash commands (such as `rm -rf` by default) for handling the detected duplicates. The script efficiently compares files based on their size and byte content to ensure accuracy, even when filenames are different.

### Features

- **Wildcard Support**: Use file patterns (e.g., `*.jpg`, `*.txt`) to specify files.
- **File Comparison**: Compares files by size and specific byte ranges (start, middle, end) to detect duplicates.
- **Command Output**: Outputs bash commands to handle duplicates (default is `rm -rf`).
- **Flexible Input**: Can compare files from two separate directories or within the same directory.

### Usage

Run the script using the following command:

```python detect_duplicates.py -f "left_dir/*.jpg" -r "right_dir/*.jpg" ```
