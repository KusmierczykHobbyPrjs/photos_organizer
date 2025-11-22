import argparse
from glob import glob
from typing import Dict, List, Tuple
import file_date
import os


def parse_args():
    parser = argparse.ArgumentParser(
        description="Outputs bash commands renaming files (e.g. jpegs) "
        "according to their date. "
        "Tested with python3 on Ubuntu20. "
    )

    parser.add_argument(
        "-f",
        "--files",
        type=str,
        nargs="*",
        required=False,
        default=[],
        help="list of files in a directory",
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
        default=None,
        required=False,
        help="destination directory path",
    )
    parser.add_argument(
        "-s",
        "--date_separators",
        type=str,
        nargs="+",
        default=[" ", "_", "-"],
        required=False,
        help="separators of date and suffix in file name",
    )
    parser.add_argument(
        "-c",
        "--cmd",
        type=str,
        default="mv",
        required=False,
        help="command executed for individual files",
    )
    args = parser.parse_args()
    
    args.files = list(set(args.files + args.dropped_files))

    return args


def rename_files(file2meta, target_directory=None, separators=[" ", "_"]):
    dst_src = []
    for file, meta in file2meta.items():
        dirname = target_directory or meta["dirname"]
        date, suffix = meta["date"], meta["suffix"]

        for separator in separators:
            if separator and len(separator) > 0:
                suffix = suffix.lstrip(separator)
        if len(suffix) > 0:
            suffix = separators[0] + suffix

        dst = os.path.join(dirname, f"{date}{suffix}")

        dst_src.append((dst, file))
    return dst_src


def resolve_conflicts(dst_src: List[Tuple[str, str]]) -> Dict[str, str]:
    dst_src = sorted(dst_src)  # sort by destination

    dst_src_resolved = []
    prev_dst, prev_src = None, None
    conflicts_counter = 0
    for dst, src in dst_src:

        if prev_dst and dst == prev_dst:
            conflicts_counter += 1

            parts = dst.split(".")
            if len(parts) == 1:
                dst += "-" + str(conflicts_counter)
            else:
                dst = (
                    ".".join(parts[:-1])
                    + "-"
                    + str(conflicts_counter)
                    + "."
                    + parts[-1]
                )

            print(f"# Resolving conflict between '{src}' vs '{prev_src}' -> '{dst}'.")

        else:  # update only if no conflict
            prev_dst, prev_src = dst, src
            conflicts_counter = 0

        dst_src_resolved.append((dst, src))

    return dst_src_resolved


if __name__ == "__main__":

    args = parse_args()

    ###########################################################################

    # use glob to find files matching wildcards
    # if a string does not contain a wildcard, glob will return it as is.
    file_names = []
    for arg in args.files:
        file_names += glob(arg)

    ###########################################################################

    # Modify first the longest paths to avoid conflicts
    file_names = sorted(file_names, key=lambda x: -len(x))

    print("# Renaming files to date+suffix:")
    file2meta = file_date.extract_meta(file_names)

    dst_src = rename_files(file2meta, args.target_directory, args.date_separators)
    dst_src = resolve_conflicts(dst_src)

    for dst, src in dst_src:
        if src != dst:
            print(f"{args.cmd} '{src}' '{dst}'")
    print("#############################")
