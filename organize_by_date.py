import argparse
import os
import file_date
from glob import glob
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

from path_matcher import match_paths


def parse_args() -> argparse.Namespace:
    """
    Parses the command-line arguments required for the script.

    Returns:
        argparse.Namespace: Parsed arguments including:
            - files: List of file paths or patterns to process.
            - target_directory: Destination directory for the grouped files.
            - suffix: Optional suffix for directory names.
            - prefix: Optional prefix for directory names.
            - min_n_files: Minimum number of files required to create a directory.
            - cmd: Command to execute for moving files (default is 'mv').
    """
    parser = argparse.ArgumentParser(
        description="Groups and moves files (e.g., JPEGs) into directories based on their date. "
        "Outputs bash commands for the file movement."
    )

    parser.add_argument(
        "-f",
        "--files",
        type=str,
        nargs="*",
        required=False,
        default=[],
        help="List of file paths or patterns to process (wildcards supported).",
    )
    # Support drag-and-drop file input
    parser.add_argument(
        'dropped_files', 
        nargs='*',      # Accepts zero or more files
        default=[],     # Default to empty list
        help='List of files (drag and drop)'
    )

    parser.add_argument(
        "-d",
        "--target_directory",
        type=str,
        default="",
        required=False,
        help="Destination directory path (default is current directory).",
    )
    parser.add_argument(
        "-s",
        "--suffix",
        type=str,
        default="",
        required=False,
        help="Optional suffix to add to the directory names.",
    )
    parser.add_argument(
        "-p",
        "--prefix",
        type=str,
        default="",
        required=False,
        help="Optional prefix to add to the directory names.",
    )
    parser.add_argument(
        "-n",
        "--min_n_files",
        type=int,
        default=3,
        required=False,
        help="Minimum number of files required to create a directory (default: 3).",
    )
    parser.add_argument(
        "-m",
        "--merge",
        action="store_false",
        required=False,
        help="Merge consecutive days (default: true)",
    )
    parser.add_argument(
        "-c",
        "--cmd",
        type=str,
        default="mv",
        required=False,
        help="Command to execute for moving files (default: 'mv').",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        required=False,
        help="Print more details",
    )

    args = parser.parse_args()

    args.target_directory = args.target_directory.rstrip(os.path.sep)
    args.files = list(set(args.files + args.dropped_files))

    return args


def move_files(
    file2meta: Dict[str, Dict[str, str]], args: argparse.Namespace
) -> Dict[str, List[str]]:
    """
    Groups files into directories based on their date metadata.

    Args:
        file2meta (dict): Dictionary where keys are file paths and values are metadata dicts with date information.
        args (argparse.Namespace): Parsed command-line arguments.

    Returns:
        dict: A dictionary where keys are destination directory paths, and values are lists of files to move there.
    """
    dst2files = {}
    for file, meta in file2meta.items():
        date_dir = meta["date"]
        dst = date_dir
        dst2files.setdefault(dst, []).append(file)
    return dst2files


def merge_small_directories(
    dst2files: Dict[str, List[str]], args: argparse.Namespace
) -> Dict[str, List[str]]:
    """
    Merges small directories into a common destination if they have fewer than the minimum required files.

    Args:
        dst2files (dict): Dictionary of directories and their associated files.
        args (argparse.Namespace): Parsed command-line arguments.

    Returns:
        dict: Updated dictionary of directories and files after merging small directories.
    """
    merged_dst2files = {}
    default_dst_files = []

    for dst, files in dst2files.items():
        if len(files) < args.min_n_files:
            print(
                f"# Too few files (={len(files)}) in {dst}. Moving files to the common directory."
            )
            default_dst_files.extend(files)
        else:
            merged_dst2files[dst] = files

    # Add small files to the root directory
    if default_dst_files:
        merged_dst2files[args.target_directory] = default_dst_files

    return merged_dst2files


