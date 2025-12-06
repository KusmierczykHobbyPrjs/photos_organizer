import os
from datetime import datetime
from tabnanny import verbose
from typing import List, Dict, Optional, Tuple
import file_date
import argparse
from glob import glob
from pathlib import Path
import re

from path_matcher import match_paths


def parse_args() -> argparse.Namespace:
    """
    Parses the command-line arguments required for the script.

    Returns:
        argparse.Namespace: Parsed arguments including:
            - files: List of directories to process.
    """
    parser = argparse.ArgumentParser(
        description="Rename directories by date ranges of contained files."
    )

    parser.add_argument(
        "-f",
        "--files",
        type=str,
        nargs="*",
        required=False,
        default=[],
        help="List of directory paths or patterns to process (wildcards supported).",
    )
    # Support drag-and-drop file input
    parser.add_argument(
        "dropped_files",
        nargs="*",  # Accepts zero or more files
        default=[],  # Default to empty list
        help="List of files (drag and drop)",
    )
    parser.add_argument(
        "-x",
        "--remove_date",
        action="store_true",
        default=False,
        required=False,
        help="Remove date from the original dir name. "
        "By default dates are used as a prefixes.",
    )
    parser.add_argument(
        "-s",
        "--span_days",
        type=int,
        default=5,
        required=False,
        help="Directories spanning over some number of days (default: 5), "
        "are prefixed with range: start_date - end_date. Otherwise just start_date is used.",
    )
    parser.add_argument(
        "-nr",
        "--non_recursive",
        action="store_true",
        default=False,
        required=False,
        help="Do not search subdirectories recursively",
    )
    parser.add_argument(
        "-a",
        "--all_types",
        action="store_true",
        default=False,
        required=False,
        help="Extract dates based on all file types (*.*). "
        "By default it's only media types (*.jpg, *.png, etc.)",
    )
    parser.add_argument(
        "-q",
        "--quantiles",
        type=float,
        nargs="+",
        default=[0.05, 0.5, 0.95],
        help="List of date quantiles (ranges) for each directory to consider (between 0 and 1). Default: [0.05, 0.5, 0.95]",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        required=False,
        help="Print more details",
    )

    args = parser.parse_args()

    assert len(args.quantiles) == 3, "3 quantiles required: low, medium, high"
    args.files = list(set(args.files + args.dropped_files))

    return args


def check_date_pattern(text: str) -> Tuple[Optional[str], str]:
    """
    Check if a string starts with date pattern(s) and extract them.

    Patterns checked (in order):
    1. "YYYY-MM-DD - YYYY-MM-DD" (date range)
    2. "YYYY-MM-DD" (single date)

    Args:
        text: The string to check

    Returns:
        Tuple of (matched_part, remaining_part)
        - If no match: (None, original_string)
        - If match: (matched_date_string, remaining_string)

    Examples:
        >>> check_date_pattern("2024-01-15 - 2024-01-20 Meeting notes")
        ('2024-01-15 - 2024-01-20', ' Meeting notes')

        >>> check_date_pattern("2024-01-15 Task description")
        ('2024-01-15', ' Task description')

        >>> check_date_pattern("No date here")
        (None, 'No date here')
    """
    # Pattern for date range: YYYY-MM-DD - YYYY-MM-DD
    date_range_pattern = r"^(\d{4}-\d{2}-\d{2}\s*-\s*\d{4}-\d{2}-\d{2})"

    # Pattern for single date: YYYY-MM-DD
    single_date_pattern = r"^(\d{4}-\d{2}-\d{2})"

    # Try date range pattern first
    match = re.match(date_range_pattern, text)
    if match:
        matched_part = match.group(1)
        remaining_part = text[len(matched_part) :]
        return (matched_part, remaining_part)

    # Try single date pattern
    match = re.match(single_date_pattern, text)
    if match:
        matched_part = match.group(1)
        remaining_part = text[len(matched_part) :]
        return (matched_part, remaining_part)

    # No match found
    return (None, text)


