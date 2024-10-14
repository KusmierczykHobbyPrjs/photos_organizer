import argparse
from glob import glob
from typing import Dict, List
import file_date
import os


def parse_args():
    parser = argparse.ArgumentParser(
        description="Outputs bash commands grouping files (e.g. jpegs) "
        "according to their date. "
        "Tested with python3 on Ubuntu20. "
    )

    parser.add_argument(
        "-f",
        "--files",
        type=str,
        nargs="+",
        required=True,
        help="list of files in a directory",
    )
    parser.add_argument(
        "-d",
        "--target_directory",
        type=str,
        default=".",
        required=False,
        help="destination directory path",
    )
    parser.add_argument(
        "-s",
        "--suffix",
        type=str,
        default="",
        required=False,
        help="directory name suffix",
    )
    parser.add_argument(
        "-p",
        "--prefix",
        type=str,
        default="",
        required=False,
        help="directory name prefix",
    )
    parser.add_argument(
        "-n",
        "--min_n_files",
        type=int,
        default=3,
        required=False,
        help="minimum number of files to create a directory",
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
    args.target_directory = args.target_directory.rstrip("/")
    return args


def move_files(file2meta, args):
    dst2files = {}
    for file, meta in file2meta.items():
        dst = meta["date"]
        # translate dir to full path:
        dst = os.path.join(
            args.target_directory, f"{args.prefix}{dst}{args.suffix}{os.path.sep}"
        )
        dst2files.setdefault(dst, []).append(file)
    return dst2files


def merge_small_directories(
    dst2files: Dict[str, str], args: argparse.Namespace
) -> Dict[str, str]:
    dst2files2 = {}
    default_dst_files = []
    for dst, files in dst2files.items():
        if len(files) < args.min_n_files:
            print(
                f"# Too few files (={len(files)}) for {dst}. Moving {files} to the common directory."
            )
            default_dst_files.extend(files)
        else:
            dst2files2[dst] = files
    dst2files2[args.target_directory + os.path.sep] = default_dst_files
    return dst2files2


def resolve_conflicts(files: List[str]) -> Dict[str, str]:
    files = sorted(files, key=lambda path: os.path.basename(path))  # sort by filename

    src2dst = {}
    prev_filename, prev_path = None, None
    conflicts_counter = 0
    for path in files:
        filename = os.path.basename(path)

        if prev_filename and filename == prev_filename:
            conflicts_counter += 1

            parts = filename.split(".")
            if len(parts) == 1:
                filename += "-" + str(conflicts_counter)
            else:
                filename = (
                    ".".join(parts[:-1])
                    + "-"
                    + str(conflicts_counter)
                    + "."
                    + parts[-1]
                )

            print(
                f"# Conflict between '{prev_path}' and '{path}' resolved by renaming to '{filename}'."
            )

        else:  # update only if no conflict
            prev_filename, prev_path = filename, path
            conflicts_counter = 0

        src2dst[path] = filename

    return src2dst


if __name__ == "__main__":

    args = parse_args()

    ###########################################################################

    # use glob to find files matching wildcards
    # if a string does not contain a wildcard, glob will return it as is.
    file_names = []
    for arg in args.files:
        file_names += glob(arg)

    ###########################################################################

    print("# Moving files to directories matching their date:")
    file2meta = file_date.extract_meta(file_names)
    dst2files = move_files(file2meta, args)
    dst2files = merge_small_directories(dst2files, args)
    dst2files = {dst: sorted(files) for dst, files in dst2files.items()}

    for dir, files in sorted(dst2files.items()):

        print(f"mkdir -p '{dir}'")

        files2dst_file_name = resolve_conflicts(files)

        for file, dst_file_name in files2dst_file_name.items():
            target = os.path.join(dir, dst_file_name)
            print(f"{args.cmd} '{file}' '{target}'")
    print("#############################")