def resolve_conflicts(files: List[str]) -> Dict[str, str]:
    """
    Resolves naming conflicts between files by appending numerical suffixes if needed.

    Args:
        files (list): List of file paths to check for conflicts.

    Returns:
        dict: Mapping from original file paths to new (potentially renamed) file names.
    """
    files = sorted(files, key=lambda path: os.path.basename(path))
    src2dst = {}
    prev_filename, prev_path = None, None
    conflict_counter = 0

    for path in files:
        filename = os.path.basename(path)

        if prev_filename and filename == prev_filename:
            conflict_counter += 1
            parts = filename.rsplit(".", 1)  # Split into name and extension

            if len(parts) == 1:  # No extension case
                filename = f"{parts[0]}-{conflict_counter}"
            else:
                filename = f"{parts[0]}-{conflict_counter}.{parts[1]}"

            print(
                f"# Conflict between '{prev_path}' and '{path}' resolved as '{filename}'."
            )

        else:
            prev_filename, prev_path = filename, path
            conflict_counter = 0

        src2dst[path] = filename

    return src2dst


def extract_common_prefix(file_names: List[str]) -> str:
    """
    Extracts the common directory prefix from a list of file paths.

    This function finds the longest common directory path that is shared by all
    file paths in the input list. It respects directory boundaries and works with
    both absolute and relative paths, as well as mixed path separators.

    Args:
        file_names: List of file paths (strings)

    Returns:
        Common directory prefix as a string. Returns empty string if:
        - Input list is empty
        - No common prefix exists
        - Common prefix is not a complete directory

    Examples:
        >>> extract_common_prefix([
        ...     "/home/user/documents/report.pdf",
        ...     "/home/user/documents/data.csv",
        ...     "/home/user/documents/images/photo.jpg"
        ... ])
        '/home/user/documents'

        >>> extract_common_prefix([
        ...     "project/src/main.py",
        ...     "project/src/utils.py",
        ...     "project/tests/test_main.py"
        ... ])
        'project'

        >>> extract_common_prefix([
        ...     "/var/log/app.log",
        ...     "/home/user/data.txt"
        ... ])
        ''
    """
    if not file_names:
        return ""

    if len(file_names) == 1:
        # Single file: return its directory
        return str(Path(file_names[0]).parent)

    # Normalize all paths to use consistent separators
    normalized_paths = [Path(f) for f in file_names]

    # Convert to parts for comparison
    path_parts = [list(p.parts) for p in normalized_paths]

    # Find common prefix by comparing parts
    common_parts = []

    # Get minimum length to avoid index errors
    min_length = min(len(parts) for parts in path_parts)

    for i in range(min_length):
        # Check if all paths have the same part at position i
        first_part = path_parts[0][i]

        if all(parts[i] == first_part for parts in path_parts):
            common_parts.append(first_part)
        else:
            break

    # Don't include the filename itself in the prefix
    # Check if the common parts include a filename by verifying
    # if any path has exactly len(common_parts) parts
    if common_parts and any(len(parts) == len(common_parts) for parts in path_parts):
        # The last common part is a filename, not a directory
        common_parts = common_parts[:-1]

    # Construct the result path
    if not common_parts:
        return ""

    # Handle absolute vs relative paths
    if normalized_paths[0].is_absolute():
        # For absolute paths, join parts with root
        result = Path(*common_parts)
    else:
        # For relative paths
        result = Path(*common_parts)

    return str(result)


