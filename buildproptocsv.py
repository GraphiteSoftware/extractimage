import csv
import os.path
import argbase as arg
import readbase as rb

# define global variables
# options as globals
DEBUG = '[DEBUG]'
VERBOSE = '[STATUS]'
WARNING = '[WARNING]'
ERROR = '[ERROR]'
re_datetime = r"(.*?)=(.*)"
usagemsg = "This program reads a json file that been output from the build props program and produces a csv"\
                " version of the data." \
                "Here is the sequence or processing:\n" \
                "\tgeturls.py\n\tripimage.py\n\tmountimages.py\n\tparsebuildprop.py\n\tbuildproptocsv.py"


def main():
    """main processing loop"""
    do = arg.MyArgs(usagemsg)
    do.processargs()
    msg = arg.MSG()
    msg.TEST("Running in test mode")
    msg.DEBUG(do)

    rd = rb.ReadJson(arg.Flags.configsettings['root'],
                     arg.Flags.configsettings['extractprops'],
                     arg.Flags.configsettings['output'])
    rd.readinput()
    for prop in rd.data:
        addprop(rd.data[prop])
    CSV.file = arg.Flags.configsettings['output'][:-4] + 'csv'
    writecsv()


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


def addprop(p: dict):
    print(p)
    proplist = [p['model'], p['region'], p['channel'], p['version']]
    for k in CSV.propsummary:
        if k in p['props']:
            proplist.append(p['props'][k])
        else:
            proplist.append('')
    CSV.propsoutput.append(proplist)


def writecsv():
    csv_file = os.path.join(arg.Flags.configsettings['root'], CSV.file)
    csv_fh = open(csv_file, "w")
    csvw = csv.writer(csv_fh, quoting=csv.QUOTE_MINIMAL)
    csvw.writerow(CSV.csvheader)
    csvw.writerows(CSV.propsoutput)
    csv_fh.close()


if __name__ == '__main__':
    main()
