import sys
from urllib.request import urlretrieve


def reporthook(blocknum, blocksize, totalsize):
    readsofar = blocknum * blocksize
    if totalsize > 0:
        percent = readsofar * 1e2 / totalsize
        s = "\r%5.1f%% %*d / %d" % (
            percent, len(str(totalsize)), readsofar, totalsize)
        sys.stderr.write(s)
        if readsofar >= totalsize:  # near the end
            sys.stderr.write("\n")
    else:  # total size is unknown
        sys.stderr.write("read %d\n" % (readsofar,))


file_url = 'http://bigota.d.miui.com/V8.5.4.0.NDECNEF/miui_MIMIX2_V8.5.4.0.NDECNEF_ac2de28209_7.1.zip'
file_name = "./miui_MIMIX2_V8.5.4.0.NDECNEF_ac2de28209_7.1.zip"

urlretrieve(file_url, file_name, reporthook)
