import sys
import os.path
import re
from urllib.request import urlretrieve
import time
import argbase as arg
import readbase as rb

# define global variables
# options as globals
DEBUG = '[DEBUG]'
VERBOSE = '[STATUS]'
ERROR = '[ERROR]'
usagemsg = "This program downloads the image files as listed in the link file" \
           "Here is the sequence of processing:\n" \
                "\tgeturls.py\n\tripimage.py\n\tmountimages.py\n\tparsebuildprop.py\n\tbuildproptocsv.py"


def main():
    """main processing loop"""
    do = arg.MyArgs(usagemsg)
    do.processargs()
    msg = arg.MSG()
    msg.TEST("Running in test mode")
    msg.DEBUG(do)

    rd = rb.ReadJson(arg.Flags.configsettings['root'], arg.Flags.configsettings['data'],
                     arg.Flags.configsettings['links'])

    rd.readinput()
    d = rd.data
    for line in d:
        model = d[line]['name']
        for i in d[line]['images']:
            file_name = extractgroup(re.search(r"http:\/\/.*\/(.*)", i['image']))
            msg.DEBUG("{}, {}, {}".format(arg.Flags.configsettings['root'],
                                          arg.Flags.configsettings['extractedimages'],
                                          file_name))
            file_path = os.path.join(arg.Flags.configsettings['root'], arg.Flags.configsettings['extractimages'],
                                     file_name)
            if os.path.isfile(file_path) and not arg.Flags.force:
                msg.VERBOSE("File exists. Not downloading. [{}]".format(file_path))
            else:
                msg.VERBOSE("[STATUS] Downloading: {} ({}, {}, {}) to [{}]".format(i['image'],
                                                                                   model,
                                                                                   i['region'],
                                                                                   i['channel'],
                                                                                   file_path))
                start = time.time()
                urlretrieve(i['image'], file_path, reporthook)
                end = time.time()
                print("This download took {0:.2f} seconds".format(end - start))
            d[line]['file'] = file_path


def reporthook(blocknum, blocksize, totalsize):
    readsofar = blocknum * blocksize
    if totalsize > 0:
        percent = readsofar * 1e2 / totalsize
        s = "\r%5.1f%% %*d / %d" % (
            percent, len(str(totalsize)), readsofar, totalsize)
        sys.stderr.write(s)
        if readsofar >= totalsize:  # near the end
            sys.stderr.write("\n")
    else:  # total size is unknown
        sys.stderr.write("read %d\n" % (readsofar,))


class Global:
    global_id = ''
    china_id = ''
    processing = ''
    model_name = ''
    channel = ''


def extractgroup(match):
    """extract the group (index: 1) from the match object"""
    if match is None:
        return None
    return match.group(1)


if __name__ == '__main__':
    main()
