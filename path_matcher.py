from glob import glob
import os


def match_paths(patterns, recursive=True, verbose=False):
    # Expand wildcards to get all matching files
    file_paths = []
    for pattern in patterns:
        if os.path.isdir(pattern):
            pattern = (
                os.path.join(pattern, "**") if recursive else os.path.join(pattern, "*")
            )
        if verbose:
            print(f"#Searching for files matching pattern: {pattern}")
        matches = glob(pattern, recursive=recursive)
        if matches:
            file_paths.extend(matches)
        else:
            # If glob returns nothing, the pattern might be a literal filename
            file_paths.append(pattern)
    return file_paths
