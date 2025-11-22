#!/usr/bin/env python3
"""Generate ImageMagick commands to annotate images with dates and/or directory names."""

import argparse
from pathlib import Path
from PIL import Image

from path_matcher import match_paths
import file_date


def get_image_size(filepath):
    """Return image dimensions or None if not a valid image."""
    try:
        with Image.open(filepath) as img:
            return img.size
    except Exception:
        # print(f"#FAILED FOR {filepath}. NOT AN IMAGE?")
        return None


def process_image(
    filepath,
    annotation_text=None,
    annotate_with_date: bool = True,
    gravity="southeast",
    text_divisor=30,
    rename_prefix=None,
    resize_config=None,
):
    """
    Generate ImageMagick commands for a single image.

    Args:
        filepath: Path to the image file
        annotation_text: Text to annotate (e.g., directory name)
        annotate_with_date: Whether to annotate with date extracted from image
        gravity: Text position (southeast, southwest, etc.)
        text_divisor: Divisor for calculating text size (smaller = larger text)
        rename_prefix: If provided, rename file with this prefix
        resize_config: Dict with resize settings or None to skip resizing
                      {'max_dimension': int, 'max_file_size_kb': int,
                       'target_dimension': int, 'quality': int}
    """
    filepath = Path(filepath)

    img_size = get_image_size(filepath)
    if not img_size:
        return

    file_size = filepath.stat().st_size
    # Calculate initial text size based on image dimensions
    # Larger images get proportionally larger text
    pointsize = max(img_size) // text_divisor

    # RESIZING: Reduce image dimensions and file size if needed
    # This is useful for web display or when storage space is limited
    # Original images from modern cameras are often 4000x3000px and 5+ MB
    if resize_config:
        max_dim = resize_config.get("max_dimension", 1600)
        max_size_kb = resize_config.get("max_file_size_kb", 300)
        target_dim = resize_config.get("target_dimension", 1200)
        quality = resize_config.get("quality", 80)

        # Check if image exceeds dimension OR file size thresholds
        if max(img_size) > max_dim or file_size > max_size_kb * 1024:
            # Calculate scale percentage to fit within target dimension
            # e.g., 2400px image -> 1200px target = 50% scale
            scale = min(100, int(100 * target_dim / max(img_size)))

            # Generate resize command with quality reduction for JPEG compression
            print(
                f"convert '{filepath}' -quality {quality}% -resize {scale}% '{filepath}'"
            )

            # Adjust text size proportionally to the resize
            # If image scaled to 50%, text should also be 50% of original size
            pointsize = int(pointsize * scale / 100)

    # Build annotation text
    annotations = []

    if annotate_with_date:
        try:
            date, _ = file_date.extract_date_for_path(str(filepath))
            if date:
                annotations.append(date)
        except Exception:
            print(f"#WARNING: Could not extract date from {filepath}")

    if annotation_text:
        annotations.append(annotation_text)

    # Generate annotation command
    if annotations:
        full_annotation = " ".join(annotations)
        print(
            f"convert '{filepath}' -gravity {gravity} -pointsize {pointsize} "
            f"-fill yellow -annotate 0 \"{full_annotation}\" '{filepath}'"
        )


def main():
    args = parse_args()

    file_paths = match_paths(args.files, recursive=args.recursive)

    if not file_paths:
        print("#ERROR: No files found matching the patterns")
        return

    # Configure resizing if enabled
    resize_config = None
    if args.resize:
        resize_config = {
            "max_dimension": args.resize_max_dimension,
            "max_file_size_kb": args.resize_max_filesize,
            "target_dimension": args.resize_target_dimension,
            "quality": args.resize_quality,
        }
        print(
            f"#RESIZE ENABLED: Images >{args.resize_max_dimension}px or "
            f">{args.resize_max_filesize}KB will be resized to {args.resize_target_dimension}px "
            f"at {args.resize_quality}% quality"
        )

    # Process each file
    print(f"#PROCESSING {len(file_paths)} file(s)")

    for filepath in file_paths:
        filepath = Path(filepath)

        # Get annotation text (directory name if requested)
        if args.dirname:
            if args.date:  # Avoid redundant date extraction
                _, annotation = file_date.extract_date_for_path(
                    filepath.parent.name, modification_time_fallback=False
                )
            else:
                annotation = filepath.parent.name
            annotation = annotation.strip("_- ")
        else:
            annotation = None

        # Process the image
        try:
            process_image(
                filepath=filepath,
                annotation_text=annotation,
                annotate_with_date=args.date,
                gravity=args.gravity,
                text_divisor=args.text_size,
                resize_config=resize_config,
            )
        except Exception as e:
            print(f"#ERROR processing {filepath}: {e}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate ImageMagick annotation commands for images",
        epilog="Examples:\n"
        "  %(prog)s -f *.jpg\n"
        "  %(prog)s -f dir1/*.png dir2/*.jpg --dirname\n"
        "  %(prog)s -f **/*.jpg --gravity southwest",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "-f",
        "--files",
        type=str,
        nargs="*",
        required=False,
        default=[],
        help="List of files or wildcard patterns (e.g., *.jpg dir/**/*.png)",
    )
    # Support drag-and-drop file input
    parser.add_argument(
        'dropped_files', 
        nargs='*',      # Accepts zero or more files
        default=[],     # Default to empty list
        help='List of files (drag and drop)'
    )

    parser.add_argument(
        "-r",
        "--recursive",
        action="store_false",
        help="Recursively search directories for images",
        default=True,
    )

    parser.add_argument(
        "--date",
        action="store_false",
        help="Annotate with date extracted from image (default: enabled)",
        default=True,
    )

    parser.add_argument(
        "-d",
        "--dirname",
        action="store_true",
        help="Annotate with parent directory name (default: disabled)",
        default=False,
    )

    parser.add_argument(
        "--gravity",
        type=str,
        default="southeast",
        choices=[
            "northwest",
            "north",
            "northeast",
            "west",
            "center",
            "east",
            "southwest",
            "south",
            "southeast",
        ],
        help="Text position (default: southeast)",
    )

    parser.add_argument(
        "--text-size",
        type=int,
        default=30,
        help="Text size divisor - smaller number = larger text (default: 30)",
    )

    parser.add_argument(
        "--resize",
        action="store_true",
        help="Enable image resizing to reduce file size and dimensions",
        default=False,
    )

    parser.add_argument(
        "--resize-max-dimension",
        type=int,
        default=1600,
        help="Resize images larger than this dimension in pixels (default: 1600)",
    )

    parser.add_argument(
        "--resize-max-filesize",
        type=int,
        default=300,
        help="Resize images larger than this size in KB (default: 300)",
    )

    parser.add_argument(
        "--resize-target-dimension",
        type=int,
        default=1200,
        help="Target maximum dimension after resizing in pixels (default: 1200)",
    )

    parser.add_argument(
        "--resize-quality",
        type=int,
        default=85,
        help="JPEG quality for resized images, 0-100 (default: 85)",
    )

    args = parser.parse_args()

    if not args.date and not args.dirname:
        raise ValueError("If no date is requested, dirname must be enabled!")
    
    args.files = list(set(args.files + args.dropped_files))

    return args


if __name__ == "__main__":
    main()
