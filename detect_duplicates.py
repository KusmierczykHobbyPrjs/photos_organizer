import argparse
from glob import glob
from typing import Dict, List
import os


def parse_args():
    """
    Parses command-line arguments.

    Returns:
        args: Parsed command-line arguments, including:
            - left_files (list): List of files or patterns to match on the left side.
            - right_files (list): List of files or patterns to match on the right side.
            - cmd (str): Command to apply to duplicates (default is 'rm -rf').
    """
    parser = argparse.ArgumentParser(
        description="Detect and handle duplicate files between two sets of files. "
        "Outputs commands to handle detected duplicates."
    )

    parser.add_argument(
        "-f",
        "--files",
        type=str,
        nargs="+",
        required=True,
        help="List of file paths or patterns to compare (wildcards supported).",
    )
    parser.add_argument(
        "-r",
        "--right_files",
        type=str,
        nargs="+",
        required=False,
        default=None,
        help="Optional list of files or patterns to compare against the left files.",
    )
    parser.add_argument(
        "-c",
        "--cmd",
        type=str,
        required=False,
        default="rm -rf",
        help="Command to apply to duplicate files (default is 'rm -rf').",
    )

    args = parser.parse_args()
    args.left_files = args.files
    return args


_stats_cache = {}


def get_size(file1: str) -> int:
    """
    Retrieves the size of a file, using a cache to avoid redundant stat calls.

    Args:
        file1 (str): Path to the file.

    Returns:
        int: File size in bytes.
    """
    if file1 not in _stats_cache:
        _stats_cache[file1] = os.stat(file1)
    return _stats_cache[file1].st_size


def are_equal(
    file1: str, file2: str, start_bytes=1024, end_bytes=1024, mid_bytes=1024
) -> bool:
    """
    Compares two files to check if they are equal by comparing their start, middle, and end bytes.

    Args:
        file1 (str): Path to the first file.
        file2 (str): Path to the second file.
        start_bytes (int): Number of bytes to compare from the start.
        end_bytes (int): Number of bytes to compare from the end.
        mid_bytes (int): Number of bytes to compare from the middle.

    Returns:
        bool: True if the files are considered equal, False otherwise.
    """
    if os.path.isdir(file1) or os.path.isdir(file2):
        return False

    size1 = get_size(file1)
    size2 = get_size(file2)

    if size1 != size2:
        return False

    # Compare start bytes
    nb = min(start_bytes, size1)
    with open(file1, "rb") as f1, open(file2, "rb") as f2:
        if f1.read(nb) != f2.read(nb):
            return False

    # Compare middle bytes
    mid_start = size1 // 2
    nb = min(mid_bytes, size1 - mid_start)
    with open(file1, "rb") as f1, open(file2, "rb") as f2:
        f1.seek(mid_start)
        f2.seek(mid_start)
        if f1.read(nb) != f2.read(nb):
            return False

    # Compare end bytes
    nb = min(end_bytes, size1)
    with open(file1, "rb") as f1, open(file2, "rb") as f2:
        f1.seek(-nb, os.SEEK_END)
        f2.seek(-nb, os.SEEK_END)
        if f1.read(nb) != f2.read(nb):
            return False

    return True


def handle_duplicates(file_pairs: List[str], cmd: str):
    """
    Handles duplicate files by executing the specified command.

    Args:
        file_pairs (List[str]): List of duplicate file pairs.
        cmd (str): The command to execute on the duplicate files (e.g., 'rm -rf').
    """
    for file1, file2 in file_pairs:
        print(f"# Duplicate detected: '{file1}' and '{file2}'")
        # Remove the larger file or use the specified command
        if len(file1) < len(file2):
            print(f"{cmd} '{file2}'")
        else:
            print(f"{cmd} '{file1}'")


if __name__ == "__main__":

    args = parse_args()

    # Gather left files using glob for wildcards
    left_files = [file for pattern in args.left_files for file in glob(pattern)]
    print(f"# Considering {len(left_files)} (left) files")

    # Gather right files or reuse left files if not specified
    right_files = []
    if args.right_files:
        right_files = [file for pattern in args.right_files for file in glob(pattern)]
        print(f"# Considering {len(right_files)} (right) files")
    else:
        right_files = left_files.copy()

    # Detect duplicates
    duplicates = []
    considered = set()
    for i, file1 in enumerate(left_files):
        if i % (len(left_files) // 100 + 1) == 0:
            print(f"# Progress: {i}/{len(left_files)}")

        for file2 in right_files:
            if file1 == file2 or (file1, file2) in considered:
                continue

            if are_equal(file1, file2):
                duplicates.append((file1, file2))

            considered.add((file1, file2))
            considered.add((file2, file1))

    # Handle duplicates
    if duplicates:
        handle_duplicates(duplicates, args.cmd)
    else:
        print("# No duplicates found")
