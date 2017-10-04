from bs4 import BeautifulSoup
import httplib2
import json
import sys
import argparse
import ericbase as eb
import os.path

# define global variables
# options as globals
verbose = False
debug = False
test = False
DEBUG = '[DEBUG] '
VERBOSE = '[STATUS] '

htmltouse = '''
<div class="phone_hd ">
    <span>Xiaomi Mi 6</span>
    <span id="t_480" class="tab">Mi 6 Global</span><span id="t_481" class="tab">Mi 6 China</span>
</div>
<div class="content" id="content_t_480">
    <div class="block">
        <div class="appl">
            <div class="tbn">
                <h2>Stable ROM</h2>
                <ul>
                    <li class="current"><span class="index"></span><a href="javascript:;">Full ROM pack</a></li>
                    <li><span class="index"></span><a href="javascript:;">Older versions</a></li>
                </ul>
            </div>
        </div>
        <div class="rom_list_div">
            <div class="rom_list" style="display:block;">
                <div class="download_nv">Stable ROM<span>></span>Full ROM pack</div>
                <div class="stable div_margin">
                    <div class="btn_5" style="background:none;position:relative;">
                        <a class="btn_5" style="margin-top: 0"
                           href="http://bigota.d.miui.com/V8.5.1.0.NCAMIEG/miui_MI6Global_V8.5.1.0.NCAMIEG_7648f20aab_7.1.zip"></a>
                    </div>
                    <a class="btn_6" href="http://en.miui.com/a-232.html"></a>
                    <div class="supports">
                        <p>Author: MIUI Official Team<span class="space"></span>Version: V8.5.1.0.NCAMIEG (MIUI8)
                            <span class="space"></span>Size: 1.5G</p>


                        <p>Download MIUI Forum app to get the latest updates <a
                                href="http://api.en.miui.com/url/MIUIForum1.1.0" target="_blank" class="flush_tool">Download
                            now</a></p>

                    </div>
                </div>
            </div>
            <div class="rom_list" style="display: none;">
                <div class="download_nv">Stable ROM<span>></span>Older versions<span class="space"></span>Author: MIUI
                    Official Team
                </div>
                <ul class="version">
                    <li class="li_2">
                        <span class="span_version">Version: V8.2.2.0.NCAMIEC</span><span class="span_size"> 1.5G </span><span
                            class="span_md5">MD5: 7f3f8ad7c8646ee5ce596ca51556c7c0</span><span class="span_log"><a
                            target="_blank" href="http://en.miui.com/thread-649169-1-1.html">Changelog</a></span><span
                            class="span_download"><a
                            href="http://bigota.d.miui.com/V8.2.2.0.NCAMIEC/miui_MI6Global_V8.2.2.0.NCAMIEC_7f3f8ad7c8_7.1.zip"
                            onmouseover="showMenu({'ctrlid':this.id, 'pos':'!'})"
                            id="rom_7f3f8ad7c8646ee5ce596ca51556c7c0" target="_blank"></a></span>
                    </li>
                </ul>
            </div>
        </div>
    </div>
    <div style="clear:both;"></div>
    <div class="block">
        <div class="appl">
            <div class="tbn">
                <h2>Developer ROM</h2>
                <ul>
                    <li class="current"><span class="index"></span><a href="javascript:;">Full ROM pack</a></li>
                    <li><span class="index"></span><a href="javascript:;">Incremental ROM pack</a></li>
                    <li><span class="index"></span><a href="javascript:;">Older versions</a></li>
                </ul>
            </div>
        </div>
        <div class="rom_list_div">
            <div class="rom_list" style="display:block;">
                <div class="download_nv">Developer ROM<span>></span>Full ROM pack</div>
                <div class="stable div_margin">
                    <div class="btn_5" style="background:none;position:relative;">
                        <a class="btn_5" style="margin-top: 0"
                           href="http://bigota.d.miui.com/7.9.22/miui_MI6Global_7.9.22_431a70c634_7.1.zip"></a>
                    </div>
                    <a class="btn_6" href="http://en.miui.com/a-232.html"></a>
                    <div class="supports">
                        <p>Author: MIUI Official Team<span class="space"></span>Version: 7.9.22 (MIUI9)
                            <span class="space"></span>Size: 1.5G</p>


                        <p>Download MIUI Forum app to get the latest updates <a
                                href="http://api.en.miui.com/url/MIUIForum1.1.0" target="_blank" class="flush_tool">Download
                            now</a></p>

                    </div>
                </div>
            </div>
            <div class="rom_list" style="display: none;">
                <div class="download_nv">Developer ROM<span>></span>Incremental ROM pack<span class="space"></span>Author:
                    MIUI Official Team<span class="space"></span>Version: 7.9.22 (MIUI9)
                </div>
                <ul class="version">
                    <li class="li_2">
                        <span class="span_version">Upgrade from MIUI7.9.7</span><span class="span_size">224M</span><span
                            class="span_md5">MD5: d088bd5dcdf766584a2a4b612c8e6599</span><span class="span_log"><a
                            target="_blank" href="forum.php">Changelog</a></span> <span class="span_download"><a
                            href="http://bigota.d.miui.com/7.9.22/miui-blockota-sagit_global-7.9.7-7.9.22-d088bd5dcd-7.1.zip"
                            onmouseover="showMenu({'ctrlid':this.id, 'pos':'!'})"
                            id="rom_d088bd5dcdf766584a2a4b612c8e6599" target="_blank"></a></span>
                    </li>
                    <li class="li_2">
                        <span class="span_version">Upgrade from MIUI7.9.21</span><span
                            class="span_size">143M</span><span
                            class="span_md5">MD5: e8b03e457e0a58db9cdbfa4a72c6c47d</span><span class="span_log"><a
                            target="_blank" href="forum.php">Changelog</a></span> <span class="span_download"><a
                            href="http://bigota.d.miui.com/7.9.22/miui-blockota-sagit_global-7.9.21-7.9.22-e8b03e457e-7.1.zip"
                            onmouseover="showMenu({'ctrlid':this.id, 'pos':'!'})"
                            id="rom_e8b03e457e0a58db9cdbfa4a72c6c47d" target="_blank"></a></span>
                    </li>
                    <li class="li_2">
                        <span class="span_version">Upgrade from MIUI7.9.20</span><span
                            class="span_size">187M</span><span
                            class="span_md5">MD5: 3ddb555093ca67d9f74987ab05bd84ed</span><span class="span_log"><a
                            target="_blank" href="forum.php">Changelog</a></span> <span class="span_download"><a
                            href="http://bigota.d.miui.com/7.9.22/miui-blockota-sagit_global-7.9.20-7.9.22-3ddb555093-7.1.zip"
                            onmouseover="showMenu({'ctrlid':this.id, 'pos':'!'})"
                            id="rom_3ddb555093ca67d9f74987ab05bd84ed" target="_blank"></a></span>
                    </li>
                    <li class="li_2">
                        <span class="span_version">Upgrade from MIUI7.9.19</span><span
                            class="span_size">152M</span><span
                            class="span_md5">MD5: b5a50a035aabd3417273d42e7aaa7a1f</span><span class="span_log"><a
                            target="_blank" href="forum.php">Changelog</a></span> <span class="span_download"><a
                            href="http://bigota.d.miui.com/7.9.22/miui-blockota-sagit_global-7.9.19-7.9.22-b5a50a035a-7.1.zip"
                            onmouseover="showMenu({'ctrlid':this.id, 'pos':'!'})"
                            id="rom_b5a50a035aabd3417273d42e7aaa7a1f" target="_blank"></a></span>
                    </li>
                    <li class="li_2">
                        <span class="span_version">Upgrade from MIUI7.9.18</span><span
                            class="span_size">167M</span><span
                            class="span_md5">MD5: 223d9e7665d5e0801860ad515c271d9d</span><span class="span_log"><a
                            target="_blank" href="forum.php">Changelog</a></span> <span class="span_download"><a
                            href="http://bigota.d.miui.com/7.9.22/miui-blockota-sagit_global-7.9.18-7.9.22-223d9e7665-7.1.zip"
                            onmouseover="showMenu({'ctrlid':this.id, 'pos':'!'})"
                            id="rom_223d9e7665d5e0801860ad515c271d9d" target="_blank"></a></span>
                    </li>
                </ul>
            </div>
            <div class="rom_list" style="display: none;">
                <div class="download_nv">Developer ROM<span>></span>Older versions<span class="space"></span>Author:
                    MIUI Official Team
                </div>
                <ul class="version">
                    <li class="li_2">
                        <span class="span_version">Version: 7.9.7</span><span class="span_size"> 1.5G </span><span
                            class="span_md5">MD5: 1aefcd07ec440c23fab61e784796c226</span><span class="span_log"><a
                            target="_blank" href="forum.php">Changelog</a></span><span class="span_download"><a
                            href="http://bigota.d.miui.com/7.9.7/miui_MI6Global_7.9.7_1aefcd07ec_7.1.zip"
                            onmouseover="showMenu({'ctrlid':this.id, 'pos':'!'})"
                            id="rom_1aefcd07ec440c23fab61e784796c226" target="_blank"></a></span>
                    </li>
                    <li class="li_2">
                        <span class="span_version">Version: 7.8.31</span><span class="span_size"> 1.5G </span><span
                            class="span_md5">MD5: 8de7f993ed9e688e26057ba1607806ba</span><span class="span_log"><a
                            target="_blank" href="forum.php">Changelog</a></span><span class="span_download"><a
                            href="http://bigota.d.miui.com/7.8.31/miui_MI6Global_7.8.31_8de7f993ed_7.1.zip"
                            onmouseover="showMenu({'ctrlid':this.id, 'pos':'!'})"
                            id="rom_8de7f993ed9e688e26057ba1607806ba" target="_blank"></a></span>
                    </li>
                    <li class="li_2">
                        <span class="span_version">Version: 7.8.24</span><span class="span_size"> 1.5G </span><span
                            class="span_md5">MD5: 52ee82c8641d49eed8fb7132ea34238d</span><span class="span_log"><a
                            target="_blank" href="forum.php">Changelog</a></span><span class="span_download"><a
                            href="http://bigota.d.miui.com/7.8.24/miui_MI6Global_7.8.24_52ee82c864_7.1.zip"
                            onmouseover="showMenu({'ctrlid':this.id, 'pos':'!'})"
                            id="rom_52ee82c8641d49eed8fb7132ea34238d" target="_blank"></a></span>
                    </li>
                    <li class="li_2">
                        <span class="span_version">Version: 7.8.18</span><span class="span_size"> 1.5G </span><span
                            class="span_md5">MD5: 11939d27fcbff5cdf970b7b02edd08a3</span><span class="span_log"><a
                            target="_blank" href="forum.php">Changelog</a></span><span class="span_download"><a
                            href="http://bigota.d.miui.com/7.8.18/miui_MI6Global_7.8.18_11939d27fc_7.1.zip"
                            onmouseover="showMenu({'ctrlid':this.id, 'pos':'!'})"
                            id="rom_11939d27fcbff5cdf970b7b02edd08a3" target="_blank"></a></span>
                    </li>
                    <li class="li_2">
                        <span class="span_version">Version: 7.8.10</span><span class="span_size"> 1.5G </span><span
                            class="span_md5">MD5: 024aaf1afd4a248ec9d60f7159186390</span><span class="span_log"><a
                            target="_blank" href="forum.php">Changelog</a></span><span class="span_download"><a
                            href="http://bigota.d.miui.com/7.8.10/miui_MI6Global_7.8.10_024aaf1afd_7.1.zip"
                            onmouseover="showMenu({'ctrlid':this.id, 'pos':'!'})"
                            id="rom_024aaf1afd4a248ec9d60f7159186390" target="_blank"></a></span>
                    </li>
                </ul>
            </div>
        </div>
    </div>
    <div style="clear:both;"></div>

</div>
'''
htmltousesmall = '''
<div class="phone_hd ">
    <span>Xiaomi Mi 6</span>
    <span id="t_480" class="tab">Mi 6 Global</span><span id="t_481" class="tab">Mi 6 China</span>
</div>
<div class="content" id="content_t_480">
    <div class="block">
        <div class="appl">
            <div class="tbn">
                <h2>Stable ROM</h2>
                <ul>
                    <li class="current"><span class="index"></span><a href="javascript:;">Full ROM pack</a></li>
                    <li><span class="index"></span><a href="javascript:;">Older versions</a></li>
                </ul>
            </div>
        </div>
        <div class="rom_list_div">
            <div class="rom_list" style="display:block;">
                <div class="download_nv">Stable ROM<span>></span>Full ROM pack</div>
                <div class="stable div_margin">
                    <div class="btn_5" style="background:none;position:relative;">
                        <a class="btn_5" style="margin-top: 0"
                           href="http://bigota.d.miui.com/V8.5.1.0.NCAMIEG/miui_MI6Global_V8.5.1.0.NCAMIEG_7648f20aab_7.1.zip"></a>
                    </div>
                    <a class="btn_6" href="http://en.miui.com/a-232.html"></a>
                    <div class="supports">
                        <p>Author: MIUI Official Team<span class="space"></span>Version: V8.5.1.0.NCAMIEG (MIUI8)
                            <span class="space"></span>Size: 1.5G</p>


                        <p>Download MIUI Forum app to get the latest updates <a
                                href="http://api.en.miui.com/url/MIUIForum1.1.0" target="_blank" class="flush_tool">Download
                            now</a></p>

                    </div>
                </div>
            </div>
            <div class="rom_list" style="display: none;">
                <div class="download_nv">Stable ROM<span>></span>Older versions<span class="space"></span>Author: MIUI
                    Official Team
                </div>
                <ul class="version">
                    <li class="li_2">
                        <span class="span_version">Version: V8.2.2.0.NCAMIEC</span><span class="span_size"> 1.5G </span><span
                            class="span_md5">MD5: 7f3f8ad7c8646ee5ce596ca51556c7c0</span><span class="span_log"><a
                            target="_blank" href="http://en.miui.com/thread-649169-1-1.html">Changelog</a></span><span
                            class="span_download"><a
                            href="http://bigota.d.miui.com/V8.2.2.0.NCAMIEC/miui_MI6Global_V8.2.2.0.NCAMIEC_7f3f8ad7c8_7.1.zip"
                            onmouseover="showMenu({'ctrlid':this.id, 'pos':'!'})"
                            id="rom_7f3f8ad7c8646ee5ce596ca51556c7c0" target="_blank"></a></span>
                    </li>
                </ul>
            </div>
        </div>
    </div>
    <div style="clear:both;"></div>

</div>
'''

