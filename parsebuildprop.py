import ericbase as eb
import os.path
import re
import fnmatch
import argbase as arg
import readbase as rb

# define global variables
# options as globals
DEBUG = '[DEBUG]'
VERBOSE = '[STATUS]'
WARNING = '[WARNING]'
ERROR = '[ERROR]'
re_datetime = r"(.*?)=(.*)"
usagemsg = "This program reads a json file that been output from the extract program and has a list of\
 image urls and associated data. Then the images are downloaded, unzipped, and ripped to extract the build\
  properties and write those to a JSON file" \
                "Here is the sequence or processing:\n" \
                "\tgeturls.py\n\tripimage.py\n\tmountimages.py\n\tparsebuildprop.py\n\tbuildproptocsv.py"


def main():
    """main processing loop"""
    do = arg.MyArgs(usagemsg)
    do.processargs()
    if arg.Flags.test:
        print(VERBOSE, "Running in Test Mode")
    if arg.Flags.debug:
        print(do)

    output_dict = {}
    rd = rb.ReadJson(arg.Flags.configsettings['root'],
                     arg.Flags.configsettings['extractprops'],
                     '')
    wd = rb.WriteJson(arg.Flags.configsettings['root'],
                      arg.Flags.configsettings['extractprops'],
                      arg.Flags.configsettings['output'])
    listofprops = getfilelist(os.path.join(arg.Flags.configsettings['root'], arg.Flags.configsettings['extractprops']))
    for propfile in listofprops:
        line_dict = {}
        if arg.Flags.debug:
            print(DEBUG, propfile.rstrip())
        rd.json = propfile
        d = rd.readinput()
        head, file = os.path.split(propfile)
        if file != '':
            imgfields = splitfilename(file)
        else:
            if arg.Flags.debug:
                print(WARNING, "bad file name in", propfile)
            imgfields = {"model": '', "region": '', "channel": '', "version": ''}
        for line in d:
            if line[0] == '#':
                if arg.Flags.test:
                    print("Comment line")
                else:
                    continue
            else:
                prop = extractgroups(re.search(re_datetime, line))
                if prop is not None:
                    if arg.Flags.test:
                        print("Found {} = {}".format(prop[0], prop[1]))
                    line_dict[prop[0]] = prop[1]
        imgfields['props'] = line_dict
        output_dict[file] = imgfields
    wd.data = output_dict
    wd.writeoutput()


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


def extractgroups(match):
    """extract all of the matching groups from the regex object"""
    if match is None:
        return None
    return match.groups()


if __name__ == '__main__':
    main()
