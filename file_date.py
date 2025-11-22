import os
import re
from typing import Dict, List, Tuple, Optional
from datetime import datetime


def _extract_timestamp_as_date(full_path: str) -> str:
    """
    Extracts the file's modification time and converts it to a date string (YYYY-MM-DD).

    Args:
        full_path (str): The full path of the file.

    Returns:
        str: A string representing the file's modification date in "YYYY-MM-DD" format.
    """
    timestamp = os.path.getmtime(full_path)
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d")


def extract_date_from_string(text: str) -> Tuple[Optional[str], str]:
    """
    Extracts date from a string split by '-', '_', or space, and returns the date
    in YYYY-MM-DD format along with the remaining text.

    Args:
        text: Input string that may contain a date

    Returns:
        Tuple of (formatted_date, remaining_text) where:
        - formatted_date is a string in YYYY-MM-DD format or None if no date found
        - remaining_text is the input string with date components removed

    Examples:
        >>> extract_date_from_string("report-2024-03-15-final")
        ('2024-03-15', 'report-final')

        >>> extract_date_from_string("backup_20240315_data")
        ('2024-03-15', 'backup_data')
    """
    if not text:
        return None, text

    # Split by delimiters while keeping track of original structure
    parts = re.split(r"[-_\s]+", text)

    # Try to find date patterns in consecutive parts
    date_patterns = [
        # YYYYMMDD (compact format)
        (r"^(\d{8})$", lambda m: _parse_compact_date(m.group(1))),
        # YYYY MM DD or YYYY-MM-DD variants
        (r"^(\d{4})$", None),  # Year - need to check next parts
    ]

    found_date = None
    date_indices = []

    # Scan through parts looking for date components
    i = 0
    while i < len(parts):
        part = parts[i]

        # Check for compact YYYYMMDD format
        if re.match(r"^\d{8}$", part):
            parsed = _parse_compact_date(part)
            if parsed:
                found_date = parsed
                date_indices = [i]
                break

        # Check for YYYY-MM-DD pattern across consecutive parts
        if i + 2 < len(parts):
            year_match = re.match(r"^(\d{4})$", parts[i])
            month_match = re.match(r"^(\d{1,2})$", parts[i + 1])
            day_match = re.match(r"^(\d{1,2})$", parts[i + 2])

            if year_match and month_match and day_match:
                year = int(parts[i])
                month = int(parts[i + 1])
                day = int(parts[i + 2])

                if _is_valid_date(year, month, day):
                    found_date = f"{year:04d}-{month:02d}-{day:02d}"
                    date_indices = [i, i + 1, i + 2]
                    break

        # Check for YYYYMM or MMDDYYYY variations
        if re.match(r"^\d{6}$", part):
            # Could be YYYYMM or MMDDYY
            parsed = _try_parse_six_digit(part)
            if parsed:
                found_date = parsed
                date_indices = [i]
                break

        i += 1

    # Build remaining text by excluding date parts
    if found_date:
        remaining_parts = [parts[j] for j in range(len(parts)) if j not in date_indices]
        remaining_text = " ".join(p for p in remaining_parts if p)
    else:
        remaining_text = text

    return found_date, remaining_text


def _parse_compact_date(s: str) -> Optional[str]:
    """Parse YYYYMMDD format string."""
    if len(s) != 8:
        return None

    try:
        year = int(s[0:4])
        month = int(s[4:6])
        day = int(s[6:8])

        if _is_valid_date(year, month, day):
            return f"{year:04d}-{month:02d}-{day:02d}"
    except ValueError:
        pass

    return None


def _try_parse_six_digit(s: str) -> Optional[str]:
    """Try to parse 6-digit date formats (YYYYMM, MMDDYY, etc.)."""
    if len(s) != 6:
        return None

    # Try YYMMDD (assuming 20YY for years)
    try:
        year = 2000 + int(s[0:2])
        month = int(s[2:4])
        day = int(s[4:6])

        if _is_valid_date(year, month, day):
            return f"{year:04d}-{month:02d}-{day:02d}"
    except ValueError:
        pass

    return None


def _is_valid_date(year: int, month: int, day: int) -> bool:
    """Check if the given year, month, day form a valid date."""
    # Basic range checks
    if year < 1900 or year > 2100:
        return False
    if month < 1 or month > 12:
        return False
    if day < 1 or day > 31:
        return False

    # Use datetime to validate the actual date
    try:
        datetime(year, month, day)
        return True
    except ValueError:
        return False