def main():
    """main processing loop"""
    image_dict = {}
    global verbose, debug, test
    verbose, debug, test, root, data, images, inputfile, outputfile = processargs()
    rw = ReadWrite(root, data, images, inputfile, outputfile)
    for line in rw.readinput():
        image_dict[line['name']] = processline(line['pid'], line['name'])
        break
    # rw.writeoutput(image_dict)


class ReadWrite:
    def __init__(self, rootpath: str, datapath: str, imagepath: str, infile: str, outfile: str):
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
            self.input_json = 'xmlist.json'
        else:
            self.input_json = infile
        if outfile is None:
            self.output_json = 'urllist.json'
        else:
            self.output_json = outfile

    def __str__(self) -> str:
        return "Input file is: " + os.path.join(self.root_path,
                                                self.url_list_path,
                                                self.output_json) + \
               "\nOutput file is: " + os.path.join(self.root_path,
                                                   self.url_list_path,
                                                   self.output_json)

    def readinput(self):
        """read model and download url from json file"""
        global verbose, debug, test
        json_file = os.path.join(self.root_path, self.url_list_path, self.input_json)
        json_fh = open(json_file, "r")
        data = json.load(json_fh)
        json_fh.close()
        if debug:
            print(DEBUG + "Got json file")
        return data

    def writeoutput(self, idout: dict):
        """write the image list dictionary to the json file"""
        global verbose, debug, test
        if debug:
            print("{}{}".format(DEBUG, idout))
        json_file = os.path.join(self.root_path, self.url_list_path, self.output_json)
        json_fh = open(json_file, "w")
        json.dump(idout, json_fh)
        json_fh.close()


