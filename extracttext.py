from bs4 import BeautifulSoup
import httplib2
import json
import sys
from optparse import OptionParser
import ericbase as eb
import os.path
import re

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
    image_dict = {}
    inf = ReadJson(Flags.configsettings['root'], Flags.configsettings['data'], Flags.configsettings['links'])
    outf = WriteJson(Flags.configsettings['root'], Flags.configsettings['data'], Flags.configsettings['output'])
    inf.readinput()
    for line in inf.data:
        image_dict[line['name']] = processline(line['pid'], line['name'])
    outf.data = image_dict
    outf.writeoutput()


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
        except IOError:
            print(ERROR, "Failed to open input file", self.json)
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
            self.json = 'imagelist.json'
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
        except IOError:
            print(ERROR, "Failed to open output file", self.json)
            sys.exit(1)
        json.dump(self.data, json_fh)
        json_fh.close()


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


def walker(soup, ld):
    if soup.name is not None:
        for child in soup.children:
            if child.name == 'span':
                # print("<SPAN>: ", child.text, child.attrs)
                if bool(re.search("Global$", child.text)):
                    Global.global_id = 'content_' + child.get('id')
                    if Flags.debug:
                        print("Found Global: " + child.text + " with id of: " + child.get('id'))
                if bool(re.search("China", child.text)):
                    Global.china_id = 'content_' + child.get('id')
                    if Flags.debug:
                        print("Found China: " + child.text + " with id of: " + child.get('id'))

            if child.name == 'div':
                # print("<DIV>: ", child.text, child.attrs)
                if 'id' in child.attrs:
                    if child.get('id') == Global.global_id:
                        Global.processing = "global"
                    if child.get('id') == Global.china_id:
                        Global.processing = "china"
                if 'class' in child.attrs:
                    for c in child.get('class'):
                        if c == 'download_nv':
                            Global.channel = extractgroup(re.search(r"^(.*?) ", child.text))
            if child.name == 'a':
                if 'class' in child.attrs:
                    # print("Found a class of:", child.get('class'))
                    if 'btn_5' in child.get('class'):
                        if Flags.verbose:
                            print("Processing", Global.channel, Global.processing, Global.model_name, "link of:",
                                  child.get('href'))
                            temp_d = {'image': child.get('href'), 'channel': Global.channel,
                                      'region': Global.processing}
                            ld['images'].append(temp_d)
            ld = walker(child, ld)
    return ld


def processline(pid: str, n: str):
    """process the line by reading the html and extracting the information"""
    url = "http://en.miui.com/download-" + pid + ".html"
    if Flags.verbose:
        print(VERBOSE, "Name: {} -> {}".format(n, url))
    line_dict = dict(url=url, name=n, images=[])

    http = httplib2.Http()
    status, response = http.request(url)

    soup = BeautifulSoup(response, 'html.parser')

    line_dict = walker(soup, line_dict)
    if Flags.debug:
        print(line_dict)
    return line_dict


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
        self.usagemsg = "This program reads a json file that has the Xiaomi model list as pulled from the Xiaomi" + \
                        "download site and extracts all of the image URLs from all of the download pages. " + \
                        "The URLS are written to a json file."

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
