import json
import magic
from optparse import OptionParser
import ericbase as eb
import os.path
import fnmatch
import re
import subprocess
import sys
import os
import errno

# define global variables
# options as globals
DEBUG = '[DEBUG]'
VERBOSE = '[STATUS]'
WARNING = '[WARNING]'
ERROR = '[ERROR]'
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
    do = MyArgs()
    do.processargs()
    if Flags.test:
        print(VERBOSE, "Running in Test Mode")
    if Flags.debug:
        print(DEBUG,
              "Flags are:\n\tVerbose: {}\n\tDebug: {}\n\tTest: {}\n\tConfig File: {}\n\tConfig Settings: {}".format(
                  Flags.verbose, Flags.debug, Flags.test, Flags.config, Flags.configsettings))
    rw = ReadJson(Flags.configsettings['root'], Flags.configsettings['data'], Flags.configsettings['links'])
    rw.readinput()
    modelstoprocess = len(rw.data)
    for idx, line in enumerate(rw.data):
        if Flags.verbose:
            print(VERBOSE, "Processing model {} of {}".format(idx + 1, modelstoprocess))
        model = rw.data[line]['name']
        for i in rw.data[line]['images']:
            file_name = extractgroup(re.search(r"http://.*/(.*)", i['image']))
            pf = ProcessImage(Flags.configsettings['root'], Flags.configsettings['image'],
                              Flags.configsettings['extractimages'], file_name, model, i['region'], i['channel'],
                              False)
            pf.processfile()
        if Flags.test:
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
    def __init__(self, root: str, imgdir: str, extractdir: str, filename: str, model: str, region: str, channel: str,
                 all: bool):
        self.file = os.path.join(root, imgdir, filename)
        self.extractpath = os.path.join(root, extractdir)
        self.mountpath = os.path.join(root, 'tmp')
        self.propspath = os.path.join(root, 'extracted_props')
        self.model = model
        self.region = region
        self.channel = channel
        self.processall = all
        self.sysdatname = 'system.new.dat'
        self.transferlistname = 'system.transfer.list'
        self.sysimgname = 'system.img'
        self.buildpropname = 'build.prop'

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
            if Flags.verbose:
                dl_message = "Could not find file: [" + self.file + "]" + self.model + ", " + self.region + ", " + \
                             self.channel
                print(WARNING, dl_message)
        return False

    def makedirname(self) -> str:
        version = extractgroup(re.search(patternversion, self.file))
        d = ''
        if version is None:
            d = self.model.replace(' ', '') + self.region.replace(' ', '').title() + self.channel.replace(' ', '')
        else:
            d = self.model.replace(' ', '') + self.region.replace(' ', '').title() + self.channel.replace(' ',
                                                                                                          '') + version
        return d

    def buildcommand(self, type: str, src: str, dest: str) -> list:
        cmd = []
        if type == 'unzip':
            cmd = ['unzip', src, '-d', dest]
        elif type == 'mount':
            cmd = ['ext4fuse', src, dest]
        elif type == 'unmount':
            cmd = ['umount', dest]
        elif type == 'copy':
            cmd = ['cp', src, dest]
        print("COMMAND is:", cmd)
        return cmd

    def processfile(self):
        """processing the downloaded zip/tar file"""
        if self.checkfile():
            if Flags.debug:
                dl_message = "Found and processing: " + self.model + ", " + self.region + ", " + \
                             self.channel + " File: [" + self.file + "]"
                print(DEBUG, dl_message)

            file_type = magic.from_file(self.file)
            if Flags.debug:
                print(DEBUG, "\t[{}] is type [{}]".format(self.file, file_type))
            if file_type[:4] == 'gzip':
                # tgz file - we don't do those yet (only one in the file)
                if Flags.verbose:
                    print(VERBOSE, "File is Tar GZ format. SKIPPING:", self.file)

            if file_type[-5:] == '(JAR)':
                # zip file - use unzip
                dirname = os.path.join(self.extractpath, self.makedirname())
                if Flags.verbose:
                    print("Processing:", self.file, "(" + file_type + ") as ZIP into [" + dirname + "]")
                if os.path.isdir(dirname):
                    # directory exists, probably extracted already, skip to find system.new.dat
                    if Flags.verbose:
                        print(VERBOSE, "Extraction directory [" + dirname + "] for", self.file,
                              "already exists. SKIPPING")
                else:
                    subprocess.run(self.buildcommand('unzip', self.file, dirname))

                # now we either have an existing directory with the image file or we have just unzipped the image file
                sysdatpath = os.path.join(dirname, self.sysdatname)
                transferlistpath = os.path.join(dirname, self.transferlistname)
                outputpath = os.path.join(dirname, self.sysimgname)
                if not os.path.isfile(outputpath):
                    # system image does not exist - extract it
                    if os.path.isfile(sysdatpath):
                        if Flags.verbose:
                            print(VERBOSE, "Found", self.sysdatname, "in", dirname)
                        # check that we have the transfer list
                        if os.path.isfile(transferlistpath):
                            # all good
                            simg = SDat2Img(transferlistpath, sysdatpath, outputpath)
                            simg.sdat2img_main()
                        else:
                            # something is wrong
                            print(ERROR, "Could not find", transferlistpath)
                            return 1
                    else:
                        # something is wrong
                        print(ERROR, "Could not find", sysdatpath)
                        return 2
                else:
                    # system img already exists - process it
                    if Flags.verbose:
                        print(VERBOSE, "Found an existing", outputpath, "looking for", self.buildpropname,
                              "in that file")
                # now we have a known image file
                subprocess.run(self.buildcommand('mount', outputpath, self.mountpath))
                buildpropspath = os.path.join(self.mountpath, self.buildpropname)
                bpoutputname = self.makedirname() + '.' + self.buildpropname
                bpoutputpath = os.path.join(self.propspath, bpoutputname)
                if os.path.isfile(buildpropspath):
                    # found the build props file
                    subprocess.run(self.buildcommand('copy', buildpropspath, bpoutputpath))
                    if Flags.verbose:
                        print(VERBOSE, "Found and copied", buildpropspath, "to", bpoutputpath)
                else:
                    print(ERROR, "Did not find", buildpropspath)
                # unmount the image
                subprocess.run(self.buildcommand('unmount', '', self.mountpath))
        return 0


