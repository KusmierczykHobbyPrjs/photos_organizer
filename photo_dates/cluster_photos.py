#!/usr/bin/env python
import os, sys
from photo_dates import *

MAX_TIME_GAP_H = 48
MAX_TIME_GAP = MAX_TIME_GAP_H*3600





if __name__=="__main__":
    print "#DETECTS IMAGES CREATED WITH GAPS <=%iH AND GROUPS (GENERATES BASH COMMANDS TO DO SO) THEM TOGETHER" % MAX_TIME_GAP_H

    # path to the directory (relative or absolute)
    dirpath = sys.argv[1] if len(sys.argv) == 2 else r'.'
    print "#DIRECTORY: %s" % dirpath
    entries = (os.path.join(dirpath, fn) for fn in os.listdir(dirpath))


    packages = [[]]
    for path in sorted(entries):
        cdate = get_image_timestamp(path)
        #print cdate, path, dt
        current = len(packages)-1
        if len(packages[current])==0 or abs(packages[current][-1][0]-cdate)<MAX_TIME_GAP:
            packages[current].append( (cdate, path) )
        else:
            packages.append([ (cdate, path) ])


    print "#========================"
    for package in packages:
        tm = datetime.datetime.fromtimestamp(package[0][0]).strftime('%Y-%m-%d')
        dr = os.path.join(dirpath, tm)
        print "mkdir '%s'" % dr
        for ctime, path in package:
            fname = os.path.basename(path)
            dst = os.path.join(dr, fname)
            print "mv '%s' '%s'" % (path, dst)
            #os.rename(path, dst)
    print "#%i GROUPS EXTRACTED" % len(packages)


