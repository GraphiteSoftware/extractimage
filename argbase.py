from optparse import OptionParser
import readbase as rb
import ericbase as eb


class Flags:
    verbose = False
    debug = False
    test = False
    force = False
    config = None
    ubuntu = False
    macos = False
    configsettings = {}


class MyArgs:
    def __init__(self, use):
        self.usagemsg = use

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
        Flags.config = options.config
        if Flags.config is not None:
            cf = rb.ReadJson('.', '.', Flags.config)
            cf.readinput()
            Flags.configsettings = cf.data
        else:
            eb.printerror("Missing required configuration file (--config)")
