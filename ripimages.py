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
verbose = False
debug = False
test = False
DEBUG = '[DEBUG] '
VERBOSE = '[STATUS] '


def main():
    """main processing loop"""
    global verbose, debug, test
    image_dict = {}
    verbose, debug, test, root, data, images, inputfile, outputfile = processargs()
    rw = ReadWrite(root, data, images, inputfile, outputfile)
    for line in rw.readinput():
        image_dict[line['name']] = processline(line['pid'], line['name'])
    rw.writeoutput(image_dict)


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
            self.input_json = 'xmlist.json'
        else:
            self.input_json = infile
        if outfile is None:
            self.output_json = 'urllist.json'
        else:
            self.output_json = outfile

    def __str__(self) -> str:
        return "Input file is: " + os.path.join(self.root_path,
                                                self.url_list_path,
                                                self.output_json) + \
               "\nOutput file is: " + os.path.join(self.root_path,
                                                   self.url_list_path,
                                                   self.output_json)

    def readinput(self):
        """read model and download url from json file"""
        global verbose, debug, test
        json_file = os.path.join(self.root_path, self.url_list_path, self.input_json)
        json_fh = open(json_file, "r")
        data = json.load(json_fh)
        json_fh.close()
        if debug:
            print(DEBUG + "Got json file")
        return data

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


def walker(soup, ld):
    global global_id, china_id, processing, model_name, channel
    global verbose, debug, test
    if soup.name is not None:
        for child in soup.children:
            if child.name == 'span':
                # print("<SPAN>: ", child.text, child.attrs)
                if bool(re.search("Global$", child.text)):
                    global_id = 'content_' + child.get('id')
                    if debug:
                        print("Found Global: " + child.text + " with id of: " + child.get('id'))
                if bool(re.search("China", child.text)):
                    china_id = 'content_' + child.get('id')
                    if debug:
                        print("Found China: " + child.text + " with id of: " + child.get('id'))

            if child.name == 'div':
                # print("<DIV>: ", child.text, child.attrs)
                if 'id' in child.attrs:
                    if child.get('id') == global_id:
                        processing = "global"
                    if child.get('id') == china_id:
                        processing = "china"
                if 'class' in child.attrs:
                    for c in child.get('class'):
                        if c == 'download_nv':
                            channel = extractgroup(re.search(r"^(.*?) ", child.text))
            if child.name == 'a':
               if 'class' in child.attrs:
                    # print("Found a class of:", child.get('class'))
                    if 'btn_5' in child.get('class'):
                        if verbose:
                            print("Processing", channel, processing, model_name, "link of:", child.get('href'))
                            ld[child.get('href')] = {'channel': channel, 'region': processing}
            ld = walker(child, ld)
    return ld



def processline(pid: str, n: str):
    """process the line by reading the html and extracting the information"""
    global verbose, debug, test
    url = "http://en.miui.com/download-" + pid + ".html"
    if verbose:
        print(VERBOSE + "Name: {} -> {}".format(n, url))
    line_dict = dict(url=url, name=n)

    http = httplib2.Http()
    status, response = http.request(url)

    soup = BeautifulSoup(response, 'html.parser')

    line_dict = walker(soup, line_dict)
    if debug:
        print(line_dict)
    return line_dict


def processargs():
    """process arguments and options"""
    usagemsg = "This program reads a json file that has the Xiaomi model list as pulled from the Xiaomi download site\n\
     and extracts all of the image URLs from all of the download pages. The URLS are written to a json file. \n\
    Usage is:\n\n\
    python3 " + sys.argv[0] + " [options] where:"

    parser = OptionParser(usagemsg)
    parser.add_option("-v", "--verbose", dest="verbose", action="store_true", default=False,
                      help="Print out helpful information during processing")
    parser.add_option("-d", "--debug", dest="debug", action="store_true", default=False,
                      help="Print out debug messages during processing")
    parser.add_option("-t", "--test", dest="test", action="store_true", default=False,
                      help="Use test file instead of full file list")
    parser.add_option("-r", "--root", dest="rootpath", default=None,
                      help="Root path to use for files and images", metavar="ROOTPATH")
    parser.add_option("-a", "--data", dest="datapath", default=None,
                      help="Path to use for files", metavar="DATAPATH")
    parser.add_option("-i", "--images", dest="imagepath", default=None,
                      help="Path to use for images", metavar="IMAGEPATH")
    parser.add_option("-m", "--model", dest="modelfile", default=None,
                      help="JSON file with model and URL data", metavar="MODELFILE")
    parser.add_option("-o", "--output", dest="outputfile", default=None,
                      help="JSON file to write the download URL data to", metavar="OUTPUTFILE")
    (options, args) = parser.parse_args()

    # required options checks
    if options.debug:
        options.verbose = True
    return options.verbose, \
           options.debug, \
           options.test, \
           options.rootpath, \
           options.datapath, \
           options.imagepath, \
           options.modelfile, \
           options.outputfile


if __name__ == '__main__':
    main()
