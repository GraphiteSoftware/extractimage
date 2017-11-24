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
           "extracts all of the image URLs from all of the download pages. " \
           "The URLS are written to a json file." \
           "Here is the sequence of processing:\n" \
                "\tgeturls.py\n\tripimage.py\n\tmountimages.py\n\tparsebuildprop.py\n\tbuildproptocsv.py"


def main():
    """main processing loop"""
    do = arg.MyArgs(usagemsg)
    do.processargs()
    msg = arg.MSG()
    msg.TEST("Running in test mode")
    msg.DEBUG(do)

    writefile = rb.WriteJson(arg.Flags.configsettings['root'], arg.Flags.configsettings['data'],
                             arg.Flags.configsettings['model'])
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
            msg.DEBUG("No match on element: {}".format(i))
            continue
        else:
            msg.DEBUG("Got a match on element: {}".format(i))
            phonelist = json.loads(vardata)
            foundmatch = True
            break
    if foundmatch:
        msg.DEBUG("\n\n\nPhone list is: \n{}".format(phonelist))
    else:
        msg.ERROR("Did not find the phone list")
    if arg.Flags.configsettings['xmonly']:
        xmlist = extractxm(phonelist)
        writefile.data = xmlist
    else:
        writefile.data = phonelist

    # instead of writing the model file - do the extract url processes from extracttext.py
    image_dict = {}
    outf = rb.WriteJson(arg.Flags.configsettings['root'], arg.Flags.configsettings['data'],
                        arg.Flags.configsettings['links'])
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
    global msg
    if soup.name is not None:
        for child in soup.children:
            if child.name == 'span':
                # print("<SPAN>: ", child.text, child.attrs)
                if bool(re.search(r"Global$", child.text)):
                    Global.global_id = 'content_' + child.get('id')
                if bool(re.search(r"China", child.text)):
                    Global.china_id = 'content_' + child.get('id')

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
                        msg.VERBOSE("Processing {}, {}, {} link of: {}".format(Global.channel,
                                                                               Global.processing,
                                                                               Global.model_name,
                                                                               child.get('href')))
                        temp_d = {'image': child.get('href'), 'channel': Global.channel,
                                  'region': Global.processing}
                        ld['images'].append(temp_d)
            ld = walker(child, ld)
    return ld


def processline(pid: str, n: str):
    """process the line by reading the html and extracting the information"""
    global msg
    url = "http://en.miui.com/download-" + pid + ".html"
    msg.VERBOSE("Name: {} -> {}".format(n, url))
    line_dict = dict(url=url, name=n, images=[])

    http = httplib2.Http()
    status, response = http.request(url)

    soup = BeautifulSoup(response, 'html.parser')

    line_dict = walker(soup, line_dict)
    if arg.Flags.debug:
        print(line_dict)
    return line_dict


def extractxm(ph: list) -> list:
    global msg
    xmlist = []
    for ent in ph:
        if arg.Flags.debug:
            if ent['type'] == "1":
                msg.DEBUG("Xiaomi device {}".format(ent['name']))
            else:
                msg.DEBUG("Got model type {}, {}".format(ent['type'], ent['name']))
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
