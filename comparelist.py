import json
from optparse import OptionParser
import ericbase as eb
import os.path
import re
import sys
import os
import readbase as rb
import argbase as arg

# define global variables
# options as globals
DEBUG = '[DEBUG]'
VERBOSE = '[STATUS]'
ERROR = '[ERROR]'

usagemsg = "This program compares 2 files that contain a URL list from the Xiaomi Download pages."

patternimg = '*.img'
patterndat = '*.dat'
patternversion = r"V(\d*\.\d*\.\d*\.\d*)"


def main():
    """main processing loop"""
    do = arg.MyArgs(usagemsg)
    do.processargs()
    if arg.Flags.test:
        print(VERBOSE, "Running in Test Mode")
    if arg.Flags.debug:
        print(do)

    l1 = rb.ReadJson(arg.Flags.configsettings['root'], arg.Flags.configsettings['link1'])
    l2 = rb.ReadJson(arg.Flags.configsettings['root'], arg.Flags.configsettings['link2'])
    o1 = rb.WriteJson(arg.Flags.configsettings['root'], arg.Flags.configsettings['compareoutput'])
    l1.readinput()
    l2.readinput()
    # check for items from the old file to see if they are in the new file
    for item in l1.data:
        if item in l2.data:
            if l1.data[item] == l2.data[item]:
                if arg.Flags.debug:
                    print("Found", item, "in", arg.Flags.configsettings['link2'], "- it is the same")
                o1.data[item] = l1.data[item]
                o1.data[item]['status'] = 'unchanged'
            else:
                if arg.Flags.debug:
                    print("Found", item, "in", arg.Flags.configsettings['link2'], "- it is changed")
                olditem = str(item) + '-old'
                newitem = str(item) + '-new'
                o1.data[olditem] = l1.data[item]
                o1.data[olditem]['status'] = 'changed'
                o1.data[newitem] = l2.data[item]
                o1.data[newitem]['status'] = 'changed'
                if arg.Flags.verbose:
                    changed = whatchanged(l1.data[item], l2.data[item])
                    print(VERBOSE, "Changed for", item)
                    for changeline in changed:
                        chan, reg = changeline[0].split(":")
                        if changeline[1] == '':
                            print("\t{} {} NEW with version {}".format(chan, reg, changeline[2]))
                        elif changeline[2] == '':
                            print("\t{} {} REMOVED".format(chan, reg))
                        else:
                            print(
                                "\t{} {} CHANGED from version {} to {}".format(chan, reg, changeline[1], changeline[2]))
        else:
            if arg.Flags.debug:
                print("Did NOT find", item, "in", arg.Flags.configsettings['link2'], "- report it as removed")
            o1.data[item] = l1.data[item]
            o1.data[item]['status'] = 'removed'
            if arg.Flags.verbose:
                print(VERBOSE, "Removed", item)
    # check for any that are in the new file, but not in the old file
    for item in l2.data:
        if item not in l1.data:
            if arg.Flags.debug:
                print("Did NOT find", item, "in", arg.Flags.configsettings['link1'], "- this is a new item, report it")
            o1.data[item] = l2.data[item]
            o1.data[item]['status'] = 'added'
            if arg.Flags.verbose:
                print(VERBOSE, "New", item)
    o1.writeoutput()


def whatchanged(old, new) -> list:
    """reports on what has changed between the 2 lists"""
    # first re-structure the image lists into keyed dictionaries by channel and region
    oldbykey = restruct(old['images'])
    newbykey = restruct(new['images'])
    out = []
    patternver = r".com/(.*)/"
    for imgkey in oldbykey:
        oldver = extractgroup(re.search(patternver, oldbykey[imgkey]))
        if imgkey in newbykey:
            newver = extractgroup(re.search(patternver, newbykey[imgkey]))
            if oldbykey[imgkey] != newbykey[imgkey]:
                # image url has changed
                out.append([imgkey, oldver, newver])
        else:
            # deleted entry
            out.append([imgkey, oldver, ''])
    for imgkey in newbykey:
        # check for new items
        if imgkey not in oldbykey:
            # this is new
            newver = extractgroup(re.search(patternver, newbykey[imgkey]))
            out.append([imgkey, '', newver])
    return out


def restruct(imglist: list) -> dict:
    out = {}
    for img in imglist:
        outkey = img['channel'] + ":" + img['region']
        out[outkey] = img['image']
    return out


def extractgroups(match):
    """extract all of the matching groups from the regex object"""
    if match is None:
        return None
    return match.groups()


def extractgroup(match):
    """extract the group (index: 1) from the match object"""
    if match is None:
        return None
    return match.group(1)


if __name__ == '__main__':
    main()
