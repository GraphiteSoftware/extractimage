import json
import sys
from optparse import OptionParser
import ericbase as eb
import os.path
import re
from urllib.request import urlretrieve

# define global variables
# options as globals
verbose = False
debug = False
test = False
DEBUG = '[DEBUG] '
VERBOSE = '[STATUS] '
root, data, images, outputfile = None, None, None, None
re_datetime = r"(.*?)=(.*)"
output_dict = {}


def main():
    """main processing loop"""
    global verbose, debug, test, root, images, outputfile, output_dict
    verbose, debug, test, root, images, outputfile = processargs()
    if test:
        print(VERBOSE, "Running in Test Mode")
    rw = ReadWrite(root, images, outputfile)
    d = rw.readinput()
    if debug:
        print(str(rw))
        print(verbose, debug, test, rw.root_path, rw.image_path, rw.output_json)
    for line in d:
        if debug:
            print(line.rstrip())
        if line[0] == '#':
            if debug:
                print("Comment line")
            else:
                continue
        else:
            prop = extractgroups(re.search(re_datetime, line))
            if prop is not None:
                if debug:
                    print("Found {} = {}".format(prop[0], prop[1]))
                output_dict[prop[0]] = prop[1]
    rw.writeoutput(output_dict)


class ReadWrite:
    def __init__(self, rootpath: str, imagepath: str, outfile: str):
        if rootpath is None:
            self.root_path = '/Volumes/passport/test'
        else:
            self.root_path = rootpath
        if imagepath is None:
            self.image_path = 'sys'
        else:
            self.image_path = imagepath
        if outfile is None:
            self.output_json = 'imageprop.json'
        else:
            self.output_json = outfile
        self.buildprop_file = 'build.prop'
        # check that the path is valid and exists
        if not os.path.exists(os.path.join(self.root_path, self.image_path)):
            eb.printerror(
                "Image directory does not exist or is not mounted: [path: " + os.path.join(self.root_path,
                                                                                           self.image_path) + "]")
        if not os.path.exists(os.path.join(self.root_path, self.image_path, self.buildprop_file)):
            eb.printerror(
                "Build properties file does not exist: [path: " + os.path.join(self.root_path, self.image_path,
                                                                               self.buildprop_file) + "]")

    def __str__(self) -> str:
        return "Input file is: " + os.path.join(self.root_path,
                                                self.image_path,
                                                self.buildprop_file) + \
               "\nOutput file is: " + os.path.join(self.root_path,
                                                   self.output_json +
                                                   "\nImage path is: " + os.path.join(self.root_path,
                                                                                      self.image_path))

    def readinput(self):
        """read build prop file"""
        global verbose, debug, test
        bp_file = os.path.join(self.root_path, self.image_path, self.buildprop_file)
        bp_fh = open(bp_file, "r")
        dtdata = bp_fh.readlines()
        bp_fh.close()
        if debug:
            print(DEBUG + "Got build props file")
        return dtdata

    def writeoutput(self, idout: dict):
        """write the build props to the json file"""
        global verbose, debug, test
        if debug:
            print("{}{}".format(DEBUG, idout))
        json_file = os.path.join(self.root_path, self.output_json)
        json_fh = open(json_file, "w")
        json.dump(idout, json_fh)
        json_fh.close()

def extractgroups(match):
    """extract all of the matching groups from the regex object"""
    if match is None:
        return None
    return match.groups()



def processargs():
    """process arguments and options"""
    usagemsg = "This program reads a json file that been output from the extract program and has a list of\
     image urls and associated data. Then the images are downloaded, unzipped, and ripped to extract the build\
      properties and write those to a JSON file"

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
    parser.add_option("-o", "--output", dest="outputfile", default=None,
                      help="JSON file to write the build.props data to", metavar="OUTPUTFILE")
    options, args = parser.parse_args()

    # required options checks
    if options.debug:
        options.verbose = True
    return options.verbose, options.debug, options.test, options.rootpath, options.imagepath, options.outputfile


if __name__ == '__main__':
    main()
