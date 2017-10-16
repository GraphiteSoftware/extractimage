import json
import magic
from optparse import OptionParser
import ericbase as eb
import os.path
import fnmatch

# define global variables
# options as globals
verbose = False
debug = False
test = False
DEBUG = '[DEBUG] '
VERBOSE = '[STATUS] '
root, data, images = None, None, None
re_datetime = r"(.*?)=(.*)"
output_dict = {}
patternimg = '*.img'
patterndat = '*.dat'


# app/Spaces*/Spaces*.apk
# priv-app/SpacesManagerService/Spaces*.apk


def main():
    """main processing loop"""
    global verbose, debug, test, root, images, output_dict
    verbose, debug, test, root, images = processargs()
    if debug:
        print("Verbose is {}, Debug is {} and Test is {}". format(verbose, debug, test))
    if test:
        print(VERBOSE, "Running in Test Mode")
    rw = ReadWrite(root, images)
    # d = rw.readinput()
    if debug:
        print(str(rw))
    filelist = getfilelist(os.path.join(rw.root_path, rw.image_path))
    for f in filelist:
        print(f)
        print(magic.from_file(f))


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


def processfile(f: str):
    print("Processing: " + f)
    return 0



class ReadWrite:
    def __init__(self, rootpath: str, imagepath: str):
        if rootpath is None:
            self.root_path = '/Volumes/passport'
        else:
            self.root_path = rootpath
        if imagepath is None:
            self.image_path = 'test'
        else:
            self.image_path = imagepath
        # check that the path is valid and exists
        if not os.path.exists(os.path.join(self.root_path, self.image_path)):
            eb.printerror(
                "Image directory does not exist: [path: " + os.path.join(self.root_path,
                                                                                           self.image_path) + "]")

    def __str__(self) -> str:
        return "Input path is: " + os.path.join(self.root_path, self.image_path,)

    def readinput(self):
        """read build prop file"""
        global verbose, debug, test
        # bp_file = os.path.join(self.root_path, self.image_path, self.buildprop_file)
        # bp_fh = open(bp_file, "r")
        # dtdata = bp_fh.readlines()
        # bp_fh.close()
        if debug:
            print(DEBUG + "Got build props file")
        return 0

    def writeoutput(self, idout: dict):
        """write the build props to the json file"""
        global verbose, debug, test
        # if debug:
        #     print("{}{}".format(DEBUG, idout))
        # json_file = os.path.join(self.root_path, self.output_json)
        # json_fh = open(json_file, "w")
        # json.dump(idout, json_fh)
        # json_fh.close()

def extractgroups(match):
    """extract all of the matching groups from the regex object"""
    if match is None:
        return None
    return match.groups()



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
    parser.add_option("-r", "--root", dest="rootpath", default=None,
                      help="Root path to use for files and images", metavar="ROOTPATH")
    parser.add_option("-i", "--image", dest="imagepath", default=None,
                      help="Path to use for the image", metavar="IMAGEPATH")
    options, args = parser.parse_args()

    # required options checks
    if options.debug:
        options.verbose = True
    return options.verbose, options.debug, options.test, options.rootpath, options.imagepath


if __name__ == '__main__':
    main()
