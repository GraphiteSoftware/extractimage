from bs4 import BeautifulSoup
import httplib2
import json
from optparse import OptionParser
import ericbase as eb
import os.path
import re
import sys

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
    writefile = WriteJson(Flags.configsettings['root'], Flags.configsettings['output'])
    phonelist = []
    foundmatch = False

    http = httplib2.Http()
    status, response = http.request("http://en.miui.com/download.html")
    soup = BeautifulSoup(response, 'html.parser')

    data = soup.find_all("script")
    for i, d in enumerate(data):
        # print(d.text)
        vardata = extractgroup(re.search(r"var phones =(.*?);", d.text))
        if vardata is None:
            if Flags.debug:
                print("No match on element", i)
            continue
        else:
            if Flags.debug:
                print("Got a match on element:", i)
            phonelist = json.loads(vardata)
            foundmatch = True
            break
    if foundmatch:
        if Flags.debug:
            print("\n\n\nPhone list is: \n", phonelist)
    else:
        print("Did not find the phone list")
    if Flags.configsettings['xmonly']:
        xmlist = extractxm(phonelist)
        writefile.data = xmlist
    else:
        writefile.data = phonelist
    writefile.writeoutput()


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


def extractxm(ph: list) -> list:
    xmlist = []
    for ent in ph:
        if Flags.debug:
            if ent['type'] == "1":
                print("Xiaomi device", ent['name'])
            else:
                print("Got model type", ent['type'], ent['name'])
        if ent['type'] == '1':
            xmlist.append(ent)
    return xmlist


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
        self.usagemsg = "This program reads the Xiaomi dowloads page and get the list of models and the URLs. " \
               "The data is then written to a json file."

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
