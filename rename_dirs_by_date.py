import os
from datetime import datetime
from tabnanny import verbose
from typing import List, Dict
import file_date
import argparse
from glob import glob


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
        nargs="+",
        required=True,
        help="List of directory paths or patterns to process (wildcards supported).",
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
    return args


def compute_directory_date_quantiles(
    directory_path: str, quantiles: List[float]
) -> Dict[float, str]:
    """
    Searches a directory for files, extracts dates from filenames, and computes date quantiles.

    Args:
        directory_path: Path to the directory to search
        quantiles: List of quantile values (e.g., [0.25, 0.5, 0.75] for quartiles)

    Returns:
        Dictionary mapping quantile values to date strings in YYYY-MM-DD format

    Example:
        >>> compute_file_date_quantiles('/path/to/files', [0.25, 0.5, 0.75])
        {0.25: '2023-03-15', 0.5: '2023-06-20', 0.75: '2023-09-10'}
    """
    dates = []

    # Iterate through all files in the directory
    for filename in os.listdir(directory_path):
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

    for q in quantiles:
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
) -> str:
    """
    Extracts the date for a directory based on its name.

    Args:
        directory_path: Path to the directory
        verbose: Whether to print verbose output
        quantiles: List of quantile values (e.g., [0.25, 0.5, 0.75] for quartiles)
    """
    date_str, dir_name = file_date.extract_date_for_path(
        directory_path, verbose=verbose, modification_time_fallback=False
    )
    dir_name = dir_name.strip(" ")

    quantiles = compute_directory_date_quantiles(directory_path, quantiles)
    q_str = ", ".join([f" {q}: {date_str}" for q, date_str in quantiles.items()])
    if verbose:
        print(f"#Directory: {directory_path}. Date quantiles: {q_str}")
    quantiles = sorted(quantiles.values())

    if date_str is not None:
        return date_str, dir_name

    if quantiles[0] == quantiles[2]:
        return quantiles[1], dir_name  # All quantiles are the same, use the median

    return f"{quantiles[0]} - {quantiles[2]}", dir_name


if __name__ == "__main__":
    args = parse_args()

    # Find files using glob (wildcards supported)
    paths = []
    for pattern in args.files:
        paths += glob(pattern)

    # Keep only directories
    paths = [p for p in paths if os.path.isdir(p)]

    # Modify first the longest paths to avoid conflicts
    paths = sorted(paths, key=lambda x: -len(x))

    if not paths:
        print("No directories found matching the provided patterns.")
        exit(1)

    for dir_path in paths:
        try:
            date_str, dir_name = extract_date_for_directory(
                dir_path, args.verbose, args.quantiles
            )
            parent_dir = os.path.dirname(dir_path)
            new_dir_name = f"{date_str} {dir_name}"
            new_dir_path = os.path.join(parent_dir, new_dir_name)

            if dir_path != new_dir_path:
                print(f"mv '{dir_path}'  '{new_dir_path}'")
            elif args.verbose:
                print(f"# No rename needed for {dir_path}")

        except ValueError as ve:
            if args.verbose:
                print(f"# Error for {dir_path}: {ve}")
