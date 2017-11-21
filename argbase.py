from optparse import OptionParser
import readbase as rb
from sys import platform as _platform
import json
import sys


class Flags:
    verbose = False
    debug = False
    test = False
    force = False
    config = None
    ubuntu = False
    macos = False
    error = False
    configsettings = {}


class MyArgs:
    def __init__(self, use):
        self.usagemsg = use

    def __str__(self):
        argstring = "Program Arguments:"
        argstring = argstring + "\nFlags are:\n\tVerbose: {}\n\tDebug: {}\n\tTest: {}".format(Flags.verbose,
                                                                                 Flags.debug,
                                                                                 Flags.test)
        argstring = argstring +"\n\tForce: {}\n\tUbuntu: {}\n\tMacOS: {}".format(Flags.force,
                                                                                 Flags.ubuntu,
                                                                                 Flags.macos)
        argstring = argstring + "\nConfig file is [{}]".format(Flags.config)
        argstring = argstring + "\nConfig settings are:\n" + json.dumps(Flags.configsettings, indent=4)
        return argstring

    def processargs(self):
        """process arguments and options"""
        parser = OptionParser(self.usagemsg)
        parser.add_option("-v", "--verbose", dest="verbose", action="store_true", default=False,
                          help="Print out helpful information during processing")
        parser.add_option("-d", "--debug", dest="debug", action="store_true", default=False,
                          help="Print out debug messages during processing")
        parser.add_option("-t", "--test", dest="test", action="store_true", default=False,
                          help="Use test file instead of full file list")
        parser.add_option("-f", "--force", dest="force", action="store_true", default=False,
                          help="Force processing")
        parser.add_option("-c", "--config", dest="config", default=None,
                          help="Configuration file (JSON)", metavar="CONFIG")

        options, args = parser.parse_args()
        # required options checks
        if options.debug:
            options.verbose = True
        Flags.verbose = options.verbose
        Flags.debug = options.debug
        Flags.test = options.test
        Flags.force = options.force
        if _platform == "linux" or _platform == "linux2":
            # linux
            Flags.ubuntu = True
        elif _platform == "darwin":
            # MAC OS X
            Flags.macos = True
        else:
            # Windows - will not work
            MSG.ERROR("This program will only run correctly on Linux or Mac OS based systems")

        Flags.config = options.config
        if Flags.config is not None:
            cf = rb.ReadJson('.', '.', Flags.config)
            cf.readinput()
            Flags.configsettings = cf.data
        else:
            MSG.ERROR("Missing required configuration file (--config)")


class MSG:
    def ERROR(self, msg):
        print('[ERROR]', msg)
        sys.exit(2)

    def VERBOSE(self, msg):
        if Flags.verbose:
            print('[STATUS]', msg)

    def DEBUG(self, msg):
        if Flags.debug:
            print('[DEBUG]', msg)

    def TEST(self, msg):
        if Flags.test:
            print('[TEST]', msg)

