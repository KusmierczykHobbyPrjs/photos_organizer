import argparse
from glob import glob
from typing import Dict, List
import os


def parse_args():
    parser = argparse.ArgumentParser(description="TODO")

    parser.add_argument(
        "-l",
        "--left_files",
        type=str,
        nargs="+",
        required=True,
        help="list of files in a directory",
    )
    parser.add_argument(
        "-r",
        "--right_files",
        type=str,
        nargs="+",
        required=False,
        default=None,
        help="list of files in a directory",
    )
    parser.add_argument(
        "-c",
        "--cmd",
        type=str,
        required=False,
        default='rm -rf',
        help="command applied to duplicates",
    )    

    args = parser.parse_args()
    return args



_stats_cache = {}


def get_size(file1):
    stats1 = _stats_cache.setdefault(file1, os.stat(file1))
    return stats1.st_size


def are_equal(file1, file2, start_bytes=1024, end_bytes=1024, mid_bytes=1024):
    if os.path.isdir(file1) or os.path.isdir(file2):
        return False

    size1 = get_size(file1)
    size2 = get_size(file2)

    # compare sizes:
    if size1 != size2:
        return False
    fsize = size1
    
    return True

    # compare start bytes
    nb = min(start_bytes, fsize)
    f1 = open(file1, "rb")
    f2 = open(file2, "rb")
    b1, b2 = f1.read(nb), f2.read(nb)
    f1.close()
    f2.close()

    if b1 != b2:
        return False
        
    # compare middle bytes:
    sb = fsize//2
    nb = min(sb+mid_bytes, fsize) - sb
    f1 = open(file1, "rb")
    f1.seek(sb, os.SEEK_END)
    b1 = f1.read(nb)
    f1.close()

    f2 = open(file2, "rb")
    f2.seek(sb, os.SEEK_END)
    b2 = f2.read(nb)
    f2.close()

    if b1 != b2:
        return False

    # compare end bytes:
    nb = min(end_bytes, fsize)
    f1 = open(file1, "rb")
    f1.seek(-nb, os.SEEK_END)
    b1 = f1.read(nb)
    f1.close()

    f2 = open(file2, "rb")
    f2.seek(-nb, os.SEEK_END)
    b2 = f2.read(nb)
    f2.close()

    if b1 != b2:
        return False

    return True


if __name__ == "__main__":

    args = parse_args()

    ###########################################################################

    # use glob to find files matching wildcards
    # if a string does not contain a wildcard, glob will return it as is.
    left_files = []
    for arg in args.left_files:
        left_files += glob(arg)
    print(f"# Considering {len(left_files)} (left) files")

    if args.right_files:
        right_files = []
        for arg in args.right_files:
            right_files += glob(arg)
        print(f"# Considering {len(right_files)} right files")
    else:
        right_files = left_files

    ###########################################################################

    considered = set()
    for i, file1 in enumerate(left_files):
        if i % (len(left_files) // 100 + 1) == 0:
            print(f"# {i}/{len(left_files)}")
            
        for file2 in right_files:

            if file1 == file2 or (file1, file2) in considered:
                continue
                
            if are_equal(file1, file2):                
                print(f"# Duplicates (of size={get_size(file1)/1024:.1f}KB) detected: display '{file1}' & display '{file2}' & ")
                if len(file1)<len(file2):
                    print(f"{args.cmd} '{file2}'")
                else:
                    print(f"{args.cmd} '{file2}'")
                    
            considered.add( (file1, file2) )
            considered.add( (file2, file1) )            
               
