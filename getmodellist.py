from bs4 import BeautifulSoup
import httplib2
import json
import sys
from optparse import OptionParser
import ericbase as eb
import os.path
import re
import datetime

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
    verbose, debug, test, root, data, outputfile, xmonly = processargs()
    rw = ReadWrite(root, data, outputfile)
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
            if debug:
                print("No match on element", i)
            continue
        else:
            if debug:
                print("Got a match on element:", i)
            phonelist = json.loads(vardata)
            foundmatch = True
            break
    if foundmatch:
        if debug:
            print("\n\n\nPhone list is: \n", phonelist)
    else:
        print("Did not find the phone list")
    if xmonly:
        xmlist = extractxm(phonelist)
        rw.writeoutput(xmlist)
    else:
        rw.writeoutput(phonelist)


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
        d = datetime.datetime.now()
        dString = d.strftime("%Y%m%d")
        if outfile is None:
            self.output_json = 'modellist-' + dString + '.json'
        else:
            self.output_json = outfile

    def __str__(self) -> str:
        return "Output file is: " + os.path.join(self.root_path,
                                                self.url_list_path,
                                                self.output_json)

    def writeoutput(self, idout: list):
        """write the model list to the json file"""
        global verbose, debug, test
        if debug:
            print("{}{}".format(DEBUG, idout))
        json_file = os.path.join(self.root_path, self.url_list_path, self.output_json)
        json_fh = open(json_file, "w")
        json.dump(idout, json_fh)
        json_fh.close()


def extractxm(ph: list) -> list:
    xmlist = []
    for ent in ph:
        if debug:
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
    parser.add_option("-x", "--xiaomi", dest="xiaomionly", action="store_true", default=False,
                      help="Only extract Xiaomi (type=1) entries")
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
    return options.verbose, options.debug, options.test, options.rootpath, options.datapath, options.outputfile, options.xiaomionly


if __name__ == '__main__':
    main()