def merge_consecutive_date_clusters(
    date_files: Dict[str, List[str]],
) -> Dict[str, List[str]]:
    """
    Merges file lists from consecutive days into clusters.

    Takes a mapping of date strings (YYYY-MM-DD) to file lists and groups files
    from consecutive days together. Each cluster gets a new key in the format:
    - "YYYY-MM-DD - YYYY-MM-DD" for multi-day clusters
    - "YYYY-MM-DD" for single-day clusters

    Args:
        date_files: Dictionary mapping date strings to lists of files

    Returns:
        Dictionary with merged consecutive date ranges and combined file lists

    Examples:
        >>> data = {
        ...     "2024-01-01": ["file1.txt", "file2.txt"],
        ...     "2024-01-02": ["file3.txt"],
        ...     "2024-01-03": ["file4.txt"],
        ...     "2024-01-05": ["file5.txt"],
        ...     "2024-01-06": ["file6.txt"]
        ... }
        >>> merge_consecutive_date_clusters(data)
        {
            "2024-01-01 - 2024-01-03": ["file1.txt", "file2.txt", "file3.txt", "file4.txt"],
            "2024-01-05 - 2024-01-06": ["file5.txt", "file6.txt"]
        }
    """
    if not date_files:
        return {}

    # Parse and sort dates
    date_list = []
    for date_str in date_files.keys():
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            date_list.append((date_obj, date_str))
        except ValueError:
            # Skip invalid date formats
            continue

    if not date_list:
        return {}

    # Sort by date
    date_list.sort(key=lambda x: x[0])

    # Find consecutive date clusters
    clusters = []
    current_cluster = [date_list[0]]

    for i in range(1, len(date_list)):
        prev_date, _ = date_list[i - 1]
        curr_date, _ = date_list[i]

        # Check if current date is exactly one day after previous
        if curr_date - prev_date == timedelta(days=1):
            current_cluster.append(date_list[i])
        else:
            # Gap found, save current cluster and start new one
            clusters.append(current_cluster)
            current_cluster = [date_list[i]]

    # Don't forget the last cluster
    clusters.append(current_cluster)

    # Build result dictionary
    result = {}

    for cluster in clusters:
        # Get all files from this cluster
        all_files = []
        for date_obj, date_str in cluster:
            all_files.extend(date_files[date_str])

        # Create key based on cluster size
        if len(cluster) == 1:
            # Single day - use original format
            _, date_str = cluster[0]
            key = date_str
        else:
            # Multiple days - use range format
            _, start_date = cluster[0]
            _, end_date = cluster[-1]
            key = f"{start_date} - {end_date}"

        result[key] = all_files

    return result


if __name__ == "__main__":
    args = parse_args()

    # Find files using glob (wildcards supported)
    file_names = match_paths(args.files, recursive=True, verbose=False)

    if not file_names:
        print("No files found matching the provided patterns.")
        exit(1)

    if args.target_directory == "":
        try:
            args.target_directory = extract_common_prefix(file_names)
        except Exception as e:
            print(f"# ERROR: Failed to retrieve the target directory: {e}")
            args.target_directory = "."

    print("# Grouping files into directories by date:")
    file2meta = file_date.extract_meta(
        file_names
    )  # Extract metadata, including date, for each file
    dst2files = move_files(file2meta, args)  # Group files by date

    try:
        dst2files = merge_small_directories(
            dst2files, args
        )  # Merge directories with fewer than min_n_files
    except Exception as e:
        print(f"# ERROR: Failed to merge directories with fewer than min_n_files: {e}")

    try:
        dst2files = merge_consecutive_date_clusters(dst2files)
    except Exception as e:
        print(f"# ERROR: Failed to merge consecutive days: {e}")

    dst2files = {
        dst: sorted(files) for dst, files in dst2files.items()
    }  # Sort files in each directory

    # Generate bash commands for creating directories and moving files
    for dir_path, files in sorted(dst2files.items()):

        dir_path = os.path.join(
            args.target_directory, f"{args.prefix}{dir_path}{args.suffix}"
        )

        print(f"mkdir -p '{dir_path}'")  # Create directory command

        # Resolve conflicts in file names before moving
        files2dst_file_name = resolve_conflicts(files)

        for src, dst_file_name in files2dst_file_name.items():
            target_path = os.path.join(dir_path, dst_file_name)
            if src == target_path:
                if args.verbose:
                    print(f"#{src} is already in the right directory!")
            else:
                print(f"{args.cmd} '{src}' '{target_path}'")  # Move file command

    print("#############################")