class ReadJson:
    def __init__(self, rootpath: str, datapath: str, infile: str):
        if rootpath is None:
            self.root_path = '.'
        else:
            self.root_path = rootpath
        if infile is None:
            self.json = 'linklist.json'
        else:
            self.json = infile
        if datapath is None:
            self.data_path = '.'
        else:
            self.data_path = datapath
        self.data = {}

    def __str__(self) -> str:
        return "Input file is: " + os.path.join(self.root_path, self.data_path, self.json, )

    def readinput(self):
        """read a file"""
        json_file = os.path.join(self.root_path, self.data_path, self.json)
        try:
            json_fh = open(json_file, "r")
        except IOError as err:
            print(ERROR, "Failed to open input file", json_file)
            print(ERROR, err.errno, err.filename, err.strerror)
            sys.exit(1)
        self.data = json.load(json_fh)
        json_fh.close()
        if Flags.debug:
            print(DEBUG, "Got json input file", json_file)


class WriteJson:
    def __init__(self, rootpath: str, datapath: str, outfile: str):
        if rootpath is None:
            self.root_path = '.'
        else:
            self.root_path = rootpath
        if outfile is None:
            self.json = 'output.json'
        else:
            self.json = outfile
        if datapath is None:
            self.data_path = '.'
        else:
            self.data_path = datapath
        self.data = {}

    def __str__(self) -> str:
        return "Output file is: " + os.path.join(self.root_path, self.data_path, self.json, )

    def writeoutput(self):
        """write the build props to the json file"""
        if Flags.debug:
            print(DEBUG, self.data)
        json_file = os.path.join(self.root_path, self.data_path, self.json)
        try:
            json_fh = open(json_file, "w")
        except IOError as err:
            print(ERROR, "Failed to open output file", json_file)
            print(ERROR, err.errno, err.filename, err.strerror)
            sys.exit(1)
        json.dump(self.data, json_fh, indent=4)
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
        self.usagemsg = "This program looks for data or Android sparse images, extract the image to a raw, " \
                        "mountable format and then mounts the image to a known directory"

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

        options, args = parser.parse_args()
        # required options checks
        if options.debug:
            options.verbose = True
        Flags.verbose = options.verbose
        Flags.debug = options.debug
        Flags.test = options.test
        Flags.config = options.config
        if Flags.config is not None:
            cf = ReadJson('.', '.', Flags.config)
            cf.readinput()
            Flags.configsettings = cf.data
        else:
            eb.printerror("Missing required configuration file (--config)")


