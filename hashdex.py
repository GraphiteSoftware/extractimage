import hashlib
import os
import ericbase as eb
import fnmatch
from optparse import OptionParser
import json

# define global variables
# options as globals
DEBUG = '[DEBUG]'
VERBOSE = '[STATUS]'
WARNING = '[WARNING]'
ERROR = '[ERROR]'


def getfilelist(filepath) -> list:
    patternprop = r"classes.dex"
    if not os.path.isdir(filepath):
        eb.printerror("APK directory does not exist or is not mounted: " + filepath)
    else:
        shpfiles = []
        for dirpath, subdirs, files in os.walk(filepath):
            for x in files:
                if x == patternprop:
                    shpfiles.append(os.path.join(dirpath, x))
    return shpfiles


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
        self.usagemsg = "This program starts from a base root directory and finds the classes.dex files in \
        subdirectories, produces an MD5 hash of the classes.dex and then write the hash and the index fields \
        to a json file"

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


class ReadWrite:
    def __init__(self, rootpath: str, outfile: str):
        if rootpath is None:
            self.root_path = '~/code/graphite-software/spaces-core-apk'
        else:
            self.root_path = rootpath
        if outfile is None:
            self.output_json = 'checksums.json'
        else:
            self.output_json = outfile
        # check that the path is valid and exists
        if not os.path.exists(os.path.join(self.root_path)):
            eb.printerror(
                "APK directory does not exist or is not mounted: [path: " + os.path.join(self.root_path) + "]")

    def __str__(self) -> str:
        return "APK directory is: " + os.path.join(self.root_path)

    def readinput(self, propfile):
        """read build prop file"""
        bp_file = os.path.join(self.root_path, propfile)
        bp_fh = open(bp_file, "r")
        dtdata = bp_fh.readlines()
        bp_fh.close()
        if Flags.debug:
            print(DEBUG, "Got classes.dex file")
        return dtdata

    def writeoutput(self, idout: dict):
        """write the build props to the json file"""
        if Flags.debug:
            print("{}{}".format(DEBUG, idout))
        json_file = os.path.join(self.root_path, self.output_json)
        json_fh = open(json_file, "w")
        json.dump(idout, json_fh)
        json_fh.close()


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
    output_dict = {}
    rw = ReadWrite(Flags.configsettings['root'], Flags.configsettings['output'])

    files = getfilelist(Flags.configsettings['root'])
    print(files)
    for f in files:
        print(os.path.split(f))

    hasher = hashlib.md5()
    with open('urllist.json', 'rb') as afile:
        buf = afile.read()
        hasher.update(buf)
    print(hasher.hexdigest())


if __name__ == '__main__':
    main()
