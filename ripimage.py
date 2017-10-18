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
verbose = False
debug = False
test = False
DEBUG = '[DEBUG] '
VERBOSE = '[STATUS] '
root, data, images, inputfile, outputfile = None, None, None, None, None


def main():
    """main processing loop"""
    global verbose, debug, test, root, data, images, inputfile, outputfile
    verbose, debug, test, root, data, images, inputfile, outputfile, force = processargs()
    if test:
        print(VERBOSE, "Running in Test Mode")
        inputfile = 'urllist_test.json'
        root = '.'
        data = ''
        images = ''
    rw = ReadWrite(root, data, images, inputfile, outputfile)
    if debug:
        print(str(rw))
    d = rw.readinput()
    # TODO add in a check for how many dowloads and a count as the downloads progress - total completed
    for line in d:
        model = d[line]['name']
        for i in d[line]['images']:
            file_name = extractgroup(re.search(r"http:\/\/.*\/(.*)", i['image']))
            if debug:
                print(rw.root_path, rw.image_path, file_name)
            file_path = os.path.join(rw.root_path, rw.image_path, file_name)
            if os.path.isfile(file_path) and not force:
                if verbose:
                    print("[STATUS] File exists. Not downloading. [{}]".format(file_path))
            else:
                if verbose:
                    dl_message = "[STATUS] Downloading: " + i['image'] + " (" + model + ", " + i['region'] + ", " + i[
                        'channel'] + ") to [" + file_path + "]"
                    print(dl_message)
                start = time.time()
                urlretrieve(i['image'], file_path, reporthook)
                end = time.time()
                print("This download took {0:.2f} seconds".format(end - start))
            d[line]['file'] = file_path
    rw.writeoutput(d)


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


class ReadWrite:
    def __init__(self, rootpath: str, datapath: str, imagepath: str, infile: str, outfile: str):
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
            self.input_json = 'urllist.json'
        else:
            self.input_json = infile
        if outfile is None:
            self.output_json = 'urllist_updated.json'
        else:
            self.output_json = outfile
        # check that the path is valid and exists
        if not os.path.exists(os.path.join(self.root_path, self.image_path)):
            eb.printerror(
                "Image directory does not exists or is not mounted: [path: " + os.path.join(self.root_path,
                                                                                            self.image_path) + "]")
        if not os.path.exists(os.path.join(self.root_path, self.url_list_path)):
            eb.printerror(
                "Image directory does not exists or is not mounted: [path: " + os.path.join(self.root_path,
                                                                                            self.url_list_path) + "]")

    def __str__(self) -> str:
        return "Input file is: " + os.path.join(self.root_path,
                                                self.url_list_path,
                                                self.input_json) + \
               "\nOutput file is: " + os.path.join(self.root_path,
                                                   self.url_list_path,
                                                   self.output_json +
                                                   "\nImage path is: " + os.path.join(self.root_path,
                                                                                      self.image_path))

    def readinput(self):
        """read model and download url from json file"""
        global verbose, debug, test
        json_file = os.path.join(self.root_path, self.url_list_path, self.input_json)
        json_fh = open(json_file, "r")
        dtdata = json.load(json_fh)
        json_fh.close()
        if debug:
            print(DEBUG + "Got json file")
        return dtdata

    def writeoutput(self, idout: dict):
        """write the image list dictionary to the json file"""
        global verbose, debug, test
        if debug:
            print("{}{}".format(DEBUG, idout))
        json_file = os.path.join(self.root_path, self.url_list_path, self.output_json)
        json_fh = open(json_file, "w")
        json.dump(idout, json_fh)
        json_fh.close()


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
    parser.add_option("-f", "--force", dest="force", action="store_true", default=False,
                      help="Force overwrite of existing files")
    parser.add_option("-r", "--root", dest="rootpath", default=None,
                      help="Root path to use for files and images", metavar="ROOTPATH")
    parser.add_option("-a", "--data", dest="datapath", default=None,
                      help="Path to use for files", metavar="DATAPATH")
    parser.add_option("-i", "--images", dest="imagepath", default=None,
                      help="Path to use for images", metavar="IMAGEPATH")
    parser.add_option("-m", "--model", dest="modelfile", default=None,
                      help="JSON file with image URL data", metavar="MODELFILE")
    parser.add_option("-o", "--output", dest="outputfile", default=None,
                      help="JSON file to write the download URL data to", metavar="OUTPUTFILE")
    (options, args) = parser.parse_args()

    # required options checks
    if options.debug:
        options.verbose = True
    return options.verbose, \
           options.debug, \
           options.test, \
           options.rootpath, options.datapath, options.imagepath, options.modelfile, options.outputfile, options.force


if __name__ == '__main__':
    main()
