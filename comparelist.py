import json
import magic
from optparse import OptionParser
import ericbase as eb
import os.path
import fnmatch
import re
import subprocess
import sys, os, errno
import hashlib

# define global variables
# options as globals
verbose = False
debug = False
test = False
all = False
DEBUG = '[DEBUG]'
VERBOSE = '[STATUS]'
WARNING = '[WARNING]'
ERROR = '[ERROR]'
root, data, images = None, None, None
re_datetime = r"(.*?)=(.*)"
output_dict = {}
patternimg = '*.img'
patterndat = '*.dat'
patternversion = r"V(\d*\.\d*\.\d*\.\d*)"

# app/Spaces*/Spaces*.apk
# priv-app/SpacesManagerService/Spaces*.apk


def main():
    """main processing loop"""
    do = MyArgs()
    do.processargs()
    if Flags.test:
        print(VERBOSE, "Running in Test Mode")
    if Flags.debug:
        print(DEBUG,
              "Flags are:\n\tVerbose: {}\n\tDebug: {}\n\tTest: {}\n\tConfig File: {}\n\tConfig Settings: {}".format(
                  Flags.verbose, Flags.debug, Flags.test, Flags.config, Flags.configsettings))
    l1 = ReadJson(Flags.configsettings['root'], Flags.configsettings['link1'])
    l2 = ReadJson(Flags.configsettings['root'], Flags.configsettings['link2'])
    o1 = WriteJson(Flags.configsettings['root'], Flags.configsettings['output'])
    l1.readinput()
    l2.readinput()
    # check for items from the old file to see if they are in the new file
    for item in l1.data:
        if item in l2.data:
            if l1.data[item] == l2.data[item]:
                print("Found", item, "in", Flags.configsettings['link2'], "- it is the same")
                o1.data[item] = l1.data[item]
                o1.data[item]['status'] = 'unchanged'
            else:
                print("Found", item, "in", Flags.configsettings['link2'], "- it is changed")
                olditem = str(item) + '-old'
                newitem = str(item) + '-new'
                o1.data[olditem] = l1.data[item]
                o1.data[olditem]['status'] = 'changed'
                o1.data[newitem] = l2.data[item]
                o1.data[newitem]['status'] = 'changed'
        else:
            print("Did NOT find", item, "in", Flags.configsettings['link2'], "- report it as removed")
            o1.data[item] = l1.data[item]
            o1.data[item]['status'] = 'removed'
    # check for any that are in the new file, but not in the old file
    for item in l2.data:
        if item not in l1.data:
            print("Did NOT find", item, "in", Flags.configsettings['link1'], "- this is a new item, report it")
            o1.data[item] = l2.data[item]
            o1.data[item]['status'] = 'added'
    o1.writeoutput()


class ReadJson:
    def __init__(self, rootpath: str, infile: str):
        if rootpath is None:
            self.root_path = '.'
        else:
            self.root_path = rootpath
        if infile is None:
            self.json = 'linklist.json'
        else:
            self.json = infile
        self.data = {}

    def __str__(self) -> str:
        return "Input file is: " + os.path.join(self.root_path, self.json, )

    def readinput(self):
        """read a file"""
        json_file = os.path.join(self.root_path, self.json)
        try:
            json_fh = open(json_file, "r")
        except IOError:
            print(ERROR, "Failed to open input file", self.json)
            sys.exit(1)
        self.data = json.load(json_fh)
        json_fh.close()
        if Flags.debug:
            print(DEBUG, "Got json input file", json_file)

class WriteJson:
    def __init__(self, rootpath: str, outfile: str):
        if rootpath is None:
            self.root_path = '.'
        else:
            self.root_path = rootpath
        if outfile is None:
            self.json = 'linklist.json'
        else:
            self.json = outfile
        self.data = {}

    def __str__(self) -> str:
        return "Output file is: " + os.path.join(self.root_path, self.json, )

    def writeoutput(self):
        """write the build props to the json file"""
        if Flags.debug:
            print(DEBUG, self.data)
        json_file = os.path.join(self.root_path, self.json)
        try:
            json_fh = open(json_file, "w")
        except IOError:
            print(ERROR, "Failed to open output file", self.json)
            sys.exit(1)
        json.dump(self.data, json_fh)
        json_fh.close()


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

class Flags:
    verbose = False
    debug = False
    test = False
    config = None
    configsettings = {}


class MyArgs:
    def __init__(self):
        # Specifc to this program

        # Usual suspects
        self.usagemsg = "This program compares 2 files that contain a URL list from the Xiaomi Download pages."

    def processargs(self):
        """process arguments and options"""
        parser = OptionParser(self.usagemsg)
        parser.add_option("-v", "--verbose", dest="verbose", action="store_true", default=False,
                          help="Print out helpful information during processing")
        parser.add_option("-d", "--debug", dest="debug", action="store_true", default=False,
                          help="Print out debug messages during processing")
        parser.add_option("-t", "--test", dest="test", action="store_true", default=False,
                          help="Use test file instead of full file list")
        parser.add_option("-c", "--config", dest="config", default=None,
                          help="Configuration file (JSON)", metavar="CONFIG")

        options, args = parser.parse_args()
        # required options checks
        if options.debug:
            options.verbose = True
        Flags.verbose = options.verbose
        Flags.debug = options.debug
        Flags.test = options.test
        Flags.config = options.config
        if Flags.config is not None:
            json_fh = open(Flags.config, "r")
            Flags.configsettings = json.load(json_fh)
            json_fh.close()
        else:
            eb.printerror("Missing required configuration file (--config)")


if __name__ == '__main__':
    main()
