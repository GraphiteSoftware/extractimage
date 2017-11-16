import os.path
import json
import sys

ERROR = '[ERROR]'

class ReadJson:
    def __init__(self, rootpath: str, datapath: str, infile: str):
        if rootpath is None:
            self.root_path = '.'
        else:
            self.root_path = rootpath
        if infile is None:
            self.json = 'input.json'
        else:
            self.json = infile
        if datapath is None:
            self.data_path = '.'
        else:
            self.data_path = datapath
        self.data = {}

    def __str__(self) -> str:
        return json.dumps(self.data, indent=4)

    def __repr__(self):
        return self.data

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


class ReadPlain:
    def __init__(self, rootpath: str, datapath: str, infile: str):
        if rootpath is None:
            self.root_path = '.'
        else:
            self.root_path = rootpath
        if infile is None:
            self.plain = 'input.txt'
        else:
            self.plain = infile
        if datapath is None:
            self.data_path = '.'
        else:
            self.data_path = datapath
        self.data = []

    def __str__(self) -> str:
        return ''

    def __repr__(self):
        return self.data

    def readinput(self):
        """read a file"""
        plain_file = os.path.join(self.root_path, self.data_path, self.plain)
        try:
            plain_fh = open(plain_file, "r")
        except IOError as err:
            print(ERROR, "Failed to open input file", plain_file)
            print(ERROR, err.errno, err.filename, err.strerror)
            sys.exit(1)
        self.data = list(plain_fh)
        plain_fh.close()


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
        return json.dumps(self.data, indent=4)

    def __repr__(self):
        return self.data

    def writeoutput(self):
        """write the build props to the json file"""
        json_file = os.path.join(self.root_path, self.data_path, self.json)
        try:
            json_fh = open(json_file, "w")
        except IOError as err:
            print(ERROR, "Failed to open output file", json_file)
            print(ERROR, err.errno, err.filename, err.strerror)
            sys.exit(1)
        json.dump(self.data, json_fh, indent=4)
        json_fh.close()
