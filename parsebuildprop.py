import json
import csv
from optparse import OptionParser
import ericbase as eb
import os.path
import re
import fnmatch

# define global variables
# options as globals
DEBUG = '[DEBUG]'
VERBOSE = '[STATUS]'
WARNING = '[WARNING]'
ERROR = '[ERROR]'
re_datetime = r"(.*?)=(.*)"


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
    output_dict = {}
    rw = ReadWrite(Flags.configsettings['root'], Flags.configsettings['extractprops'], Flags.configsettings['output'])
    listofprops = getfilelist(os.path.join(Flags.configsettings['root'], Flags.configsettings['extractprops']))
    for propfile in listofprops:
        line_dict = {}
        if Flags.debug:
            print(DEBUG, propfile.rstrip())
        d = rw.readinput(propfile)
        head, file = os.path.split(propfile)
        if file != '':
            imgfields = splitfilename(file)
        else:
            if Flags.debug:
                print(WARNING, "bad file name in", propfile)
            imgfields = {"model": '', "region": '', "channel": '', "version": ''}
        for line in d:
            if line[0] == '#':
                if Flags.test:
                    print("Comment line")
                else:
                    continue
            else:
                prop = extractgroups(re.search(re_datetime, line))
                if prop is not None:
                    if Flags.test:
                        print("Found {} = {}".format(prop[0], prop[1]))
                    line_dict[prop[0]] = prop[1]
        if CSV.outputcsv:
            addprop(imgfields, line_dict)
        imgfields['props'] = line_dict
        output_dict[file] = imgfields
    rw.writeoutput(output_dict)
    if CSV.outputcsv:
        writecsv()


def splitfilename(f: str) -> dict:
    fieldpattern = r"(.*?)(China|Global)(Stable|Developer)(.*?).build.prop"
    fields = {'model': extractgroups(re.search(fieldpattern, f))[0],
              'region': extractgroups(re.search(fieldpattern, f))[1],
              'channel': extractgroups(re.search(fieldpattern, f))[2],
              'version': extractgroups(re.search(fieldpattern, f))[3]}
    return fields

    # app/Spaces*/Spaces*.apk
    # priv-app/SpacesManagerService/Spaces*.apk


def getfilelist(filepath) -> list:
    fl = []
    patternprop = r"*build.prop"
    if not os.path.isdir(filepath):
        eb.printerror("Build Props directory does not exist or is not mounted: " + filepath)
    else:
        for file in os.listdir(filepath):
            # print("Checking: ", file)
            if fnmatch.fnmatch(file, patternprop):
                # print("Matches property file")
                fl.append(os.path.join(filepath, file))
    return fl


class ReadWrite:
    def __init__(self, rootpath: str, proppath: str, outfile: str):
        if rootpath is None:
            self.root_path = '/Volumes/passport'
        else:
            self.root_path = rootpath
        if proppath is None:
            self.image_path = 'extracted_props'
        else:
            self.image_path = proppath
        if outfile is None:
            self.output_json = 'imageprop.json'
        else:
            self.output_json = outfile
        # check that the path is valid and exists
        if not os.path.exists(os.path.join(self.root_path, self.image_path)):
            eb.printerror(
                "Build Prop directory does not exist or is not mounted: [path: " + os.path.join(self.root_path,
                                                                                                self.image_path) + "]")

    def __str__(self) -> str:
        return "Build Prop directory is: " + os.path.join(self.root_path, self.image_path)

    def readinput(self, propfile):
        """read build prop file"""
        bp_file = os.path.join(self.root_path, self.image_path, propfile)
        bp_fh = open(bp_file, "r")
        dtdata = bp_fh.readlines()
        bp_fh.close()
        if Flags.debug:
            print(DEBUG, "Got build props file")
        return dtdata

    def writeoutput(self, idout: dict):
        """write the build props to the json file"""
        if Flags.debug:
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


class CSV:
    file = None
    outputcsv = False
    propsummary = [
        "ro.build.version.incremental",
        "ro.build.version.sdk",
        "ro.build.version.release",
        "ro.build.version.security_patch",
        "ro.build.date",
        "ro.miui.version.code_time",
        "ro.miui.ui.version.code",
        "ro.miui.ui.version.name",
        "ro.ss.version",
        "ro.ss.nohidden"
    ]
    csvheader = [
        "model",
        "region",
        "channel",
        "version",
        "ro.build.version.incremental",
        "ro.build.version.sdk",
        "ro.build.version.release",
        "ro.build.version.security_patch",
        "ro.build.date",
        "ro.miui.version.code_time",
        "ro.miui.ui.version.code",
        "ro.miui.ui.version.name",
        "ro.ss.version",
        "ro.ss.nohidden"
    ]
    propsoutput = []


def addprop(b: dict, p: dict):
    proplist = [b['model'], b['region'], b['channel'], b['version']]
    for k in p:
        if k in CSV.propsummary:
            proplist.append(p[k])
    CSV.propsoutput.append(proplist)


def writecsv():
    if Flags.debug:
        print(DEBUG, CSV.propsoutput)
    csv_file = os.path.join(Flags.configsettings['root'], CSV.file)
    csv_fh = open(csv_file, "w")
    csvw = csv.writer(csv_fh, quoting=csv.QUOTE_MINIMAL)
    csvw.writerow(CSV.csvheader)
    csvw.writerows(CSV.propsoutput)
    csv_fh.close()


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
        self.usagemsg = "This program reads a json file that been output from the extract program and has a list of\
         image urls and associated data. Then the images are downloaded, unzipped, and ripped to extract the build\
          properties and write those to a JSON file"

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
        parser.add_option("-o", "--csv", dest="csv", default=None,
                          help="Output a CSV summary file in addition to the JSON full file", metavar="CSV")

        options, args = parser.parse_args()
        # required options checks
        if options.debug:
            options.verbose = True
        Flags.verbose = options.verbose
        Flags.debug = options.debug
        Flags.test = options.test
        Flags.config = options.config
        if options.csv:
            CSV.file = options.csv
            CSV.outputcsv = True
        if Flags.config is not None:
            json_fh = open(Flags.config, "r")
            Flags.configsettings = json.load(json_fh)
            json_fh.close()
        else:
            eb.printerror("Missing required configuration file (--config)")


if __name__ == '__main__':
    main()
