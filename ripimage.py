import json
import sys
from optparse import OptionParser
import ericbase as eb
import os.path
import subprocess
import re
from urllib.request import urlretrieve
import time

# define global variables
# options as globals
DEBUG = '[DEBUG]'
VERBOSE = '[STATUS]'
ERROR = '[ERROR]'


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
    rd = ReadJson(Flags.configsettings['root'], Flags.configsettings['data'], Flags.configsettings['links'])

    rd.readinput()
    d = rd.data
    # TODO add in a check for how many dowloads and a count as the downloads progress - total completed
    for line in d:
        model = d[line]['name']
        for i in d[line]['images']:
            file_name = extractgroup(re.search(r"http:\/\/.*\/(.*)", i['image']))
            if Flags.debug:
                print(Flags.configsettings['root'], Flags.configsettings['extractedimages'], file_name)
            file_path = os.path.join(Flags.configsettings['root'], Flags.configsettings['extractimages'], file_name)
            if os.path.isfile(file_path) and not Flags.force:
                if Flags.verbose:
                    print("[STATUS] File exists. Not downloading. [{}]".format(file_path))
            else:
                if Flags.verbose:
                    dl_message = "[STATUS] Downloading: " + i['image'] + " (" + model + ", " + i['region'] + ", " + i[
                        'channel'] + ") to [" + file_path + "]"
                    print(dl_message)
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


class Flags:
    verbose = False
    debug = False
    test = False
    config = None
    force = False
    configsettings = {}


class MyArgs:
    def __init__(self):
        # Specifc to this program

        # Usual suspects
        self.usagemsg = "This program reads a json file that been output from the extract program and has a list of\
         image urls and associated data. Then the images are downloaded, unzipped, and ripped to extract the build\
          properties and write those to a JSON file" \
                   "Here is the sequence or processing:\n" \
                   "\tgeturls.py\n\tripimage.py\n\tmountimages.py\n\tparsebuildprop.py"

    def processargs(self):
        """process arguments and options"""
        parser = OptionParser(self.usagemsg)
        parser.add_option("-v", "--verbose", dest="verbose", action="store_true", default=False,
                          help="Print out helpful information during processing")
        parser.add_option("-d", "--debug", dest="debug", action="store_true", default=False,
                          help="Print out debug messages during processing")
        parser.add_option("-t", "--test", dest="test", action="store_true", default=False,
                          help="Use test file instead of full file list")
        parser.add_option("-f", "--force", dest="force", action="store_true", default=False,
                          help="Force download even if file exists")
        parser.add_option("-c", "--config", dest="config", default=None,
                          help="Configuration file (JSON)", metavar="CONFIG")

        options, args = parser.parse_args()
        # required options checks
        if options.debug:
            options.verbose = True
        Flags.verbose = options.verbose
        Flags.debug = options.debug
        Flags.test = options.test
        Flags.force = options.force
        Flags.config = options.config
        if Flags.config is not None:
            cf = ReadJson('.', '.', Flags.config)
            cf.readinput()
            Flags.configsettings = cf.data
        else:
            eb.printerror("Missing required configuration file (--config)")


class ReadJson:
    def __init__(self, rootpath: str, datapath: str, infile: str):
        if rootpath is None:
            self.root_path = '.'
        else:
            self.root_path = rootpath
        if infile is None:
            self.json = 'linklist.json'
        else:
            self.json = infile
        if datapath is None:
            self.data_path = '.'
        else:
            self.data_path = datapath
        self.data = {}

    def __str__(self) -> str:
        return "Input file is: " + os.path.join(self.root_path, self.data_path, self.json, )

    def readinput(self):
        """read a file"""
        json_file = os.path.join(self.root_path, self.data_path, self.json)
        try:
            json_fh = open(json_file, "r")
        except IOError as err:
            print(ERROR, "Failed to open input file", json_file)
            print(ERROR, err.errno, err.filename, err.strerror)
            sys.exit(1)
        self.data = json.load(json_fh)
        json_fh.close()
        if Flags.debug:
            print(DEBUG, "Got json input file", json_file)


class WriteJson:
    def __init__(self, rootpath: str, datapath: str, outfile: str):
        if rootpath is None:
            self.root_path = '.'
        else:
            self.root_path = rootpath
        if outfile is None:
            self.json = 'output.json'
        else:
            self.json = outfile
        if datapath is None:
            self.data_path = '.'
        else:
            self.data_path = datapath
        self.data = {}

    def __str__(self) -> str:
        return "Output file is: " + os.path.join(self.root_path, self.data_path, self.json, )

    def writeoutput(self):
        """write the build props to the json file"""
        if Flags.debug:
            print(DEBUG, self.data)
        json_file = os.path.join(self.root_path, self.data_path, self.json)
        try:
            json_fh = open(json_file, "w")
        except IOError as err:
            print(ERROR, "Failed to open output file", json_file)
            print(ERROR, err.errno, err.filename, err.strerror)
            sys.exit(1)
        json.dump(self.data, json_fh, indent=4)
        json_fh.close()


if __name__ == '__main__':
    main()
