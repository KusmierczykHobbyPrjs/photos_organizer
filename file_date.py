import os
import re
from typing import Dict, List, Tuple, Optional
from datetime import datetime

import time

try:
    import exifread
except ImportError:
    print("# Exifread module not found. Please install it using 'pip install exifread'")


def debug(msg: str):    # Simple debug print function; can be enhanced to use logging
    # print("DEBUG:" + msg)
    pass



def extract_dates_range(text: str) -> Tuple[Optional[str], str]:
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


EXIF_EXTENSIONS = ["jpg", "jpeg", "png", "webp", "tif", "tiff"]

def get_exif_timestamp(path):
    # Check if correct extension
    if not any(path.lower().endswith(ext) for ext in EXIF_EXTENSIONS):
        return None

    # Open image file for reading (binary mode)
    try:
        f = open(path, "rb")
    except:
        return None
    # Return Exif tags
    tags = exifread.process_file(f)
    f.close()
    if "Image DateTime" not in tags:
        return None
    t = str(tags["Image DateTime"])
    return time.mktime(datetime.strptime(t, "%Y:%m:%d %H:%M:%S").timetuple())


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


def _valid_date_ranges(year: int, month: int, day: int) -> bool:
    # Basic range checks
    if year < 1900 or year > 2050:
        return False
    if month < 1 or month > 12:
        return False
    if day < 1 or day > 31:
        return False
    return True


def _is_valid_date(year: int, month: int, day: int) -> bool:
    """Check if the given year, month, day form a valid date."""
    if not _valid_date_ranges(year, month, day):
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
        return _valid_date_ranges(d.year, d.month, d.day)
    except ValueError:
        return False



def extract_date_from_filename_re(filename: str) -> Tuple[Optional[str], str]:
    """
    Extract date from filename in various formats.
    
    Supports:
    - Year at beginning (YYYY-MM-DD) or end (DD-MM-YYYY)
    - Separators: -, _, ., or none
    - Complete dates (YYYY-MM-DD), year+month (YYYY-MM), or year only (YYYY)
    - Validates that date is bounded by non-digits or string boundaries
    
    Returns:
        Tuple of (normalized_date_str, remaining_filename)
        Date is normalized to YYYY-MM-DD, YYYY-MM, or YYYY format
    """
    
    # Pattern components
    sep = r'[-_.\s]?'  # Optional separator (including space)
    boundary = r'(?:^|[^\d])'  # Start or non-digit
    boundary_end = r'(?:[^\d]|$)'  # Non-digit or end
    
    # Date component patterns
    year = r'(\d{4})'
    month = r'(\d{1,2})'  # 1 or 2 digits
    day = r'(\d{1,2})'    # 1 or 2 digits
    
    # All possible date patterns with word boundaries
    # Format: (pattern, format_type, component_order)
    # IMPORTANT: Order matters! More specific patterns (full dates) must come before less specific (year-only)
    date_patterns = [
        # Full date patterns first (most specific)
        # YYYY-MM-DD variants (year first)
        (rf'{boundary}{year}{sep}{month}{sep}{day}{boundary_end}', 'YMD', ['year', 'month', 'day']),
        # DD-MM-YYYY variants (year last)
        (rf'{boundary}{day}{sep}{month}{sep}{year}{boundary_end}', 'DMY', ['day', 'month', 'year']),
        # MM-DD-YYYY variants (year last, US format)
        # (rf'{boundary}{month}{sep}{day}{sep}{year}{boundary_end}', 'MDY', ['month', 'day', 'year']),
        
        # Partial date patterns (less specific)
        # YYYY-MM variants (year + month only)
        (rf'{boundary}{year}{sep}{month}{boundary_end}', 'YM', ['year', 'month']),
        # YYYY variants (year only) - least specific, must come last
        (rf'{boundary}{year}{boundary_end}', 'Y', ['year']),
    ]
    
    debug(f"#Extracting date from filename: {filename}")
    for pattern, format_type, components in date_patterns:
        match = re.search(pattern, filename)
        if match:
            debug(f"#Matched pattern: {pattern} in filename: {filename}")
            # Extract the full matched string (including boundary context)
            full_match = match.group(0)
            
            # Extract date components (groups start at 1)
            groups = match.groups()
            
            # Map components to their values
            date_parts = {}
            group_idx = 0
            for comp in components:
                # Skip the boundary group (first group)
                date_parts[comp] = groups[group_idx]
                group_idx += 1
            
            debug(f"#Extracted date parts: {date_parts}")
            # Validate date components
            try:
                year_val = int(date_parts['year'])
                if year_val < 1950 or year_val > 2050:
                    continue
                
                if 'month' in date_parts:
                    month_val = int(date_parts['month'])
                    if month_val < 1 or month_val > 12:
                        continue
                
                if 'day' in date_parts:
                    day_val = int(date_parts['day'])
                    if day_val < 1 or day_val > 31:
                        continue
                    
                    # Validate actual date exists
                    datetime(year_val, month_val, day_val)
                
            except (ValueError, KeyError):
                continue
            
            # Build normalized date string in YYYY-MM-DD format
            if format_type in ['YMD', 'DMY', 'MDY']:
                # Pad month and day with leading zeros
                month_str = date_parts['month'].zfill(2)
                day_str = date_parts['day'].zfill(2)
                date_str = f"{date_parts['year']}-{month_str}-{day_str}"
            elif format_type == 'YM':
                month_str = date_parts['month'].zfill(2)
                date_str = f"{date_parts['year']}-{month_str}"
            else:  # Y
                date_str = date_parts['year']
            debug(f"#Normalized date string: {date_str}")
            
            # Find the actual date portion (without boundary characters)
            # by matching just the digits and separators in the correct order
            if format_type == 'YMD':
                date_only_pattern = rf'{year}{sep}{month}{sep}{day}'
            elif format_type == 'DMY':
                date_only_pattern = rf'{day}{sep}{month}{sep}{year}'
            elif format_type == 'MDY':
                date_only_pattern = rf'{month}{sep}{day}{sep}{year}'
            elif format_type == 'YM':
                date_only_pattern = rf'{year}{sep}{month}'
            else:  # Y
                date_only_pattern = year
            debug(f"#Date only pattern: {date_only_pattern}")
            
            date_match = re.search(date_only_pattern, full_match)
            debug(f"#Date match for remaining filename extraction: {date_match}")
            if date_match:
                matched_date = date_match.group(0)
                # Remove the matched date from filename
                remaining = filename.replace(matched_date, '', 1).strip()
                # Clean up any double separators or leading/trailing separators
                remaining = re.sub(r'[-_.\s]{2,}', ' ', remaining)
                remaining = remaining.strip('-_. ')
                
                return date_str, remaining
    
    return None, filename


