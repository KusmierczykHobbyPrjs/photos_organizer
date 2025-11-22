#!/usr/bin/env python
#REQUIREMENTS:
#pip install exifread


import os, sys
from photo_dates import *
from PIL import Image



if __name__=="__main__":
    print "#GENERATES (BASH) COMMANDS TO ANNOTATE (WITH DATES) IMAGES FROM THE SELECTED DIRECTORY"

    # path to the directory (relative or absolute)
    dirpath = sys.argv[1] if len(sys.argv) == 2 else r'.'
    print "#DIRECTORY: %s" % dirpath
    entries = (os.path.join(dirpath, fn) for fn in os.listdir(dirpath))


    for src_path in entries:
        fname = os.path.basename(src_path)
        try: 
            im = Image.open(src_path)
        except:
            print "#FAILED FOR %s. NOT AN IMAGE?" % src_path
            continue
        date = get_image_date(src_path)
        pointsize = max(im.size)/30
        print "convert '%s' -gravity southeast -pointsize %i -fill yellow  -annotate 0 \"%s \" '%s'" % (src_path, pointsize, date, src_path)
