import os.path
import fnmatch

def main():
    """main processing loop"""
    apklist = getfilelist('/Volumes/passport/tmp')
    print(apklist)

    # TODO record the model, version, region and channel
    # TODO record the apk name and the hash value
    # TODO write out the data




def getfilelist(filepath) -> list:
    shpfiles = []
    patternspaces = r"Spaces*.apk"
    if not os.path.isdir(filepath):
        print("Image directory does not exist or is not mounted: " + filepath)
    else:
        for dirpath, subdirs, files in os.walk(filepath):
            print(files, dirpath)
            for x in files:
                print(x)
                if fnmatch.fnmatch(x, patternspaces):
                    print("FOUND ", x, dirpath)
                    shpfiles.append(os.path.join(dirpath, x))
    return shpfiles


if __name__ == '__main__':
    main()
