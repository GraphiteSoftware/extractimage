import argbase as arg

usagemsg = "Test Application"
VERBOSE = '[STATUS]'
DEBUG = '[DEBUG]'

do = arg.MyArgs(usagemsg)
do.processargs()
if arg.Flags.test:
    print(VERBOSE, "Running in Test Mode")
if arg.Flags.debug:
    print(do)