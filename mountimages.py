import json
import magic
from optparse import OptionParser
import ericbase as eb
import os.path
import fnmatch
import re
import subprocess

# define global variables
# options as globals
verbose = False
debug = False
test = False
all = False
DEBUG = '[DEBUG]'
VERBOSE = '[STATUS]'
WARNING = '[WARNING]'
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
    global verbose, debug, test, root, images, output_dict, all
    verbose, debug, test, root, images, data, link, all = processargs()
    if debug:
        print(DEBUG, "\nVerbose: {}\nDebug: {}\nTest: {}\nAll: {}".format(verbose, debug, test, all))
    if test:
        print(WARNING, "Running in Test Mode")
    rw = ReadWrite(root, images, data, link)
    d = rw.readinput()
    if debug:
        print(DEBUG, str(rw))
    modelstoprocess = len(d)
    for idx, line in enumerate(d):
        if verbose:
            print(VERBOSE, "Processing model {} of {}".format(idx + 1, modelstoprocess))
        model = d[line]['name']
        for i in d[line]['images']:
            file_name = extractgroup(re.search(r"http:\/\/.*\/(.*)", i['image']))
            file_path = os.path.join(rw.root_path, rw.image_path, file_name)
            pf = ProcessImage(file_path, model, i['region'], i['channel'], all)
            pf.processfile()
        if test:
            if idx > 1:
                break


def getfilelist(filepath) -> list:
    fl = []
    for file in os.listdir(filepath):
        # print("Checking: ", file)
        if fnmatch.fnmatch(file, patternimg) or fnmatch.fnmatch(file, patterndat):
            # print("Matches Image")
            fullname = os.path.join(filepath, file)
            if fnmatch.fnmatch(file, '._*'):
                # skip these file
                # print("Skipping")
                continue
            fileinfo = os.stat(fullname)
            if fileinfo.st_size == 0:
                # skip zero byte file
                # print("Skipping")
                continue
            if file == 'boot.img' or file == 'sys.img':
                # skip special images
                continue
            fl.append(os.path.join(filepath, file))
    return fl


class ProcessImage:
    def __init__(self, filepath: str, model: str, region: str, channel: str, all: bool):
        self.file = filepath
        self.model = model
        self.region = region
        self.channel = channel
        self.processall = all

    def __str__(self) -> str:
        return "File: " + self.file + "\nModel: " + self.model + "\nRegion: " + "\nChannel: " + self.channel

    def checkfile(self) -> bool:
        if os.path.isfile(self.file):
            # Process all or only stable
            if self.processall:
                return True
            if self.channel.lower() == 'stable':
                return True
        else:
            if verbose:
                dl_message = "Could not find file: [" + self.file + "]" + self.model + ", " + self.region + ", " + \
                             self.channel
                print(WARNING, dl_message)
        return False

    def makedirname(self) -> str:
        version = extractgroup(re.search(patternversion, self.file))
        if version is None:
            return self.model.replace(' ', '') + self.region.replace(' ', '').title() + self.channel.replace(' ', '')
        else:
            return self.model.replace(' ', '') + self.region.replace(' ', '').title() + self.channel.replace(' ', '')+version

    def buildzipcommand(self, d: str) -> list:
        return ['unzip', self.file, '-d', d]

    def processfile(self):
        """processing the downloaded zip/tar file"""
        global verbose, debug, test
        if self.checkfile():
            if debug:
                dl_message = "Found and processing: " + self.model + ", " + self.region + ", " + \
                             self.channel + " File: [" + self.file + "]"
                print(DEBUG, dl_message)

            file_type = magic.from_file(self.file)
            if debug:
                print(DEBUG, "\t[{}] is type [{}]".format(self.file, file_type))
            if file_type[:4] == 'gzip':
                # tgz file - we don't do those yet (only one in the file)
                if verbose:
                    print(VERBOSE, "File is Tar GZ format. SKIPPING:", self.file)

            if file_type[-5:] == '(JAR)':
                # zip file - use unzip
                dirname = self.makedirname()
                if verbose:
                    print("Processing:", self.file, "(" + file_type + ") as ZIP into [" + dirname + "]")
                if os.path.isfile(dirname):
                    # directory exists, probably extracted already, skip
                    if verbose:
                        print(VERBOSE, "Extraction directory for", self.file, "already exists. SKIPPING")
                else:
                    unzipcmd = self.buildzipcommand(dirname)
                    subprocess.run(unzipcmd)
                    # TODO search for the system.new.dat in each of the controlled directories
                    # TODO extract and mount the image
                    # TODO get the build.props file from the image
                    # TODO unmount and do the next one

        return 0