def _is_valid_date_string(text: str, fmt: str = "%Y-%m-%d") -> bool:
    """
    Validates if the given string starts with a valid date in the format provided.

    Args:
        text (str): The string to validate.
        fmt (str): The date format to check against (default: "%Y-%m-%d").

    Returns:
        bool: True if the beginning of the string matches the date format, False otherwise.
    """
    try:
        d = datetime.strptime(text, fmt)
        return (
            d.year >= 1900
            and d.year <= 2100
            and d.month >= 1
            and d.month <= 12
            and d.day >= 1
            and d.day <= 31
        )  # Basic range checks
    except ValueError:
        return False


def extract_date_from_filename_re(filename: str) -> Tuple[str, str]:

    # Regular expressions to match different date formats
    date_patterns = [
        re.compile(r"(\d{4}-\d{2}-\d{2})"),  # Match YYYY-MM-DD
        re.compile(r"(\d{4}_\d{2}_\d{2})"),  # Match YYYY_MM_DD
        re.compile(r"(\d{8})"),  # Match YYYYMMDD
    ]

    
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
            date_str = datetime.strptime(date_str, "%Y%m%d").strftime("%Y-%m-%d")
        elif re.match(
            r"\d{4}_\d{2}_\d{2}", date_str
        ):  # Convert YYYY_MM_DD to YYYY-MM-DD
            date_str = date_str.replace("_", "-")

        # Create the new filename
        remaining_str = filename.replace(
            match.group(1), ""
        ).strip()  # Remove matched date  # Remove trailing spaces

        return date_str, remaining_str

    return None, filename


def extract_date_for_filename(full_path: str) -> Tuple[str, str]:
    """
    Attempts to extract the date from the filename. If unsuccessful, extracts the date
    from the file's modification timestamp.

    Args:
        full_path (str): The full path of the file.

    Returns:
        Tuple[str, str]: A tuple containing the date (as a string in "YYYY-MM-DD" format)
                         and the remaining part of the filename (suffix).
    """
    filename = os.path.basename(full_path)

    # Patterns like IMG_YYYYMMDD or VID_YYYYMMDD
    if (
        filename.upper().startswith(("IMG_", "IMG-", "VID_", "VID-", "PIX_", "PXL_"))
        and filename[4:12].isdigit()
    ):
        filename = filename[4:]  # Skip the prefix (e.g., IMG_)
        # Convert the YYYYMMDD to YYYY-MM-DD
        date = f"{filename[:4]}-{filename[4:6]}-{filename[6:8]}"
        suffix = filename[8:]

        # Validate the date format
        if not _is_valid_date_string(date):
            date = _extract_timestamp_as_date(full_path)

    # Files that start with 'signal-' followed by a date
    elif filename.startswith("signal-") and _is_valid_date_string(
        filename[7:17]
    ):
        date = filename[7:17]  # Extract the date from the filename
        suffix = filename[17:]

    # General case where the filename starts with a date
    elif len(filename)>=10 and _is_valid_date_string(filename[:10]):
        date = filename[:10]  # Extract the date from the first 10 characters
        suffix = filename[10:]

    else:
        try:
            date, suffix = extract_date_from_filename_re(filename)
        except:
            date, suffix = None, filename

        if date is None:
            date, suffix = extract_date_from_string(filename)

        if date is None:
            try:
                # Fallback: Use file's modification time if no date can be parsed from filename
                date = _extract_timestamp_as_date(full_path)
                suffix = filename
            except:
                print(f"# Failed to parse {full_path} -> {filename}")
                date, suffix = "", filename

    return date, suffix


def extract_meta(paths: List[str]) -> Dict[str, Dict[str, str]]:
    """
    Extracts metadata (date and suffix) for a list of file paths.

    Args:
        paths (List[str]): List of file paths for which metadata is to be extracted.

    Returns:
        Dict[str, Dict[str, str]]: A dictionary where each key is a file path, and the value is another dictionary containing:
            - 'dirname': The directory name of the file.
            - 'filename': The filename.
            - 'date': The extracted or fallback date (in "YYYY-MM-DD" format).
            - 'suffix': The remaining part of the filename after the date.
    """
    path2meta = {}
    for full_path in paths:
        filename = os.path.basename(full_path)
        dirname = os.path.dirname(full_path)
        date, suffix = extract_date_for_filename(full_path)

        path2meta[full_path] = {
            "dirname": dirname,
            "filename": filename,
            "date": date,
            "suffix": suffix,
        }

    return path2meta


# Test examples
if __name__ == "__main__":
    test_cases = [
        "report-2024-03-15-final",
        "backup_20240315_data",
        "file 2024 12 25 version2",
        "project-2024-2-5-draft",
        "document_20231231_summary",
        "no_date_here",
        "meeting-2024-13-45-notes",  # Invalid date
        "data_2024_1_1_test",
    ]

    print("Testing date extraction:\n")
    for test in test_cases:
        date, remaining = extract_date_from_string(test)
        print(f"Input:     '{test}'")
        print(f"Date:      {date}")
        print(f"Remaining: '{remaining}'")
        print()
