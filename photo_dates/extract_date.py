#!/usr/bin/env python
import os, sys
from photo_dates import *


#PREFIX_DATE_FORMAT = '%Y%m%d_%H%M%S'
PREFIX_DATE_FORMAT = '%Y-%m-%d'
FILENAME_FORMAT = "%(date)s %(name)s.%(ext)s"
#FILENAME_FORMAT = "%(date)s_T%(no)s.%(ext)s"

if __name__=="__main__":
    print "#GENERATES (BASH) COMMANDS THAT SUGGEST RENAMING IMAGES FROM THE SELECTED DIRECTORY"

    # path to the directory (relative or absolute)
    dirpath = sys.argv[1] if len(sys.argv) == 2 else r'.'
    print "#DIRECTORY: %s" % dirpath
    entries = (os.path.join(dirpath, fn) for fn in os.listdir(dirpath))


    for i, src_path in enumerate(entries):
        fname = os.path.basename(src_path).split(".")
        name, ext = ".".join(fname[:-1]), fname[-1]
        date = get_image_date(src_path, PREFIX_DATE_FORMAT)
        #dst_path = os.path.join(dirpath, "%s.%s" % (date,fname.split(".")[-1]))
        dst_path = os.path.join(dirpath, FILENAME_FORMAT % {"date": date, "name": name.replace(" ", "_"), "ext": ext, "no": ("%4s" % i).replace(" ", "0") } )
        print "#FILE:%s DATE:%s" % (src_path, date)
        print "#mv '%s' '%s'" % (src_path, dst_path)