def walker(soup):
    if soup.name is not None:
        for child in soup.children:
            # process node
            print(str(child.name) + ":" + str(type(child)))
            if type(child) == soup.tag:
                print("\tThis is a tag")
            walker(child)



def processline(pid: str, n: str):
    global verbose, debug, test
    c = 0
    url = "http://en.miui.com/download-" + pid + ".html"
    if verbose:
        print(VERBOSE + "Name: {} -> {}".format(n, url))
    line_dict = dict(url=url, images=[])

    http = httplib2.Http()
    status, response = http.request(url)

    soup = BeautifulSoup(htmltousesmall, 'html.parser')
    walker(soup)

    sys.exit(0)

    links = []

    for link in soup.find_all('a'):
        c += 1
        for child in soup.recursiveChildGenerator():
            print("Full line is [{}]".format(child))
            name = getattr(child, "name", None)
            print("Name is [{}].".format(name))
            # attrid = getattr(child, "id", None)
            # if name is not None:
            #     print(name, attrid)
            # elif not child.isspace():  # leaf node, don't print spaces
            #     print(child)
        # if verbose:
        #     eb.displaycounter(["Processing link: "], [c])

    #     if link.get('class') == ['btn_5']:
    #         links.append(link.get('href'))
    #         if debug:
    #             print(DEBUG + link.get('href'))
    # # for t in soup.find_all(string=n):
    # #     print(VERBOSE + "Found span element with name of " + n + " and object of " + t)
    # line_dict['images'] = links
    return line_dict


