import datetime
import os.path
from typing import Dict, List, Tuple


def validate_if_starts_with_date(text: str, fmt: str = "%Y-%m-%d") -> bool:
    """Returns true if beginning of text matches %Y-%m-%d."""
    try:
        datetime.datetime.strptime(text, fmt)
        return True
    except ValueError:
        pass
    return False


def _parse_filename(full_path: str) -> Tuple[str, str]:
    filename = os.path.basename(full_path)

    if (
        filename.startswith("IMG_")
        or filename.startswith("IMG-")
        or filename.startswith("VID_")
        or filename.startswith("VID-")
    ) and (filename[4:12].isdigit()):
        filename = filename[4:]  # skip prefix
        filename = (
            filename[:4] + "-" + filename[4:6] + "-" + filename[6:]
        )  # TODO validation if date

        date = filename[:10]
        suffix = filename[10:]

    elif filename.startswith("signal-"):
        filename = filename[7:]  # skip prefix
        date = filename[:10]  # TODO validation if date
        suffix = filename[10:]

    elif validate_if_starts_with_date(filename[:10]):
        date = filename[:10]  # TODO validation if date
        suffix = filename[10:]

    else:
        date = datetime.datetime.fromtimestamp(os.path.getmtime(full_path)).strftime(
            "%Y-%m-%d"
        )
        suffix = filename

    return date, suffix


def extract_meta(paths: List[str]) -> Dict[str, Dict[str, str]]:
    """Extracts meta data (e.g. creation dates) for files."""
    path2meta = dict()
    for full_path in paths:
        filename = os.path.basename(full_path)
        dirname = os.path.dirname(full_path)
        date, suffix = _parse_filename(full_path)

        path2meta[full_path] = {
            "dirname": dirname,
            "filename": filename,
            "date": date,
            "suffix": suffix,
        }

    return path2meta