def list_files(
    directory: str, patterns: List[str] = ["*.*"], recursive: bool = True
) -> List[str]:
    """
    List all files in a directory matching specified patterns.

    Args:
        directory: Path to the directory to search
        patterns: List of glob patterns to match (e.g., ["*.jpg", "*.png"])
        recursive: If True, search subdirectories recursively

    Returns:
        List of file paths matching the patterns

    Example:
        >>> list_files("/path/to/dir", ["*.jpg", "*.png"], recursive=True)
        ['/path/to/dir/image1.jpg', '/path/to/dir/subfolder/photo.PNG']
    """
    path = Path(directory)

    if not path.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")

    if not path.is_dir():
        raise NotADirectoryError(f"Not a directory: {directory}")

    matched_files = []

    for pattern in patterns:
        # Convert pattern to lowercase for case-insensitive matching
        pattern_lower = pattern.lower()

        # Use rglob for recursive, glob for non-recursive
        glob_method = path.rglob if recursive else path.glob

        # Find all files matching the pattern
        for file_path in glob_method(pattern):
            if file_path.is_file():
                # Check if filename matches pattern case-insensitively
                if any(file_path.match(p) for p in patterns):
                    # Convert to case-insensitive matching
                    pattern_parts = pattern_lower.split(".")
                    file_parts = file_path.name.lower().split(".")

                    # Simple case-insensitive check
                    if len(pattern_parts) >= 2 and len(file_parts) >= 2:
                        if (
                            pattern_parts[-1] == "*"
                            or file_parts[-1] == pattern_parts[-1]
                        ):
                            matched_files.append(str(file_path))
                    elif pattern == "*.*" or pattern_lower == "*.*":
                        matched_files.append(str(file_path))

    # Remove duplicates while preserving order
    return list(dict.fromkeys(matched_files))


MEDIA_FILES = [
    "*.jpg",
    "*.jpeg",
    "*.webp",
    "*.png",
    "*.gif",
    "*.tiff",
    "*.mp4",
    "*.mov",
    "*.avi",
    "*.mkv",
    "*.webm",
    "*.mpeg",
]


def compute_directory_date_quantiles(
    directory_path: str,
    date_quantiles: List[float],
    file_patterns: List[str] = MEDIA_FILES,
    file_search_recursive: bool = True,
) -> Dict[float, str]:
    """
    Searches a directory for files, extracts dates from filenames, and computes date quantiles.

    Args:
        directory_path: Path to the directory to search
        date_quantiles: List of quantile values (e.g., [0.25, 0.5, 0.75] for quartiles)

    Returns:
        Dictionary mapping quantile values to date strings in YYYY-MM-DD format

    Example:
        >>> compute_file_date_quantiles('/path/to/files', [0.25, 0.5, 0.75])
        {0.25: '2023-03-15', 0.5: '2023-06-20', 0.75: '2023-09-10'}
    """
    dates = []

    # Iterate through all files in the directory
    for filename in list_files(
        directory_path, patterns=file_patterns, recursive=file_search_recursive
    ):
        filepath = os.path.join(directory_path, filename)

        # Only process files, not subdirectories
        if os.path.isfile(filepath):
            try:
                # Extract date from filename
                date_str, suffix = file_date.extract_date_for_path(
                    filepath, verbose=True
                )

                # Convert date string to datetime object for sorting
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                dates.append(date_obj)
            except Exception as e:
                # Skip files that don't have valid dates
                print(f"Warning: Could not extract date from {filename}: {e}")
                continue

    if not dates:
        raise ValueError(f"No valid dates found in directory: {directory_path}")

    # Sort dates
    dates.sort()

    # Compute quantiles
    result = {}
    n = len(dates)

    for q in date_quantiles:
        if not 0 <= q <= 1:
            raise ValueError(f"Quantile must be between 0 and 1, got {q}")

        # Calculate position in sorted list
        pos = q * (n - 1)
        lower_idx = int(pos)
        upper_idx = min(lower_idx + 1, n - 1)

        # Linear interpolation between two nearest dates
        if lower_idx == upper_idx:
            quantile_date = dates[lower_idx]
        else:
            # Interpolate between dates
            weight = pos - lower_idx
            lower_date = dates[lower_idx]
            upper_date = dates[upper_idx]

            # Convert to timestamps for interpolation
            lower_ts = lower_date.timestamp()
            upper_ts = upper_date.timestamp()
            interpolated_ts = lower_ts + weight * (upper_ts - lower_ts)

            quantile_date = datetime.fromtimestamp(interpolated_ts)

        # Convert back to YYYY-MM-DD string format
        result[q] = quantile_date.strftime("%Y-%m-%d")

    return result