def extract_date_for_path(
    full_path: str, verbose: bool = False, modification_time_fallback: bool = True
) -> Tuple[str, str]:
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
    date, suffix = None, filename
    debug(f"#==========Extracting date for file: {full_path}==========")

    # Patterns like IMG_YYYYMMDD or VID_YYYYMMDD
    if (date is None  
        and filename.upper().startswith(("IMG_", "IMG-", "VID_", "VID-", "PIX_", "PXL_"))
        and filename[4:12].isdigit()
    ):
        filename = filename[4:]  # Skip the prefix (e.g., IMG_)
        # Convert the YYYYMMDD to YYYY-MM-DD
        date = f"{filename[:4]}-{filename[4:6]}-{filename[6:8]}"
        suffix = filename[8:]

        # Validate the date format
        if not _is_valid_date_string(date):
            date, suffix = None, filename

    # Files that start with 'signal-' followed by a date
    if date is None and filename.startswith("signal-") and _is_valid_date_string(filename[7:17]):
        date = filename[7:17]  # Extract the date from the filename
        suffix = filename[17:]

    # General case where the filename starts with a date
    if date is None and len(filename) >= 10 and _is_valid_date_string(filename[:10]):
        date = filename[:10]  # Extract the date from the first 10 characters
        suffix = filename[10:]

    if date is None:
        try:
            debug(f"#Regex date for: <{filename}>")
            date, suffix = extract_date_from_filename_re(filename)
        except:
            date, suffix = None, filename

    if date is None:
        try:
            debug(f"#Exif date for {full_path}")
            date_exif = get_exif_timestamp(full_path)

            if date_exif is not None:
                date = datetime.fromtimestamp(date_exif).strftime("%Y-%m-%d")
                suffix = filename
                debug(f"# Extracted Exif date: {date} for {full_path}")

        except Exception as e:
            debug(f"# Exif date extraction failed for {full_path}: {e}")
            date, suffix = None, filename

    if date is None and modification_time_fallback:
        try:
            # Fallback: Use file's modification time if no date can be parsed from filename
            debug(f"#Using modification time for {full_path}")
            date = _extract_timestamp_as_date(full_path)
            suffix = filename
        except Exception as e:
            if verbose:
                print(f"# Failed to parse {full_path} -> {filename}: {e}")
            date, suffix = None, filename

    date = date or ""
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
        date, suffix = extract_date_for_path(full_path, verbose=True)

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
        "report_2024-03-15_final.pdf",
        "2024_03_15_document.txt",
        "photo.2024.03.15.jpg",
        "20240315data.csv",
        "data_15-03-2024.xlsx",
        "meeting_notes_2024-03.txt",
        "budget_2024.pdf",
        "file_2024-13-45_invalid.txt",  # Invalid date
        "simple_file.txt",  # No date
        "year2024month03day15file.txt",  # Date without separators embedded
        "2024-03-15",  # Just a date
        "2023.06.06-Festyn-64.jpg", 
        "prefix_2024-03_suffix.txt",  # Year-month only
        "report-2024-03-15-final",
        "backup_20240315_data",
        "file 2024 12 25 version2",
        "project-2024-2-5-draft",
        "document_20231231_summary",
        "no_date_here",
        "meeting-2024-13-45-notes",  # Invalid date
        "data_2024_1_1_test",
        "report_2024-03-15_final.pdf",
        "2024_03_15_document.txt",
        "photo.2024.03.15.jpg",
        "20240315data.csv",
        "data_15-03-2024.xlsx",
        "meeting_notes_2024-03.txt",
        "budget_2024.pdf",
        "file_2024-13-45_invalid.txt",  # Invalid date
        "simple_file.txt",  # No date
        "year2024month03day15file.txt",  # Date without separators embedded
        "2024-03-15",  # Just a date
        "prefix_2024-03_suffix.txt",  # Year-month only
        "report 2024 3 15 final.pdf",  # Space separator with single digits
        "photo_2024_3_5.jpg",  # Single digit month and day
        "meeting 2024 3.txt",  # Space separator, year-month
        "data 15 3 2024.xlsx",  # Space separator, day-first
        "file_2024-3-5_test.txt",  # Mixed: dash separator, single digits
        "Absolutorium Ani 9-10.07.2016r",
    ]
    
    for test in test_cases:
        date, remaining = extract_date_from_filename_re(test)
        print(f"Input: {test} | Date: {date} | Remaining: {remaining}")