class SDat2Img:
    def __init__(self, transfer: str, datafile: str, outputfile: str):
        self.__version__ = '1.0'
        self.TRANSFER_LIST_FILE = transfer
        self.NEW_DATA_FILE = datafile
        self.OUTPUT_IMAGE_FILE = outputfile
        self.BLOCK_SIZE = 4096

    def rangeset(self, src):
        src_set = src.split(',')
        num_set = [int(item) for item in src_set]
        if len(num_set) != num_set[0] + 1:
            print(ERROR, 'Error on parsing following data to rangeset:\n%s' % src)
            sys.exit(1)

        return tuple([(num_set[i], num_set[i + 1]) for i in range(1, len(num_set), 2)])

    def parse_transfer_list_file(self, path):
        trans_list = open(self.TRANSFER_LIST_FILE, 'r')

        # First line in transfer list is the version number
        version = int(trans_list.readline())

        # Second line in transfer list is the total number of blocks we expect to write
        new_blocks = int(trans_list.readline())

        if version >= 2:
            # Third line is how many stash entries are needed simultaneously
            trans_list.readline()
            # Fourth line is the maximum number of blocks that will be stashed simultaneously
            trans_list.readline()

        # Subsequent lines are all individual transfer commands
        commands = []
        for line in trans_list:
            line = line.split(' ')
            cmd = line[0]
            if cmd in ['erase', 'new', 'zero']:
                commands.append([cmd, self.rangeset(line[1])])
            else:
                # Skip lines starting with numbers, they are not commands anyway
                if not cmd[0].isdigit():
                    print('Command "%s" is not valid.' % cmd)
                    trans_list.close()
                    sys.exit(1)

        trans_list.close()
        return version, new_blocks, commands

    def sdat2img_main(self):
        version, new_blocks, commands = self.parse_transfer_list_file(self.TRANSFER_LIST_FILE)

        if version == 1:
            print('Android Lollipop 5.0 detected!\n')
        elif version == 2:
            print('Android Lollipop 5.1 detected!\n')
        elif version == 3:
            print('Android Marshmallow 6.x detected!\n')
        elif version == 4:
            print('Android Nougat 7.x / Oreo 8.x detected!\n')
        else:
            print('Unknown Android version!\n')

        # Don't clobber existing files to avoid accidental data loss
        try:
            output_img = open(self.OUTPUT_IMAGE_FILE, 'wb')
        except IOError as e:
            if e.errno == errno.EEXIST:
                print('Error: the output file "{}" already exists'.format(e.filename))
                print('Remove it, rename it, or choose a different file name.')
                sys.exit(e.errno)
            else:
                raise

        new_data_file = open(self.NEW_DATA_FILE, 'rb')
        all_block_sets = [i for command in commands for i in command[1]]
        max_file_size = max(pair[1] for pair in all_block_sets) * self.BLOCK_SIZE

        for command in commands:
            if command[0] == 'new':
                for block in command[1]:
                    begin = block[0]
                    end = block[1]
                    block_count = end - begin
                    print('Copying {} blocks into position {}...'.format(block_count, begin))

                    # Position output file
                    output_img.seek(begin * self.BLOCK_SIZE)

                    # Copy one block at a time
                    while (block_count > 0):
                        output_img.write(new_data_file.read(self.BLOCK_SIZE))
                        block_count -= 1
            else:
                print('Skipping command %s...' % command[0])

        # Make file larger if necessary
        if (output_img.tell() < max_file_size):
            output_img.truncate(max_file_size)

        output_img.close()
        new_data_file.close()
        print('Done! Output image: %s' % os.path.realpath(output_img.name))


if __name__ == '__main__':
    main()