def extract_date_for_directory(
    directory_path: str,
    verbose: bool = False,
    quantiles: List[float] = [0.05, 0.5, 0.95],
    min_number_of_days: int = 5,
    min_name_date_length: int = 7,
    file_search_recursive: bool = True,
    file_patterns: List[str] = MEDIA_FILES,
) -> str:
    """
    Extracts the date for a directory based on its name.

    Args:
        directory_path: Path to the directory
        verbose: Whether to print verbose output
        quantiles: List of quantile values (e.g., [0.25, 0.5, 0.75] for quartiles)
    """
    directory_base = os.path.basename(directory_path)

    date_str, dir_name = check_date_pattern(directory_base)
    if date_str is None:
        date_str, dir_name = file_date.extract_date_for_path(
            directory_base, verbose=verbose, modification_time_fallback=False
        )
    dir_name = dir_name.strip(" -_")

    if date_str is not None and len(date_str) >= min_name_date_length:
        if verbose:
            print(f"#Directory: {directory_base}. Extracted date from name: {date_str}")
        return date_str, dir_name

    quantiles = compute_directory_date_quantiles(
        directory_path,
        quantiles,
        file_search_recursive=file_search_recursive,
        file_patterns=file_patterns,
    )
    q_str = ", ".join([f" {q}: {date_str}" for q, date_str in quantiles.items()])
    if verbose:
        print(f"#Directory: {directory_path}. Date quantiles: {q_str}")
    quantiles = sorted(quantiles.values())

    if quantiles[0] == quantiles[2]:
        return quantiles[1], dir_name  # All quantiles are the same, use the median

    # Short range
    number_of_days = (
        datetime.strptime(quantiles[2], "%Y-%m-%d")
        - datetime.strptime(quantiles[0], "%Y-%m-%d")
    ).days
    if number_of_days < min_number_of_days:
        return quantiles[0], dir_name

    return f"{quantiles[0]} - {quantiles[2]}", dir_name


if __name__ == "__main__":
    args = parse_args()
    if args.verbose:
        print(f"# Script args = {args}")

    paths = match_paths(args.files, recursive=False, verbose=False)

    # Keep only directories
    paths = [p for p in paths if os.path.isdir(p)]

    if not paths:
        print("# No directories found matching the provided patterns.")
        exit(1)

    for dir_path in paths:
        if args.verbose:
            print(f"\n\n# Processing directory: {dir_path}")
        try:
            parent_dir = os.path.dirname(dir_path)
            date_str, dir_name = extract_date_for_directory(
                dir_path,
                verbose=args.verbose,
                quantiles=args.quantiles,
                min_number_of_days=args.span_days,
                file_search_recursive=not args.non_recursive,
                file_patterns=MEDIA_FILES if not args.all_types else ["*.*"],
            )
            dir_basename = os.path.basename(dir_path)
            if not args.remove_date and not dir_basename.startswith(date_str):
                dir_name = dir_basename
            new_dir_name = f"{date_str} {dir_name}".strip()
            new_dir_path = os.path.join(parent_dir, new_dir_name)

            if dir_path != new_dir_path:
                print(f"mv '{dir_path}'  '{new_dir_path}'")
            elif args.verbose:
                print(f"# No rename needed for {dir_path}")

        except ValueError as ve:
            if args.verbose:
                print(f"# Error for {dir_path}: {ve}")