def processargs():
    """process arguments and options"""
    usagemsg = "This program reads a json file that has the Xiaomi model list as pulled from the Xiaomi download site\
     and extracts all of the image URLs from all of the download pages. The URLS are written to a json file."

    parser = argparse.ArgumentParser(description=usagemsg)
    parser.add_argument("-v", "--verbose", dest="verbose", action="store_true", default=False,
                      help="Print out helpful information during processing")
    parser.add_argument("-d", "--debug", dest="debug", action="store_true", default=False,
                      help="Print out debug messages during processing")
    parser.add_argument("-t", "--test", dest="test", action="store_true", default=False,
                      help="Use test file instead of full file list")
    parser.add_argument("-r", "--root", dest="rootpath", default=None,
                      help="Root path to use for files and images", metavar="ROOTPATH")
    parser.add_argument("-a", "--data", dest="datapath", default=None,
                      help="Path to use for files", metavar="DATAPATH")
    parser.add_argument("-i", "--images", dest="imagepath", default=None,
                      help="Path to use for images", metavar="IMAGEPATH")
    parser.add_argument("-m", "--model", dest="modelfile", default=None,
                      help="JSON file with model and URL data", metavar="MODELFILE")
    parser.add_argument("-o", "--output", dest="outputfile", default=None,
                      help="JSON file to write the download URL data to", metavar="OUTPUTFILE")
    options = parser.parse_args()

    # required options checks
    if options.debug:
        options.verbose = True
    if options.verbose:
        print(
            "Options set as:\nVerbose: {}\nDebug: {}\nTest: {}\nRoot: {}\nData: {}\nImage: {}\nInput: {}\nOutput: {}".format(
                options.verbose, options.debug, options.test, options.rootpath, options.datapath, options.imagepath,
                options.modelfile, options.outputfile))
    return options.verbose, \
           options.debug, \
           options.test, \
           options.rootpath, \
           options.datapath, \
           options.imagepath, \
           options.modelfile, \
           options.outputfile


if __name__ == '__main__':
    main()
