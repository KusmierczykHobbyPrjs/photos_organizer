#!/usr/bin/env python
#REQUIREMENTS:
#pip install exifread


import os, sys
#from photo_dates import *
from PIL import Image


def getSize(fileobject):
    fileobject = open(fileobject, 'rb')
    fileobject.seek(0,2) # move the cursor to the end of the file
    size = fileobject.tell()
    return size


if __name__=="__main__":
    print "#GENERATES (BASH) COMMANDS TO ANNOTATE IMAGES FROM THE SELECTED DIRECTORY"

    # path to the directory (relative or absolute)
    dirpath = sys.argv[1] if len(sys.argv) == 2 else r'.'
    print "#DIRECTORY: %s" % dirpath


    for dn in os.listdir(dirpath):
        print "#SUBDIRECTORY: %s" % dn
        dirpath1 = os.path.join(dirpath, dn)
        entries = (os.path.join(dirpath1, fn) for fn in os.listdir(dirpath1))
        for src_path in entries:
            fname = os.path.basename(src_path)
            try: 
                im = Image.open(src_path)
            except:
                print "#FAILED FOR %s. NOT AN IMAGE?" % src_path
                continue
            #date = get_image_date(src_path)

            pointsize = max(im.size)/15
            if max(im.size)>1600 or getSize(src_path)>300:
                scale = min(100, 100*1200/max(im.size))
                print "convert '%s'  -quality 80%% -resize %i%%  '%s'" % (src_path, scale, src_path)
                pointsize = pointsize*scale/100
            
            
            print "convert '%s' -gravity southwest -pointsize %i -fill yellow  -annotate 0 \" %s \" '%s'" % (src_path, pointsize, dn, src_path)
            print "mv '%s' '%s'" % (src_path, dirpath1+"/"+dn+" "+fname)
