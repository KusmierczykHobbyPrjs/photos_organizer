#!/usr/bin/env python
import time, os
from stat import ST_MTIME
import datetime
from dateutil import parser
import exifread

#REQUIREMENTS:
#pip install exifread



def get_exif_timestamp(path):
    # Open image file for reading (binary mode)
    try:    f = open(path, 'rb')	
    except: return None
    # Return Exif tags
    tags = exifread.process_file(f)
    f.close()
    if "Image DateTime" not in tags: return None
    t = str(tags["Image DateTime"])
    return time.mktime(datetime.datetime.strptime(t, "%Y:%m:%d %H:%M:%S").timetuple())


def get_image_timestamp(path):
    basepath = os.path.basename(path).replace("_", " ").replace("IMG_", " ")
    basepath = ".".join(basepath.split(".")[ :-1])
    try:    return time.mktime(datetime.datetime.strptime(basepath.split(" ")[0], "%Y-%m-%d").timetuple())
    except: pass  
    try:    return parser.parse(path).total_seconds()
    except: pass
    try:    return time.mktime(datetime.datetime.strptime(basepath.split(" ")[0], "%Y%m%d").timetuple())
    except: pass
    date = get_exif_timestamp(path)
    if date is None:    
        date = os.stat(path)[ST_MTIME]
    return date


def get_image_date(path, fmt='%Y-%m-%d'):
    def timestamp_to_date(timestamp):
        return datetime.datetime.fromtimestamp(timestamp).strftime(fmt) 
    return timestamp_to_date(get_image_timestamp(path))


