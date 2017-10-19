import json
import magic
from optparse import OptionParser
import ericbase as eb
import os.path
import fnmatch
import re
import subprocess
import sys, os, errno

# define global variables
# options as globals
verbose = False
debug = False
test = False
all = False
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
    global verbose, debug, test, root, images, output_dict, all
    verbose, debug, test, root, images, data, link, all = processargs()
    if debug:
        print(DEBUG, "\nVerbose: {}\nDebug: {}\nTest: {}\nAll: {}".format(verbose, debug, test, all))
    if test:
        print(WARNING, "Running in Test Mode")
    rw = ReadWrite(root, images, data, link)
    d = rw.readinput()
    if debug:
        print(DEBUG, str(rw))
    modelstoprocess = len(d)
    for idx, line in enumerate(d):
        if verbose:
            print(VERBOSE, "Processing model {} of {}".format(idx + 1, modelstoprocess))
        model = d[line]['name']
        for i in d[line]['images']:
            file_name = extractgroup(re.search(r"http:\/\/.*\/(.*)", i['image']))
            pf = ProcessImage(rw.root_path, rw.image_path, rw.extractpath, file_name, model, i['region'], i['channel'], all)
            pf.processfile()
        if test:
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
    def __init__(self, root: str, imgdir: str, extractdir: str, filename: str, model: str, region: str, channel: str, all: bool):
        self.file = os.path.join(root, imgdir, filename)
        self.extractpath = os.path.join(root, extractdir)
        self.model = model
        self.region = region
        self.channel = channel
        self.processall = all
        self.sysdatname = 'system.new.dat'
        self.sysimgname = 'system.img'

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
            if verbose:
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
            d = self.model.replace(' ', '') + self.region.replace(' ', '').title() + self.channel.replace(' ', '')+version
        return os.path.join(self.extractpath, d)

    def buildzipcommand(self, d: str) -> list:
        return ['unzip', self.file, '-d', d]

    def processfile(self):
        """processing the downloaded zip/tar file"""
        global verbose, debug, test, sysdatname, sysimgname
        if self.checkfile():
            if debug:
                dl_message = "Found and processing: " + self.model + ", " + self.region + ", " + \
                             self.channel + " File: [" + self.file + "]"
                print(DEBUG, dl_message)

            file_type = magic.from_file(self.file)
            if debug:
                print(DEBUG, "\t[{}] is type [{}]".format(self.file, file_type))
            if file_type[:4] == 'gzip':
                # tgz file - we don't do those yet (only one in the file)
                if verbose:
                    print(VERBOSE, "File is Tar GZ format. SKIPPING:", self.file)

            if file_type[-5:] == '(JAR)':
                # zip file - use unzip
                dirname = self.makedirname()
                if verbose:
                    print("Processing:", self.file, "(" + file_type + ") as ZIP into [" + dirname + "]")
                if os.path.isdir(dirname):
                    # directory exists, probably extracted already, skip to find system.new.dat
                    if verbose:
                        print(VERBOSE, "Extraction directory [" + dirname + "] for", self.file, "already exists. SKIPPING")
                else:
                    unzipcmd = self.buildzipcommand(dirname)
                    subprocess.run(unzipcmd)

                # now we either have an existing directory with the image file or we have just unzipped the image file
                sysimgpath = os.path.join(dirname, self.sysdatname)
                if os.path.isfile(sysimgpath):
                    if verbose:
                        print(VERBOSE, "Found", self.sysdatname, "in", dirname)
                             
                else:
                    # something is wrong
                    print(ERROR, "Could not find", sysimgpath)
                # TODO search for the system.new.dat in each of the controlled directories
                # TODO extract and mount the image
                # TODO get the build.props file from the image
                # TODO unmount and do the next one

        return 0


class ReadWrite:
    def __init__(self, rootpath: str, imagepath: str, datapath: str, infile: str):
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
            self.input_json = 'linklist.json'
        else:
            self.input_json = infile
        self.extractpath = 'extracted_images'

        # check that the path is valid and exists
        if not os.path.exists(os.path.join(self.root_path, self.image_path)):
            eb.printerror(
                "Image directory does not exist: [path: " + os.path.join(self.root_path,
                                                                         self.image_path) + "]")
        if not os.path.exists(os.path.join(self.root_path, self.url_list_path, self.input_json)):
            eb.printerror(
                "Link file does not exist or is not mounted: [path: " + os.path.join(self.root_path,
                                                                                    self.url_list_path,
                                                                                    self.input_json) + "]")

    def __str__(self) -> str:
        return "Input path is: " + os.path.join(self.root_path, self.image_path, )

    def readinput(self):
        """read a file"""
        global verbose, debug, test
        json_file = os.path.join(self.root_path, self.url_list_path, self.input_json)
        json_fh = open(json_file, "r")
        dtdata = json.load(json_fh)
        json_fh.close()
        if debug:
            print(DEBUG, "Got json file")
        return dtdata

    def writeoutput(self, idout: dict):
        """write the build props to the json file"""
        global verbose, debug, test
        if debug:
            print("{}{}".format(DEBUG, idout))
        json_file = os.path.join(self.root_path, 'props.json')
        json_fh = open(json_file, "w")
        json.dump(idout, json_fh)
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
    parser.add_option("-a", "--all", dest="all", action="store_true", default=False,
                      help="Extract all images. Default is only Stable")
    parser.add_option("-r", "--root", dest="rootpath", default=None,
                      help="Root path to use for files and images", metavar="ROOTPATH")
    parser.add_option("-f", "--data", dest="datapath", default=None,
                      help="Path to use for files", metavar="DATAPATH")
    parser.add_option("-i", "--images", dest="imagepath", default=None,
                      help="Path to use for images", metavar="IMAGEPATH")
    parser.add_option("-l", "--links", dest="linkfile", default=None,
                      help="JSON file with image URL data", metavar="LINKFILE")
    options, args = parser.parse_args()

    # required options checks
    if options.debug:
        options.verbose = True
    return options.verbose, options.debug, options.test, options.rootpath, options.imagepath, options.datapath, \
           options.linkfile, options.all


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