class ReadWrite:
    def __init__(self, rootpath: str, imagepath: str, datapath: str, infile: str):
        if rootpath is None:
            self.root_path = '/Volumes/passport'
        else:
            self.root_path = rootpath
        if imagepath is None:
            self.image_path = 'xiaomi_images'
        else:
            self.image_path = imagepath
        if datapath is None:
            self.url_list_path = 'xiaomi_data'
        else:
            self.url_list_path = datapath
        if infile is None:
            self.input_json = 'linklist.json'
        else:
            self.input_json = infile

        # check that the path is valid and exists
        if not os.path.exists(os.path.join(self.root_path, self.image_path)):
            eb.printerror(
                "Image directory does not exist: [path: " + os.path.join(self.root_path,
                                                                         self.image_path) + "]")
        if not os.path.exists(os.path.join(self.root_path, self.url_list_path, self.input_json)):
            eb.printerror(
                "Link file does not exist or is not mounted: [path: " + os.path.join(self.root_path,
                                                                                    self.url_list_path,
                                                                                    self.input_json) + "]")

    def __str__(self) -> str:
        return "Input path is: " + os.path.join(self.root_path, self.image_path, )

    def readinput(self):
        """read a file"""
        global verbose, debug, test
        json_file = os.path.join(self.root_path, self.url_list_path, self.input_json)
        json_fh = open(json_file, "r")
        dtdata = json.load(json_fh)
        json_fh.close()
        if debug:
            print(DEBUG, "Got json file")
        return dtdata

    def writeoutput(self, idout: dict):
        """write the build props to the json file"""
        global verbose, debug, test
        if debug:
            print("{}{}".format(DEBUG, idout))
        json_file = os.path.join(self.root_path, 'props.json')
        json_fh = open(json_file, "w")
        json.dump(idout, json_fh)
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


def processargs():
    """process arguments and options"""
    usagemsg = "This program looks for data or Android sparse images, extract the image to a raw, mountable format\
     and then mounts the image to a known directory"

    parser = OptionParser(usagemsg)
    parser.add_option("-v", "--verbose", dest="verbose", action="store_true", default=False,
                      help="Print out helpful information during processing")
    parser.add_option("-d", "--debug", dest="debug", action="store_true", default=False,
                      help="Print out debug messages during processing")
    parser.add_option("-t", "--test", dest="test", action="store_true", default=False,
                      help="Use test file instead of full file list")
    parser.add_option("-a", "--all", dest="all", action="store_true", default=False,
                      help="Extract all images. Default is only Stable")
    parser.add_option("-r", "--root", dest="rootpath", default=None,
                      help="Root path to use for files and images", metavar="ROOTPATH")
    parser.add_option("-f", "--data", dest="datapath", default=None,
                      help="Path to use for files", metavar="DATAPATH")
    parser.add_option("-i", "--images", dest="imagepath", default=None,
                      help="Path to use for images", metavar="IMAGEPATH")
    parser.add_option("-l", "--links", dest="linkfile", default=None,
                      help="JSON file with image URL data", metavar="LINKFILE")
    options, args = parser.parse_args()

    # required options checks
    if options.debug:
        options.verbose = True
    return options.verbose, options.debug, options.test, options.rootpath, options.imagepath, options.datapath, \
           options.linkfile, options.all


if __name__ == '__main__':
    main()
