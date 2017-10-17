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
    verbose, debug, test, root, data, outputfile = processargs()
    rw = ReadWrite(root, data, outputfile)
    model_dict = {}
    for line in rw.readinput():
        model_dict[line['name']] = processline(line['pid'], line['name'])
    rw.writeoutput(model_dict)


class ReadWrite:
    def __init__(self, rootpath: str, datapath: str, outfile: str):
        if rootpath is None:
            self.root_path = '/Volumes/passport'
        else:
            self.root_path = rootpath
        if datapath is None:
            self.url_list_path = 'xiaomi_data'
        else:
            self.url_list_path = datapath
        if outfile is None:
            self.output_json = 'modellist.json'
        else:
            self.output_json = outfile

    def __str__(self) -> str:
        return "Output file is: " + os.path.join(self.root_path,
                                                self.url_list_path,
                                                self.output_json)

    def writeoutput(self, idout: dict):
        """write the model list dictionary to the json file"""
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
                            temp_d = {'image': child.get('href'), 'channel': channel, 'region': processing}
                            ld['images'].append(temp_d)
            ld = walker(child, ld)
    return ld


def processline(pid: str, n: str):
    """process the line by reading the html and extracting the information"""
    global verbose, debug, test
    url = "http://en.miui.com/download-" + pid + ".html"
    if verbose:
        print(VERBOSE + "Name: {} -> {}".format(n, url))
    line_dict = dict(url=url, name=n, images=[])

    http = httplib2.Http()
    status, response = http.request(url)

    soup = BeautifulSoup(response, 'html.parser')

    line_dict = walker(soup, line_dict)
    if debug:
        print(line_dict)
    return line_dict


def processargs():
    """process arguments and options"""
    usagemsg = "This program reads the Xiaomi dowloads page and get the list of models and the URLs. " \
               "The data is then written to a json file."

    parser = OptionParser(usagemsg)
    parser.add_option("-v", "--verbose", dest="verbose", action="store_true", default=False,
                      help="Print out helpful information during processing")
    parser.add_option("-d", "--debug", dest="debug", action="store_true", default=False,
                      help="Print out debug messages during processing")
    parser.add_option("-t", "--test", dest="test", action="store_true", default=False,
                      help="Use test file instead of full file list")
    parser.add_option("-r", "--root", dest="rootpath", default=None,
                      help="Root path to use for files", metavar="ROOTPATH")
    parser.add_option("-a", "--data", dest="datapath", default=None,
                      help="Path to use for files", metavar="DATAPATH")
    parser.add_option("-o", "--output", dest="outputfile", default=None,
                      help="JSON file to write the download URL data to", metavar="OUTPUTFILE")
    (options, args) = parser.parse_args()

    # required options checks
    if options.debug:
        options.verbose = True
    return options.verbose, options.debug, options.test, options.rootpath, options.datapath, options.outputfile


if __name__ == '__main__':
    main()
