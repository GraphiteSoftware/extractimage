from bs4 import BeautifulSoup
import httplib2
import json
import re
import readbase as rb
import argbase as arg

# define global variables
# options as globals
DEBUG = '[DEBUG]'
VERBOSE = '[STATUS]'
ERROR = '[ERROR]'

usagemsg = "This program reads the Xiaomi download site, extracts the list of models and then" \
                "extracts all of the image URLs from all of the download pages. "  \
                "The URLS are written to a json file." \
                "Here is the sequence or processing:\n" \
                "\tgeturls.py\n\tripimage.py\n\tmountimages.py\n\tparsebuildprop.py"


def main():
    """main processing loop"""
    do = arg.MyArgs(usagemsg)
    do.processargs()
    if arg.Flags.test:
        print(VERBOSE, "Running in Test Mode")
    if arg.Flags.debug:
        print(DEBUG,
              "flag are:\n\tVerbose: {}\n\tDebug: {}\n\tTest: {}\n\tConfig File: {}\n\tConfig Settings: {}".format(
                  arg.Flags.verbose, arg.Flags.debug, arg.Flags.test, arg.Flags.config, arg.Flags.configsettings))
    writefile = rb.WriteJson(arg.Flags.configsettings['root'], arg.Flags.configsettings['data'], arg.Flags.configsettings['model'])
    phonelist = []
    foundmatch = False

    http = httplib2.Http()
    status, response = http.request("http://en.miui.com/download.html")
    soup = BeautifulSoup(response, 'html.parser')

    data = soup.find_all("script")
    for i, d in enumerate(data):
        # print(d.text)
        vardata = extractgroup(re.search(r"var phones =(.*?);", d.text))
        if vardata is None:
            if arg.Flags.debug:
                print("No match on element", i)
            continue
        else:
            if arg.Flags.debug:
                print("Got a match on element:", i)
            phonelist = json.loads(vardata)
            foundmatch = True
            break
    if foundmatch:
        if arg.Flags.debug:
            print("\n\n\nPhone list is: \n", phonelist)
    else:
        print("Did not find the phone list")
    if arg.Flags.configsettings['xmonly']:
        xmlist = extractxm(phonelist)
        writefile.data = xmlist
    else:
        writefile.data = phonelist

    # instead of writing the model file - do the extract url processes from extracttext.py
    image_dict = {}
    outf = rb.WriteJson(arg.Flags.configsettings['root'], arg.Flags.configsettings['data'], arg.Flags.configsettings['links'])
    for line in writefile.data:
        image_dict[line['name']] = processline(line['pid'], line['name'])
    outf.data = image_dict
    outf.writeoutput()

    writefile.writeoutput()


class Global:
    global_id = ''
    china_id = ''
    processing = ''
    model_name = ''
    channel = ''


def walker(soup, ld):
    if soup.name is not None:
        for child in soup.children:
            if child.name == 'span':
                # print("<SPAN>: ", child.text, child.attrs)
                if bool(re.search(r"Global$", child.text)):
                    Global.global_id = 'content_' + child.get('id')
                    if arg.Flags.debug:
                        print("Found Global: " + child.text + " with id of: " + child.get('id'))
                if bool(re.search(r"China", child.text)):
                    Global.china_id = 'content_' + child.get('id')
                    if arg.Flags.debug:
                        print("Found China: " + child.text + " with id of: " + child.get('id'))

            if child.name == 'div':
                # print("<DIV>: ", child.text, child.attrs)
                if 'id' in child.attrs:
                    if child.get('id') == Global.global_id:
                        Global.processing = "global"
                    if child.get('id') == Global.china_id:
                        Global.processing = "china"
                if 'class' in child.attrs:
                    for c in child.get('class'):
                        if c == 'download_nv':
                            Global.channel = extractgroup(re.search(r"^(.*?) ", child.text))
            if child.name == 'a':
                if 'class' in child.attrs:
                    # print("Found a class of:", child.get('class'))
                    if 'btn_5' in child.get('class'):
                        if arg.Flags.verbose:
                            print("Processing", Global.channel, Global.processing, Global.model_name, "link of:",
                                  child.get('href'))
                            temp_d = {'image': child.get('href'), 'channel': Global.channel,
                                      'region': Global.processing}
                            ld['images'].append(temp_d)
            ld = walker(child, ld)
    return ld


def processline(pid: str, n: str):
    """process the line by reading the html and extracting the information"""
    url = "http://en.miui.com/download-" + pid + ".html"
    if arg.Flags.verbose:
        print(VERBOSE, "Name: {} -> {}".format(n, url))
    line_dict = dict(url=url, name=n, images=[])

    http = httplib2.Http()
    status, response = http.request(url)

    soup = BeautifulSoup(response, 'html.parser')

    line_dict = walker(soup, line_dict)
    if arg.Flags.debug:
        print(line_dict)
    return line_dict


def extractxm(ph: list) -> list:
    xmlist = []
    for ent in ph:
        if arg.Flags.debug:
            if ent['type'] == "1":
                print("Xiaomi device", ent['name'])
            else:
                print("Got model type", ent['type'], ent['name'])
        if ent['type'] == '1':
            xmlist.append(ent)
    return xmlist


def extractgroup(match):
    """extract the group (index: 1) from the match object"""
    if match is None:
        return None
    return match.group(1)


if __name__ == '__main__':
    main()
